# Comprehensive Test Questions for Nyaya Legal Citation System

Test these questions to verify all system functionality: query validation, relevance scoring, case routing, citation network, and answer quality.

---

## ✅ CATEGORY 1: QUERY VALIDATION TESTS
**Purpose:** Verify invalid inputs are rejected

### Should be REJECTED (With error message):
1. `.\.venv\Scripts\python.exe query.py`
2. `python main.py`
3. `C:\Users\test.txt`
4. `./run.sh`
5. `powershell -c "Get-Process"`
6. `ab` (too short)
7. `123` (no letters)
8. `!!!` (only special chars)

### Should be ACCEPTED:
9. `adverse possession`
10. `what is contract law?`
11. `Sirisena v. Kobbekaduwa`

---

## 🎯 CATEGORY 2: RELEVANCE SCORING TESTS
**Purpose:** Verify correct content-based retrieval (not metadata-biased)

### Property Law:
1. **"adverse possession"**
   - Expected: Cases/text about adverse possession law
   - Should NOT return: Unrelated cases like Sirisena v. Kobbekaduwa
   - Look for: Phrases about "possession in denial of title", "time periods", "prescriptive rights"

2. **"easement rights"**
   - Expected: Cases about easements, servitudes, right of way
   - Look for: Terms like "dominant tenement", "servient tenement", "right of passage"

3. **"land title registration"**
   - Expected: Cases about Torrens system, title registration, land ownership
   - Look for: References to Registration of Title Act, indefeasibility

### Contract Law:
4. **"breach of contract remedies"**
   - Expected: Cases about damages, specific performance, rescission
   - Look for: Terms like "fundamental breach", "anticipatory breach", "damages"

5. **"offer and acceptance"**
   - Expected: Cases about contract formation, consensus ad idem
   - Look for: Terms like "invitation to treat", "acceptance", "counter-offer"

6. **"consideration in contracts"**
   - Expected: Cases about consideration doctrine, past consideration
   - Look for: Terms like "valuable consideration", "executed consideration"

### Tort Law:
7. **"negligence duty of care"**
   - Expected: Cases about duty of care, reasonable person standard
   - Look for: Terms like "proximity", "foreseeability", "breach of duty"

8. **"vicarious liability employer"**
   - Expected: Cases about employer liability for employee torts
   - Look for: Terms like "scope of employment", "respondeat superior"

### Criminal Law:
9. **"mens rea criminal intent"**
   - Expected: Cases about mental element in crimes
   - Look for: Terms like "intention", "recklessness", "criminal negligence"

10. **"murder actus reus"**
    - Expected: Cases about actus reus in homicide
    - Look for: Terms like "unlawful act", "causation", "death"

---

## 🔍 CATEGORY 3: CASE ROUTING TESTS
**Purpose:** Verify specific case name detection and citation network queries

### Specific Case Names:
11. **"Sirisena v. Kobbekaduwa"**
    - Expected: Neo4j query for this case + retrieval results
    - Should show: [CASE DETECTED], citations, followed/distinguished cases
    - Look for: Source block with PDF reference

12. **"Perera v. Silva"**
    - Expected: Case-specific routing if exists in Neo4j
    - Alternative: Regular retrieval if not in database

13. **"Attorney General v. Fernando"**
    - Expected: Constitutional law case routing

---

## 📚 CATEGORY 4: GENERAL LEGAL QUERIES
**Purpose:** Test natural language understanding and comprehensive answers

### Broad Legal Topics:
14. **"What are the elements of a valid contract in Sri Lankan law?"**
    - Expected: Multi-source answer covering offer, acceptance, consideration, capacity, intention

15. **"Explain the doctrine of res judicata"**
    - Expected: Cases and principles about finality of judgments, estoppel

16. **"What is the difference between civil and criminal burden of proof?"**
    - Expected: Discussion of "balance of probabilities" vs "beyond reasonable doubt"

17. **"How does prescription work in Sri Lankan property law?"**
    - Expected: Cases about prescription periods, interruption of prescription

18. **"What are the grounds for judicial review in Sri Lanka?"**
    - Expected: Administrative law cases, ultra vires, natural justice

### Procedural Law:
19. **"What is the statute of limitations for civil actions?"**
    - Expected: References to Prescription Ordinance, time limits

20. **"How to file a fundamental rights application?"**
    - Expected: Constitutional procedure, Article 126, Supreme Court jurisdiction

