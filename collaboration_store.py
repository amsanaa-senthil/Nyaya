"""
Collaboration and sharing persistence for conversations.

Backed by SQLite for simple deployment and persistence across restarts.
"""

import hashlib
import json
import os
import secrets
import sqlite3
import time
import uuid
from threading import Lock
from typing import Any, Dict, List, Optional

_DB_PATH = os.getenv("NYAYA_COLLAB_DB", os.getenv("NYAYA_ANALYTICS_DB", "nyaya_analytics.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    tags_json TEXT NOT NULL DEFAULT '[]',
    matter_id TEXT NOT NULL DEFAULT '',
    jurisdiction TEXT NOT NULL DEFAULT '',
    review_status TEXT NOT NULL DEFAULT 'draft',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    deleted_at REAL
);
CREATE INDEX IF NOT EXISTS idx_conversations_owner_updated ON conversations(owner_user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    message_key TEXT NOT NULL,
    version INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    citations_json TEXT NOT NULL DEFAULT '[]',
    evidence_score REAL NOT NULL DEFAULT 0.0,
    created_by TEXT NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_key_version ON messages(message_key, version);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_key ON messages(conversation_id, message_key);

CREATE TABLE IF NOT EXISTS share_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    share_token TEXT NOT NULL UNIQUE,
    permission TEXT NOT NULL,
    password_hash TEXT,
    expires_at REAL,
    revoked_at REAL,
    created_by TEXT NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);
CREATE INDEX IF NOT EXISTS idx_share_links_conversation ON share_links(conversation_id, created_at DESC);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    message_key TEXT,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    mentions_json TEXT NOT NULL DEFAULT '[]',
    created_at REAL NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);
CREATE INDEX IF NOT EXISTS idx_comments_conversation ON comments(conversation_id, created_at DESC);

CREATE TABLE IF NOT EXISTS collaboration_audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    conversation_id TEXT,
    share_token TEXT,
    details_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_collab_audit_time ON collaboration_audit_events(timestamp DESC);
