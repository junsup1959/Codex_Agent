from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import Any, Iterator


JsonObject = dict[str, Any]


class LedgerError(ValueError):
    """Raised when a ledger operation violates the run contract."""


class ContextLedger:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize_schema(self) -> None:
        schema = resources.files("context_ledger_mcp").joinpath("schema.sql").read_text(encoding="utf-8")
        with self._connection() as connection:
            connection.executescript(schema)

    def initialize_run(self, run_id: str, goal: str, metadata: JsonObject | None = None) -> JsonObject:
        metadata_json = _to_json(metadata or {})
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO runs (run_id, goal, metadata_json)
                VALUES (?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                  goal = excluded.goal,
                  metadata_json = excluded.metadata_json,
                  updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                """,
                (run_id, goal, metadata_json),
            )
        return self.query_run_ledger(run_id)

    def write_context_packet(
        self,
        run_id: str,
        packet: JsonObject,
        expected_revision: int | None = None,
    ) -> JsonObject:
        self._require_run(run_id)
        current_revision = self._current_revision(run_id)
        if expected_revision is not None and expected_revision != current_revision:
            raise LedgerError(
                f"stale context revision: expected {expected_revision}, current {current_revision}"
            )

        next_revision = current_revision + 1
        packet_with_revision = dict(packet)
        packet_with_revision["run_id"] = run_id
        packet_with_revision["context_revision"] = next_revision

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO context_packets (run_id, revision, packet_json)
                VALUES (?, ?, ?)
                """,
                (run_id, next_revision, _to_json(packet_with_revision)),
            )
            self._touch_run(connection, run_id)

        return {"run_id": run_id, "context_revision": next_revision, "context_packet": packet_with_revision}

    def read_context_packet(self, run_id: str, revision: int | None = None) -> JsonObject:
        self._require_run(run_id)
        sql = """
            SELECT revision, packet_json, created_at
            FROM context_packets
            WHERE run_id = ?
        """
        params: list[Any] = [run_id]
        if revision is not None:
            sql += " AND revision = ?"
            params.append(revision)
        sql += " ORDER BY revision DESC LIMIT 1"

        with self._connection() as connection:
            row = connection.execute(sql, params).fetchone()
        if row is None:
            return {"run_id": run_id, "context_revision": 0, "context_packet": None}
        return {
            "run_id": run_id,
            "context_revision": row["revision"],
            "created_at": row["created_at"],
            "context_packet": _from_json(row["packet_json"]),
        }

    def record_artifact_ref(
        self,
        run_id: str,
        artifact_ref: str,
        artifact_type: str,
        producer_stage: str | None = None,
        metadata: JsonObject | None = None,
    ) -> JsonObject:
        self._require_run(run_id)
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO artifact_refs (run_id, artifact_ref, artifact_type, producer_stage, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, artifact_ref, artifact_type, producer_stage, _to_json(metadata or {})),
            )
            self._touch_run(connection, run_id)
            artifact_id = cursor.lastrowid
        return {"id": artifact_id, "run_id": run_id, "artifact_ref": artifact_ref}

    def append_stage_pass(
        self,
        run_id: str,
        stage_name: str,
        stage_execution_mode: str,
        evidence: JsonObject | None = None,
        context_revision: int | None = None,
    ) -> JsonObject:
        self._require_run(run_id)
        if context_revision is not None:
            self._require_current_revision(run_id, context_revision)
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO stage_passes
                  (run_id, stage_name, stage_execution_mode, context_revision, evidence_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, stage_name, stage_execution_mode, context_revision, _to_json(evidence or {})),
            )
            self._touch_run(connection, run_id)
            stage_pass_id = cursor.lastrowid
        return {"id": stage_pass_id, "run_id": run_id, "stage_name": stage_name}

    def set_role_pass_readiness(
        self,
        run_id: str,
        role_name: str,
        ready: bool,
        context_revision: int,
        reason: str | None = None,
    ) -> JsonObject:
        self._require_current_revision(run_id, context_revision)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO readiness_flags (run_id, role_name, ready, context_revision, reason)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(run_id, role_name) DO UPDATE SET
                  ready = excluded.ready,
                  context_revision = excluded.context_revision,
                  reason = excluded.reason,
                  updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                """,
                (run_id, role_name, int(ready), context_revision, reason),
            )
            self._touch_run(connection, run_id)
        return {
            "run_id": run_id,
            "role_name": role_name,
            "ready": ready,
            "context_revision": context_revision,
        }

    def mark_stale(
        self,
        run_id: str,
        target_ref: str,
        reason: str,
        context_revision: int | None = None,
    ) -> JsonObject:
        self._require_run(run_id)
        if context_revision is not None:
            self._require_current_revision(run_id, context_revision)
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO stale_markers (run_id, target_ref, reason, context_revision)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, target_ref, reason, context_revision),
            )
            self._touch_run(connection, run_id)
            stale_marker_id = cursor.lastrowid
        return {"id": stale_marker_id, "run_id": run_id, "target_ref": target_ref}

    def record_mcp_quiescence(self, run_id: str, stage_name: str, snapshot: JsonObject) -> JsonObject:
        self._require_run(run_id)
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO mcp_quiescence_snapshots (run_id, stage_name, snapshot_json)
                VALUES (?, ?, ?)
                """,
                (run_id, stage_name, _to_json(snapshot)),
            )
            self._touch_run(connection, run_id)
            snapshot_id = cursor.lastrowid
        return {"id": snapshot_id, "run_id": run_id, "stage_name": stage_name}

    def validate_context_revision(self, run_id: str, context_revision: int) -> JsonObject:
        self._require_run(run_id)
        current_revision = self._current_revision(run_id)
        valid = context_revision == current_revision
        return {
            "run_id": run_id,
            "valid": valid,
            "provided_revision": context_revision,
            "current_revision": current_revision,
        }

    def query_run_ledger(self, run_id: str) -> JsonObject:
        self._require_run(run_id)
        with self._connection() as connection:
            run = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            artifacts = connection.execute(
                "SELECT * FROM artifact_refs WHERE run_id = ? ORDER BY id", (run_id,)
            ).fetchall()
            stage_passes = connection.execute(
                "SELECT * FROM stage_passes WHERE run_id = ? ORDER BY id", (run_id,)
            ).fetchall()
            readiness = connection.execute(
                "SELECT * FROM readiness_flags WHERE run_id = ? ORDER BY role_name", (run_id,)
            ).fetchall()
            stale_markers = connection.execute(
                "SELECT * FROM stale_markers WHERE run_id = ? ORDER BY id", (run_id,)
            ).fetchall()
        return {
            "run": _row_to_json(run, json_fields={"metadata_json"}),
            "current_revision": self._current_revision(run_id),
            "artifact_refs": [_row_to_json(row, json_fields={"metadata_json"}) for row in artifacts],
            "stage_passes": [_row_to_json(row, json_fields={"evidence_json"}) for row in stage_passes],
            "readiness_flags": [_row_to_json(row) for row in readiness],
            "stale_markers": [_row_to_json(row) for row in stale_markers],
        }

    def close_run(self, run_id: str, status: str = "closed") -> JsonObject:
        self._require_run(run_id)
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = ?,
                    closed_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                WHERE run_id = ?
                """,
                (status, run_id),
            )
        return self.query_run_ledger(run_id)

    def _require_run(self, run_id: str) -> None:
        with self._connection() as connection:
            row = connection.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise LedgerError(f"unknown run_id: {run_id}")

    def _current_revision(self, run_id: str) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(revision), 0) AS revision FROM context_packets WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return int(row["revision"])

    def _require_current_revision(self, run_id: str, context_revision: int) -> None:
        validation = self.validate_context_revision(run_id, context_revision)
        if not validation["valid"]:
            raise LedgerError(
                "stale context revision: "
                f"provided {context_revision}, current {validation['current_revision']}"
            )

    @staticmethod
    def _touch_run(connection: sqlite3.Connection, run_id: str) -> None:
        connection.execute(
            "UPDATE runs SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE run_id = ?",
            (run_id,),
        )


def _to_json(value: JsonObject) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _from_json(value: str) -> Any:
    return json.loads(value)


def _row_to_json(row: sqlite3.Row, json_fields: set[str] | None = None) -> JsonObject:
    json_fields = json_fields or set()
    result = dict(row)
    for field in json_fields:
        if field in result:
            result[field.removesuffix("_json")] = _from_json(result.pop(field))
    if "ready" in result:
        result["ready"] = bool(result["ready"])
    return result