---

## 🧪 CATEGORY 5: EDGE CASE TESTS
**Purpose:** Test system robustness and graceful degradation

### Uncommon Queries:
21. **"quantum meruit"** (Latin legal term)
    - Expected: Cases about claims for reasonable value of services

22. **"obiter dictum vs ratio decidendi"**
    - Expected: Explanation of binding vs persuasive precedent

23. **"What is a writ of certiorari?"**
    - Expected: Cases about prerogative writs, judicial review remedies

### Misspellings (Optional - depends on embedding tolerance):
24. **"advers possesion"** (misspelled)
    - Test: Does semantic search still find "adverse possession"?

25. **"breech of contract"** (misspelled breach)
    - Test: Semantic similarity handling

### Multi-concept Queries:
26. **"negligence and contributory negligence in motor vehicle accidents"**
    - Expected: Cases covering both concepts in tort context

27. **"offer acceptance consideration contract formation"**
    - Expected: Comprehensive contract law results

---

## ⚡ CATEGORY 6: PERFORMANCE TESTS
**Purpose:** Verify caching and optimization system

### Cache Testing:
28. **First query:** `"adverse possession"` 
    - Note the time (e.g., 2.4s)
    - Should show retrieval logs

29. **Repeat query:** `"adverse possession"` (immediate repeat)
    - Should show: **[CACHE HIT]**
    - Time should be ~0.001s (1000x faster)

30. **Different query:** `"breach of contract"`
    - Should NOT show cache hit (first time for this query)

---

## 📊 EXPECTED BEHAVIORS CHECKLIST

### For ALL valid queries, verify:
- ✅ No error messages
- ✅ Response time logged
- ✅ Source citations included (PDF + page numbers)
- ✅ Relevant content (matches query topic)
- ✅ Well-formatted answer with legal analysis

### For invalid queries (Category 1 rejected), verify:
- ✅ Error message: "[ERROR] Invalid query detected..."
- ✅ No retrieval attempted
- ✅ System stops immediately

### For case-routed queries (Category 3), verify:
- ✅ "[CASE DETECTED]" message appears
- ✅ Neo4j citation network queried
- ✅ Source block at end with case details

### For cached queries (Category 6), verify:
- ✅ "[CACHE HIT]" message appears
- ✅ Response time < 0.01s
- ✅ Identical results to first query

### For relevance scoring (Category 2), verify:
- ✅ Debug output shows: "[FILTER] Top result scores"
- ✅ Scores near 1.0 for exact phrase matches
- ✅ Scores near 0.4-0.6 for term matches
- ✅ Results kept/total ratio shown

---

## 🚀 HOW TO RUN THE TESTS

### Option 1: Interactive Testing
```powershell
.\.venv\Scripts\python.exe query.py
```
Then enter each question one at a time, observe output.

### Option 2: Clear Cache Between Tests (for performance testing)
```powershell
Remove-Item -Recurse -Force .query_cache
.\.venv\Scripts\python.exe query.py
```

### Option 3: View Debug Output
- Relevance scores are automatically printed during retrieval
- Look for "[FILTER]" messages showing scoring decisions

---

## 📝 RECOMMENDED TEST SEQUENCE

**Phase 1: Validation** (Questions 1-10)
- Verify invalid queries rejected
- Verify valid queries accepted

**Phase 2: Core Relevance** (Questions 1-10 from Category 2)
- Test one from each legal domain
- Verify content-based results

**Phase 3: Case Routing** (Questions 11-13)
- Test case name detection
- Verify Neo4j integration

**Phase 4: Natural Language** (Questions 14-20)
- Test complex queries
- Verify comprehensive answers

**Phase 5: Performance** (Questions 28-30)
- Test cache functionality
- Measure speedup

**Phase 6: Edge Cases** (Questions 21-27)
- Test robustness
- Identify improvement areas

---

## ✨ SUCCESS CRITERIA

The system passes if:
1. ✅ All invalid queries (1-8) are rejected
2. ✅ All valid queries (9+) return relevant content
3. ✅ Relevance scores prioritize content (1.0 for exact matches)
4. ✅ Cache provides >100x speedup for repeated queries
5. ✅ Case routing works for known cases
6. ✅ Answers include proper source citations
7. ✅ No crashes or unhandled errors

---

**Good luck with testing! 🎯**