"""


class CollaborationStore:
    def __init__(self) -> None:
        self._db_path = _DB_PATH
        self._lock = Lock()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.executescript(_SCHEMA)
            conn.commit()

    @staticmethod
    def _loads_json(raw: str, fallback: Any) -> Any:
        try:
            return json.loads(raw)
        except Exception:
            return fallback

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _now(self) -> float:
        return time.time()

    def _audit(
        self,
        *,
        user_id: str,
        event_type: str,
        conversation_id: Optional[str] = None,
        share_token: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload = details or {}
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO collaboration_audit_events "
                "(timestamp, user_id, event_type, conversation_id, share_token, details_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    self._now(),
                    user_id,
                    event_type,
                    conversation_id,
                    share_token,
                    json.dumps(payload, ensure_ascii=True),
                ),
            )
            conn.commit()

    def _ensure_owner(self, user_id: str, conversation_id: str, include_deleted: bool = False) -> Dict[str, Any]:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT id, owner_user_id, title, tags_json, matter_id, jurisdiction, review_status, "
                "created_at, updated_at, deleted_at "
                "FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()

        if not row:
            raise ValueError("Conversation not found")
        if row[1] != user_id:
            raise PermissionError("You do not have access to this conversation")
        if (row[9] is not None) and not include_deleted:
            raise ValueError("Conversation has been deleted")

        return {
            "id": row[0],
            "owner_user_id": row[1],
            "title": row[2],
            "tags": self._loads_json(row[3], []),
            "matter_id": row[4],
            "jurisdiction": row[5],
            "review_status": row[6],
            "created_at": row[7],
            "updated_at": row[8],
            "deleted_at": row[9],
        }

    def create_conversation(
        self,
        *,
        owner_user_id: str,
        title: str,
        tags: Optional[List[str]] = None,
        matter_id: str = "",
        jurisdiction: str = "",
    ) -> Dict[str, Any]:
        now = self._now()
        conversation_id = str(uuid.uuid4())
        safe_tags = [str(tag)[:64] for tag in (tags or []) if str(tag).strip()]
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO conversations "
                    "(id, owner_user_id, title, tags_json, matter_id, jurisdiction, review_status, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?)",
                    (
                        conversation_id,
                        owner_user_id,
                        title[:180],
                        json.dumps(safe_tags, ensure_ascii=True),
                        matter_id[:100],
                        jurisdiction[:100],
                        now,
                        now,
                    ),
                )
                conn.commit()

        self._audit(
            user_id=owner_user_id,
            event_type="conversation.created",
            conversation_id=conversation_id,
            details={"title": title[:180]},
        )
        return self._ensure_owner(owner_user_id, conversation_id, include_deleted=True)

    def list_conversations(self, *, owner_user_id: str, include_deleted: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 200))
        sql = (
            "SELECT id, owner_user_id, title, tags_json, matter_id, jurisdiction, review_status, "
            "created_at, updated_at, deleted_at "
            "FROM conversations WHERE owner_user_id = ? "
        )
        params: List[Any] = [owner_user_id]
        if not include_deleted:
            sql += "AND deleted_at IS NULL "
        sql += "ORDER BY updated_at DESC LIMIT ?"
        params.append(safe_limit)

        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [
            {
                "id": row[0],
                "owner_user_id": row[1],
                "title": row[2],
                "tags": self._loads_json(row[3], []),
                "matter_id": row[4],
                "jurisdiction": row[5],
                "review_status": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "deleted_at": row[9],
            }
            for row in rows
        ]

    def add_message(
        self,
        *,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        evidence_score: float = 0.0,
    ) -> Dict[str, Any]:
        self._ensure_owner(user_id, conversation_id)
        now = self._now()
        message_key = str(uuid.uuid4())
        safe_role = role if role in {"user", "assistant", "system"} else "assistant"
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO messages "
                "(conversation_id, message_key, version, role, content, citations_json, evidence_score, created_by, created_at) "
                "VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)",
                (
                    conversation_id,
                    message_key,
                    safe_role,
                    content,
                    json.dumps(citations or [], ensure_ascii=True),
                    max(0.0, min(1.0, float(evidence_score))),
                    user_id,
                    now,
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
            conn.commit()

        self._audit(
            user_id=user_id,
            event_type="conversation.message_added",
            conversation_id=conversation_id,
            details={"message_key": message_key, "role": safe_role},
        )
        return {
            "conversation_id": conversation_id,
            "message_key": message_key,
            "version": 1,
            "role": safe_role,
            "content": content,
            "citations": citations or [],
            "evidence_score": max(0.0, min(1.0, float(evidence_score))),
            "created_by": user_id,
            "created_at": now,
        }

    def edit_message(
        self,
        *,
        user_id: str,
        conversation_id: str,
        message_key: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        evidence_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        self._ensure_owner(user_id, conversation_id)
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(version), 0), role FROM messages "
                "WHERE conversation_id = ? AND message_key = ?",
                (conversation_id, message_key),
            ).fetchone()
            if not row or int(row[0]) <= 0:
                raise ValueError("Message not found")

            next_version = int(row[0]) + 1
            role = row[1]
            now = self._now()
            eff_score = 0.0 if evidence_score is None else max(0.0, min(1.0, float(evidence_score)))
            conn.execute(
                "INSERT INTO messages "
                "(conversation_id, message_key, version, role, content, citations_json, evidence_score, created_by, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    conversation_id,
                    message_key,
                    next_version,
                    role,
                    content,
                    json.dumps(citations or [], ensure_ascii=True),
                    eff_score,
                    user_id,
                    now,
                ),
            )
            conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
            conn.commit()

        self._audit(
            user_id=user_id,
            event_type="conversation.message_edited",
            conversation_id=conversation_id,
            details={"message_key": message_key, "version": next_version},
        )
        return {
            "conversation_id": conversation_id,
            "message_key": message_key,
            "version": next_version,
            "role": role,
            "content": content,
            "citations": citations or [],
            "evidence_score": eff_score,
            "created_by": user_id,
            "created_at": now,
        }

    def get_messages(self, *, conversation_id: str, include_history: bool = False) -> List[Dict[str, Any]]:
        if include_history:
            sql = (
                "SELECT message_key, version, role, content, citations_json, evidence_score, created_by, created_at "
                "FROM messages WHERE conversation_id = ? ORDER BY created_at ASC"
            )
            params = (conversation_id,)
        else:
            sql = (
                "SELECT m.message_key, m.version, m.role, m.content, m.citations_json, m.evidence_score, m.created_by, m.created_at "
                "FROM messages m "
                "INNER JOIN ("
                "  SELECT message_key, MAX(version) AS latest "
                "  FROM messages WHERE conversation_id = ? GROUP BY message_key"
                ") last ON m.message_key = last.message_key AND m.version = last.latest "
                "WHERE m.conversation_id = ? "
                "ORDER BY m.created_at ASC"
            )
            params = (conversation_id, conversation_id)

        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(sql, params).fetchall()

        return [
            {
                "message_key": row[0],
                "version": row[1],
                "role": row[2],
                "content": row[3],
                "citations": self._loads_json(row[4], []),
                "evidence_score": row[5],
                "created_by": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]

    def get_conversation(
        self,
        *,
        user_id: str,
        conversation_id: str,
        include_history: bool = False,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        convo = self._ensure_owner(user_id, conversation_id, include_deleted=include_deleted)
        convo["messages"] = self.get_messages(conversation_id=conversation_id, include_history=include_history)
        convo["comments"] = self.list_comments(user_id=user_id, conversation_id=conversation_id)
        convo["shares"] = self.list_shares(user_id=user_id, conversation_id=conversation_id)
        return convo

    def set_review_status(self, *, user_id: str, conversation_id: str, review_status: str) -> Dict[str, Any]:
        allowed = {"draft", "needs_review", "reviewed", "approved"}
        if review_status not in allowed:
            raise ValueError("Invalid review status")
        self._ensure_owner(user_id, conversation_id)
        now = self._now()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "UPDATE conversations SET review_status = ?, updated_at = ? WHERE id = ?",
                (review_status, now, conversation_id),
            )
            conn.commit()

        self._audit(
            user_id=user_id,
            event_type="conversation.review_status_changed",
            conversation_id=conversation_id,
            details={"review_status": review_status},
        )
        return self._ensure_owner(user_id, conversation_id)

    def soft_delete_conversation(self, *, user_id: str, conversation_id: str) -> None:
        self._ensure_owner(user_id, conversation_id)
        now = self._now()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("UPDATE conversations SET deleted_at = ?, updated_at = ? WHERE id = ?", (now, now, conversation_id))
            conn.commit()

        self._audit(
            user_id=user_id,
            event_type="conversation.deleted",
            conversation_id=conversation_id,
            details={},
        )

    def create_share_link(
        self,
        *,
        user_id: str,
        conversation_id: str,
        permission: str,
        expires_in_hours: Optional[int] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        if permission not in {"view", "comment", "edit"}:
            raise ValueError("Invalid permission")
        self._ensure_owner(user_id, conversation_id)
        share_token = secrets.token_urlsafe(18)
        now = self._now()
        expires_at: Optional[float] = None
        if isinstance(expires_in_hours, int) and expires_in_hours > 0:
            expires_at = now + (expires_in_hours * 3600)
        password_hash = self._hash_password(password) if password else None

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO share_links "
                "(conversation_id, share_token, permission, password_hash, expires_at, revoked_at, created_by, created_at) "
                "VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
                (conversation_id, share_token, permission, password_hash, expires_at, user_id, now),
            )
            conn.commit()

        self._audit(
            user_id=user_id,
            event_type="conversation.share_created",
            conversation_id=conversation_id,
            share_token=share_token,
            details={"permission": permission, "expires_at": expires_at, "has_password": bool(password_hash)},
        )
        return {
            "conversation_id": conversation_id,
            "share_token": share_token,
            "permission": permission,
            "expires_at": expires_at,
            "created_at": now,
            "revoked": False,
            "has_password": bool(password_hash),
        }

    def list_shares(self, *, user_id: str, conversation_id: str) -> List[Dict[str, Any]]:
        self._ensure_owner(user_id, conversation_id)
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT share_token, permission, expires_at, revoked_at, created_by, created_at, password_hash "
                "FROM share_links WHERE conversation_id = ? ORDER BY created_at DESC",
                (conversation_id,),
            ).fetchall()
        return [
            {
                "share_token": row[0],
                "permission": row[1],
                "expires_at": row[2],
                "revoked": row[3] is not None,
                "created_by": row[4],
                "created_at": row[5],
                "has_password": bool(row[6]),
            }
            for row in rows
        ]

    def revoke_share(self, *, user_id: str, conversation_id: str, share_token: str) -> Dict[str, Any]:
        self._ensure_owner(user_id, conversation_id)
        now = self._now()
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute(
                "UPDATE share_links SET revoked_at = ? "
                "WHERE conversation_id = ? AND share_token = ?",
                (now, conversation_id, share_token),
            )
            conn.commit()
        if not cur.rowcount:
            raise ValueError("Share token not found")

        self._audit(
            user_id=user_id,
            event_type="conversation.share_revoked",
            conversation_id=conversation_id,
            share_token=share_token,
            details={},
        )
        return {"share_token": share_token, "revoked_at": now}

    def access_shared_conversation(
        self,
        *,
        accessor_user_id: str,
        share_token: str,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT conversation_id, permission, password_hash, expires_at, revoked_at, created_by "
                "FROM share_links WHERE share_token = ?",
                (share_token,),
            ).fetchone()

        if not row:
            raise ValueError("Share token not found")

        conversation_id, permission, password_hash, expires_at, revoked_at, created_by = row
        now = self._now()
        if revoked_at is not None:
            raise PermissionError("Share link has been revoked")
        if expires_at is not None and float(expires_at) < now:
            raise PermissionError("Share link has expired")
        if password_hash:
            if not password or self._hash_password(password) != password_hash:
                raise PermissionError("Invalid share password")

        with sqlite3.connect(self._db_path) as conn:
            convo_row = conn.execute(
                "SELECT id, owner_user_id, title, tags_json, matter_id, jurisdiction, review_status, created_at, updated_at, deleted_at "
                "FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
        if not convo_row or convo_row[9] is not None:
            raise ValueError("Conversation is not available")

        self._audit(
            user_id=accessor_user_id,
            event_type="conversation.share_accessed",
            conversation_id=conversation_id,
            share_token=share_token,
            details={"permission": permission, "shared_by": created_by},
        )

        return {
            "conversation": {
                "id": convo_row[0],
                "owner_user_id": convo_row[1],
                "title": convo_row[2],
                "tags": self._loads_json(convo_row[3], []),
                "matter_id": convo_row[4],
                "jurisdiction": convo_row[5],
                "review_status": convo_row[6],
                "created_at": convo_row[7],
                "updated_at": convo_row[8],
            },
            "permission": permission,
            "messages": self.get_messages(conversation_id=conversation_id, include_history=False),
            "comments": self.list_comments_by_conversation(conversation_id=conversation_id),
        }

    def add_comment(
        self,
        *,
        user_id: str,
        conversation_id: str,
        content: str,
        mentions: Optional[List[str]] = None,
        message_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._ensure_owner(user_id, conversation_id)
        now = self._now()
        safe_mentions = [str(m)[:128] for m in (mentions or []) if str(m).strip()]
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO comments (conversation_id, message_key, user_id, content, mentions_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    conversation_id,
                    message_key,
                    user_id,
                    content[:1500],
                    json.dumps(safe_mentions, ensure_ascii=True),
                    now,
                ),
            )
            conn.commit()

        self._audit(
            user_id=user_id,
            event_type="conversation.comment_added",
            conversation_id=conversation_id,
            details={"message_key": message_key, "mentions": safe_mentions},
        )
        return {
            "conversation_id": conversation_id,
            "message_key": message_key,
            "user_id": user_id,
            "content": content[:1500],
            "mentions": safe_mentions,
            "created_at": now,
        }

    def list_comments(self, *, user_id: str, conversation_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        self._ensure_owner(user_id, conversation_id)
        return self.list_comments_by_conversation(conversation_id=conversation_id, limit=limit)

    def list_comments_by_conversation(self, *, conversation_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT message_key, user_id, content, mentions_json, created_at "
                "FROM comments WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
                (conversation_id, safe_limit),
            ).fetchall()

        return [
            {
                "message_key": row[0],
                "user_id": row[1],
                "content": row[2],
                "mentions": self._loads_json(row[3], []),
                "created_at": row[4],
            }
            for row in rows
        ]

    def export_conversation(self, *, user_id: str, conversation_id: str, include_history: bool = False) -> Dict[str, Any]:
        convo = self.get_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
            include_history=include_history,
            include_deleted=False,
        )
        return {
            "exported_at": self._now(),
            "conversation": convo,
        }

    def purge_data(self, *, user_id: str, deleted_older_than_days: int = 30, expired_share_older_than_days: int = 7) -> Dict[str, int]:
        safe_deleted_days = max(1, min(deleted_older_than_days, 3650))
        safe_expired_days = max(1, min(expired_share_older_than_days, 3650))
        now = self._now()
        deleted_cutoff = now - (safe_deleted_days * 86400)
        expired_cutoff = now - (safe_expired_days * 86400)

        with sqlite3.connect(self._db_path) as conn:
            conv_rows = conn.execute(
                "SELECT id FROM conversations WHERE deleted_at IS NOT NULL AND deleted_at < ?",
                (deleted_cutoff,),
            ).fetchall()
            conv_ids = [r[0] for r in conv_rows]

            deleted_messages = 0
            deleted_comments = 0
            deleted_shares = 0
            deleted_conversations = 0

            if conv_ids:
                placeholders = ",".join(["?"] * len(conv_ids))
                cur = conn.execute(f"DELETE FROM messages WHERE conversation_id IN ({placeholders})", tuple(conv_ids))
                deleted_messages = cur.rowcount or 0
                cur = conn.execute(f"DELETE FROM comments WHERE conversation_id IN ({placeholders})", tuple(conv_ids))
                deleted_comments = cur.rowcount or 0
                cur = conn.execute(f"DELETE FROM share_links WHERE conversation_id IN ({placeholders})", tuple(conv_ids))
                deleted_shares = cur.rowcount or 0
                cur = conn.execute(f"DELETE FROM conversations WHERE id IN ({placeholders})", tuple(conv_ids))
                deleted_conversations = cur.rowcount or 0

            cur = conn.execute(
                "DELETE FROM share_links WHERE expires_at IS NOT NULL AND expires_at < ? AND revoked_at IS NOT NULL AND revoked_at < ?",
                (now, expired_cutoff),
            )
            deleted_expired_revoked = cur.rowcount or 0

            conn.commit()

        self._audit(
            user_id=user_id,
            event_type="governance.purge_executed",
            details={
                "deleted_conversations": deleted_conversations,
                "deleted_messages": deleted_messages,
                "deleted_comments": deleted_comments,
                "deleted_shares": deleted_shares,
                "deleted_expired_revoked": deleted_expired_revoked,
            },
        )

        return {
            "deleted_conversations": deleted_conversations,
            "deleted_messages": deleted_messages,
            "deleted_comments": deleted_comments,
            "deleted_shares": deleted_shares,
            "deleted_expired_revoked": deleted_expired_revoked,
        }

    def get_audit_events(self, *, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT timestamp, user_id, event_type, conversation_id, share_token, details_json "
                "FROM collaboration_audit_events "
                "WHERE user_id = ? OR event_type = 'conversation.share_accessed' "
                "ORDER BY id DESC LIMIT ?",
                (user_id, safe_limit),
            ).fetchall()

        return [
            {
                "timestamp": row[0],
                "user_id": row[1],
                "event_type": row[2],
                "conversation_id": row[3],
                "share_token": row[4],
                "details": self._loads_json(row[5], {}),
            }
            for row in rows
        ]


collaboration_store = CollaborationStore()
