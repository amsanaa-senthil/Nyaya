#!/usr/bin/env python3
"""
Sri Lanka Supreme Court — Full Judgements Scraper
https://supremecourt.lk/judgements/

The site renders a plain HTML table on each page with a direct [Download] link
per row pointing to:
    https://supremecourt.lk/wp-content/uploads/judgements/<filename>.pdf

Pagination is via:
    ?year=YYYY&month=&judgment_by=&paged=N

This script:
  1. Iterates every year (2010-2026) + "all years" (?year=)
  2. Walks every page until the table is empty
  3. Downloads every PDF directly
  4. Skips already-downloaded files (resumable)
  5. Saves a manifest CSV

Install:
    pip install requests beautifulsoup4 tqdm

Run:
    python scrape_supremecourt.py                  # download everything
    python scrape_supremecourt.py --year 2022      # single year
    python scrape_supremecourt.py --dry-run        # list links, no download
    python scrape_supremecourt.py --workers 3      # parallel downloads
"""

import re, csv, time, random, logging, argparse, hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL       = "https://supremecourt.lk/judgements/"
SPECIAL_URL    = "https://supremecourt.lk/special-determination/"
BOOK_URLS      = [
    "https://supremecourt.lk/judgments-book-2024/",
    "https://supremecourt.lk/judgments-book-2023/",
]
YEARS          = [""] + [str(y) for y in range(2010, 2027)]  # "" = all years

OUTPUT_DIR     = Path("supremecourt_judgements")
DELAY_MIN      = 1.0
DELAY_MAX      = 2.5
TIMEOUT        = 40
MAX_RETRIES    = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer":         "https://supremecourt.lk/",
}

FILE_RE = re.compile(r"\.(pdf|doc|docx)(\?.*)?$", re.IGNORECASE)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Data ──────────────────────────────────────────────────────────────────────
@dataclass
class Doc:
    case_no:    str
    parties:    str
    date:       str
    judge:      str
    url:        str
    year:       str
    local_path: str = ""

# ── Session ───────────────────────────────────────────────────────────────────
_sess: Optional[requests.Session] = None

def sess() -> requests.Session:
    global _sess
    if _sess is None:
        _sess = requests.Session()
        _sess.headers.update(HEADERS)
    return _sess

def nap(fixed: Optional[float] = None):
    time.sleep(fixed if fixed is not None else random.uniform(DELAY_MIN, DELAY_MAX))

def fetch(url: str, stream=False) -> Optional[requests.Response]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = sess().get(url, timeout=TIMEOUT, stream=stream)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            log.warning("  Attempt %d/%d: %s", attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                time.sleep(attempt * 3)
    log.error("  FAILED: %s", url)
    return None

# ── Helpers ───────────────────────────────────────────────────────────────────
def safe(s: str, n: int = 160) -> str:
    s = re.sub(r'[\\/*?:"<>|\r\n\t]+', "_", s)
    return re.sub(r'\s+', " ", s).strip()[:n] or "unnamed"

def url2fname(url: str, case_no: str = "") -> str:
    ext  = Path(urlparse(url).path).suffix.lower() or ".pdf"
    # prefer the filename from the URL itself (e.g. sc_fr_56_2023.pdf)
    stem = Path(urlparse(url).path).stem
    if not stem:
        stem = safe(case_no) if case_no else hashlib.md5(url.encode()).hexdigest()[:10]
    return safe(stem) + ext

# ── Parse one listing page → list[Doc] ───────────────────────────────────────
def parse_table(soup: BeautifulSoup, page_url: str, year: str) -> list[Doc]:
    docs = []
    # Find the judgements table — look for rows with a Download link
    for row in soup.select("table tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        # Find the Download anchor in any cell
        dl_a = None
        for cell in cells:
            a = cell.find("a", href=FILE_RE)
            if a:
                dl_a = a; break
        if dl_a is None:
            continue

        full_url = urljoin(page_url, dl_a["href"].strip())

        # Extract metadata from cells (order: Date, Case No, Parties, Judge, Keywords, Legislation, Document)
        texts = [c.get_text(" ", strip=True) for c in cells]
        date     = texts[0] if len(texts) > 0 else ""
        case_no  = texts[1] if len(texts) > 1 else ""
        parties  = texts[2][:300] if len(texts) > 2 else ""
        judge    = texts[3] if len(texts) > 3 else ""

        # Derive year from date or URL param
        yr = year
        if not yr:
            m = re.search(r'\b(20\d{2})\b', date)
            if m: yr = m.group(1)

        docs.append(Doc(
            case_no=case_no, parties=parties,
            date=date, judge=judge,
            url=full_url, year=yr,
        ))
    return docs


def scrape_all_links(soup: BeautifulSoup, page_url: str, year: str) -> list[Doc]:
    """
    Fallback: if no table rows found, grab every PDF link on the page.
    Used for book pages and special determinations.
    """
    docs = []
    for a in soup.find_all("a", href=FILE_RE):
        full = urljoin(page_url, a["href"].strip())
        title = a.get_text(" ", strip=True) or Path(urlparse(full).path).name
        docs.append(Doc(
            case_no=title, parties="", date="", judge="",
            url=full, year=year,
        ))
    return docs

# ── Paginated scrape for one year ─────────────────────────────────────────────
def scrape_year(year: str) -> list[Doc]:
    all_docs: list[Doc] = []
    seen_urls: set[str] = set()
    page = 1

    while True:
        if page == 1:
            url = f"{BASE_URL}?year={year}&month=&judgment_by="
        else:
            url = f"{BASE_URL}?year={year}&month=&judgment_by=&paged={page}"

        log.info("Fetching year=%-4s page=%d  %s", year or "ALL", page, url)
        r = fetch(url)
        if r is None:
            break

        soup = BeautifulSoup(r.text, "html.parser")
        docs = parse_table(soup, url, year)

        new = [d for d in docs if d.url not in seen_urls]
        if not new:
            log.info("  → no new entries on page %d, done with year=%s", page, year or "ALL")
            break

        for d in new:
            seen_urls.add(d.url)
        all_docs.extend(new)
        log.info("  → found %d new (total so far: %d)", len(new), len(all_docs))

        # Check if there's a next page link
        has_next = bool(soup.select_one("a.next, a[rel='next'], .nav-previous a, .pagination .next"))
        # Also check the raw text for a "next" link
        if not has_next:
            for a in soup.find_all("a", href=True):
                txt = a.get_text(strip=True).lower()
                if txt in ("next", "next »", "›", "»", ">"):
                    has_next = True; break

        if not has_next:
            # Try fetching page+1 anyway — if it has new results, continue
            # This handles sites without explicit next buttons
            pass  # we rely on the "no new entries" break above

        page += 1
        nap()

    return all_docs


def scrape_static_page(url: str, year: str) -> list[Doc]:
    """For book pages and special determinations."""
    docs: list[Doc] = []
    seen: set[str] = set()
    current = url

    while current:
        log.info("Fetching static page: %s", current)
        r = fetch(current)
        if r is None:
            break
        soup = BeautifulSoup(r.text, "html.parser")

        # Try table first, then raw links
        page_docs = parse_table(soup, current, year)
        if not page_docs:
            page_docs = scrape_all_links(soup, current, year)

        new = [d for d in page_docs if d.url not in seen]
        for d in new:
            seen.add(d.url)
        docs.extend(new)
        log.info("  → %d new links", len(new))

        # Follow next page
        nxt = None
        for a in soup.find_all("a", href=True):
            if a.get_text(strip=True).lower() in ("next", "next »", "›", "»", ">"):
                nxt = urljoin(current, a["href"]); break
        if not nxt:
            for a in soup.find_all("a", rel=True):
                if "next" in (a.get("rel") or []):
                    nxt = urljoin(current, a["href"]); break
        current = nxt
        if current:
            nap()

    return docs

# ── Download ──────────────────────────────────────────────────────────────────
def download(doc: Doc, out_dir: Path) -> tuple[Doc, str]:
    sub = out_dir / (doc.year or "unknown")
    sub.mkdir(parents=True, exist_ok=True)
    fname = url2fname(doc.url, doc.case_no)
    dest  = sub / fname

    if dest.exists() and dest.stat().st_size > 0:
        doc.local_path = str(dest)
        return doc, "skipped"

    r = fetch(doc.url, stream=True)
    if r is None:
        return doc, "failed"

    try:
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(65536):
                if chunk:
                    fh.write(chunk)
        if dest.stat().st_size == 0:
            dest.unlink()
            return doc, "failed"
        doc.local_path = str(dest)
        return doc, "downloaded"
    except Exception as e:
        log.error("Write error %s: %s", dest, e)
        if dest.exists(): dest.unlink()
        return doc, "failed"

# ── Manifest ──────────────────────────────────────────────────────────────────
FIELDS = ["case_no", "date", "judge", "year", "url", "local_path", "parties"]

def load_done(path: Path) -> set[str]:
    done: set[str] = set()
    if not path.exists():
        return done
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lp = row.get("local_path", "")
            if lp and lp not in ("", "failed"):
                done.add(row["url"])
    return done

def append_manifest(path: Path, docs: list[Doc]):
    write_hdr = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if write_hdr: w.writeheader()
        for d in docs: w.writerow(asdict(d))

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Download all Sri Lanka Supreme Court judgements")
    ap.add_argument("--year",    help="Single year, e.g. 2022")
    ap.add_argument("--out",     default=str(OUTPUT_DIR), help="Output directory")
    ap.add_argument("--workers", type=int, default=1, help="Parallel download threads (default 1)")
    ap.add_argument("--delay",   type=float, help="Fixed delay in seconds between requests")
    ap.add_argument("--dry-run", action="store_true", help="Collect links only, no download")
    args = ap.parse_args()

    if args.delay:
        global DELAY_MIN, DELAY_MAX
        DELAY_MIN = DELAY_MAX = args.delay

    out_dir  = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "_manifest.csv"
    done     = load_done(manifest)
    log.info("Previously downloaded: %d files", len(done))

    # ── Collect all links ─────────────────────────────────────────────────────
    all_docs: list[Doc] = []
    seen: set[str] = set()

    def add(docs: list[Doc]):
        for d in docs:
            if d.url not in seen:
                seen.add(d.url)
                all_docs.append(d)

    years_to_scrape = [str(args.year)] if args.year else YEARS

    for yr in years_to_scrape:
        add(scrape_year(yr))

    # Book pages (2023 / 2024 have their own static pages)
    if not args.year or args.year in ("2023", "2024"):
        for burl in BOOK_URLS:
            m  = re.search(r'(\d{4})', burl)
            yr = m.group(1) if m else ""
            if args.year and yr != args.year:
                continue
            add(scrape_static_page(burl, yr))

    # Special determinations
    if not args.year:
        add(scrape_static_page(SPECIAL_URL, "special"))

    log.info("Total unique links found: %d", len(all_docs))

    # Filter out already downloaded
    to_download = [d for d in all_docs if d.url not in done]
    log.info("New files to download:    %d", len(to_download))

    if args.dry_run:
        print(f"\n{'='*65}")
        print(f"DRY RUN — {len(all_docs)} total unique links found, {len(to_download)} new\n")
        for d in all_docs:
            status = "✓" if d.url in done else " "
            print(f"  [{status}] [{d.year}] {d.case_no[:40]:40s}  {d.url}")
        return

    if not to_download:
        log.info("Nothing new to download — all caught up!")
        return

    # ── Download ──────────────────────────────────────────────────────────────
    dl = sk = fl = 0
    finished: list[Doc] = []

    def _dl(doc: Doc):
        nap(DELAY_MIN / max(args.workers, 1))
        return download(doc, out_dir)

    log.info("Downloading %d files with %d worker(s)…", len(to_download), args.workers)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(_dl, d): d for d in to_download}
        for fut in tqdm(as_completed(futs), total=len(to_download), desc="Downloading", unit="file"):
            doc, status = fut.result()
            if   status == "downloaded": dl += 1
            elif status == "skipped":    sk += 1
            else:
                fl += 1
                with open(out_dir / "_failed.txt", "a") as ff:
                    ff.write(doc.url + "\n")
            finished.append(doc)

    append_manifest(manifest, finished)

    log.info("=" * 50)
    log.info("Downloaded : %d", dl)
    log.info("Skipped    : %d (already existed)", sk)
    log.info("Failed     : %d  → _failed.txt", fl)
    log.info("Output     : %s", out_dir.resolve())
    log.info("Manifest   : %s", manifest.resolve())

if __name__ == "__main__":
    main()
