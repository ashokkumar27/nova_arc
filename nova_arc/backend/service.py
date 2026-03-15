from __future__ import annotations

import csv
import html
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import re
import sqlite3
import uuid

from nova_arc.config import SAMPLE_DATA_DIR
from nova_arc.core.mission_profile import utc_now


COLD_CHAIN_DEFAULTS = {
    "batch_id": "VX-204",
    "shipment_id": "SHP-884",
    "zone_id": "Zone-B",
    "destination": "Hub-2",
    "temperature_c": 11.8,
    "duration_minutes": 14,
}

GRID_OPS_DEFAULTS = {
    "transformer_id": "T-17",
    "feeder_id": "F-12",
    "site": "Substation-East",
    "load_shed_percent": "20",
}


def _json_dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, sort_keys=True)


def _json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _read_pdf_text(path: Path) -> str:
    raw_text = path.read_text(encoding="latin-1", errors="ignore")
    matches = re.findall(r"\((.*?)\)\s*Tj", raw_text, flags=re.S)
    cleaned = [match.replace(r"\(", "(").replace(r"\)", ")") for match in matches]
    if cleaned:
        return _normalize_whitespace(" ".join(cleaned))
    chunks = [match.decode("utf-8", errors="ignore") for match in re.findall(rb"[A-Za-z0-9][A-Za-z0-9 ,.\-():/]{4,}", path.read_bytes())]
    return _normalize_whitespace(" ".join(chunks))


def _read_svg_text(path: Path) -> str:
    raw_text = path.read_text(encoding="utf-8")
    matches = re.findall(r"<text[^>]*>(.*?)</text>", raw_text, flags=re.S)
    cleaned = [re.sub(r"<[^>]+>", "", html.unescape(match)) for match in matches]
    return _normalize_whitespace(" ".join(cleaned))


def _read_csv_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            message = row.get("message", "")
            source = row.get("source", "")
            timestamp = row.get("timestamp", "")
            event_type = row.get("event_type", "")
            rows.append(f"{timestamp} {event_type} {source}: {message}")
    return _normalize_whitespace(" ".join(rows))


def _read_plain_text(path: Path) -> str:
    raw_text = path.read_text(encoding="utf-8")
    raw_text = re.sub(r"^#+\s*", "", raw_text, flags=re.M)
    raw_text = re.sub(r"^\-\s*", "", raw_text, flags=re.M)
    return _normalize_whitespace(raw_text)


def _read_source_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _read_pdf_text(path)
    if path.suffix.lower() == ".svg":
        return _read_svg_text(path)
    if path.suffix.lower() == ".csv":
        return _read_csv_text(path)
    return _read_plain_text(path)


class CommandCenterBackend:
    def __init__(self, db_path: str, sample_data_root: Path | None = None):
        self.db_path = Path(db_path)
        self.sample_data_root = sample_data_root or SAMPLE_DATA_DIR
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE NOT NULL,
                    pack_id TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    context TEXT,
                    transcript TEXT,
                    summary TEXT,
                    status TEXT,
                    hazards_json TEXT,
                    signals_json TEXT,
                    confidence REAL,
                    risk_score INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pack_id TEXT NOT NULL,
                    batch_id TEXT UNIQUE NOT NULL,
                    product_name TEXT,
                    status TEXT,
                    zone_id TEXT,
                    notes TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS shipments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pack_id TEXT NOT NULL,
                    shipment_id TEXT UNIQUE NOT NULL,
                    destination TEXT,
                    route TEXT,
                    status TEXT,
                    notes TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT UNIQUE NOT NULL,
                    incident_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details_json TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT UNIQUE NOT NULL,
                    pack_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    path TEXT NOT NULL,
                    content_text TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    def bootstrap(self, reset: bool = False, pack_id: str | None = None) -> Dict[str, Any]:
        self.initialize()
        self._seed_evidence_sources()
        if reset:
            if pack_id:
                self._reset_pack_state(pack_id)
            else:
                for current_pack in ("cold_chain", "grid_ops"):
                    self._reset_pack_state(current_pack)
        return self.health()

    def health(self) -> Dict[str, Any]:
        self.initialize()
        with self._connect() as conn:
            incident_count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
            evidence_count = conn.execute("SELECT COUNT(*) FROM evidence_sources").fetchone()[0]
            batch_count = conn.execute("SELECT COUNT(*) FROM batches").fetchone()[0]
            shipment_count = conn.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
        return {
            "ok": True,
            "db_path": str(self.db_path),
            "incidents": incident_count,
            "evidence_sources": evidence_count,
            "batches": batch_count,
            "shipments": shipment_count,
        }

    def ingest_incident(self, pack_id: str, scenario: str, context: str, transcript: str) -> Dict[str, Any]:
        self.initialize()
        transcript = (transcript or "").strip()
        if scenario == "cold_chain":
            signals = self._parse_cold_chain_signals(transcript)
            hazards = [
                "temperature_excursion",
                "inventory_spoilage_risk",
                "regulatory_non_compliance",
            ]
            confidence = 0.96
            risk_score = 84
            summary = (
                f"{signals['zone_id']} is above threshold at {signals['temperature_c']}C for "
                f"{signals['duration_minutes']} minutes. Batch {signals['batch_id']} is at risk. "
                f"Shipment {signals['shipment_id']} is loading now."
            )
            self._upsert_batch(
                pack_id=pack_id,
                batch_id=signals["batch_id"],
                product_name="mRNA Vaccine Lots",
                status="at_risk",
                zone_id=signals["zone_id"],
                notes="Monitoring pending quarantine decision.",
            )
            self._upsert_shipment(
                pack_id=pack_id,
                shipment_id=signals["shipment_id"],
                destination=signals["destination"],
                route="Dock-3 -> Hub-2",
                status="loading",
                notes="Outbound load in progress.",
            )
        else:
            signals = self._parse_grid_ops_signals(transcript)
            hazards = ["thermal_failure", "arc_fault_risk", "cascading_outage"]
            confidence = 0.93
            risk_score = 88
            summary = (
                f"Transformer {signals['transformer_id']} is overheating and feeder {signals['feeder_id']} "
                f"is under stress at {signals['site']}."
            )

        incident_id = f"{pack_id}-{uuid.uuid4().hex[:8]}"
        timestamp = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO incidents (
                    incident_id, pack_id, scenario, context, transcript, summary, status,
                    hazards_json, signals_json, confidence, risk_score, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    pack_id,
                    scenario,
                    context,
                    transcript,
                    summary,
                    "open",
                    _json_dumps(hazards),
                    _json_dumps(signals),
                    confidence,
                    risk_score,
                    timestamp,
                    timestamp,
                ),
            )
        return self.get_incident(incident_id)

    def get_incident(self, incident_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)).fetchone()
        if not row:
            raise KeyError(f"Unknown incident_id: {incident_id}")
        return self._incident_row_to_dict(row)

    def latest_incident(self, pack_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM incidents WHERE pack_id = ? ORDER BY id DESC LIMIT 1",
                (pack_id,),
            ).fetchone()
        return self._incident_row_to_dict(row) if row else None

    def get_dashboard(self, pack_id: str, incident_id: str | None = None) -> Dict[str, Any]:
        incident = self.get_incident(incident_id) if incident_id else self.latest_incident(pack_id)
        with self._connect() as conn:
            batches = [
                dict(row)
                for row in conn.execute(
                    "SELECT batch_id, product_name, status, zone_id, notes, updated_at FROM batches WHERE pack_id = ? ORDER BY batch_id",
                    (pack_id,),
                ).fetchall()
            ]
            shipments = [
                dict(row)
                for row in conn.execute(
                    "SELECT shipment_id, destination, route, status, notes, updated_at FROM shipments WHERE pack_id = ? ORDER BY shipment_id",
                    (pack_id,),
                ).fetchall()
            ]
            actions = []
            if incident:
                action_rows = conn.execute(
                    """
                    SELECT action_id, incident_id, tool_name, status, details_json, created_at
                    FROM action_log
                    WHERE incident_id = ?
                    ORDER BY id ASC
                    """,
                    (incident["incident_id"],),
                ).fetchall()
                actions = [{**dict(row), "details": _json_loads(row["details_json"], {})} for row in action_rows]
        return {
            "incident": incident,
            "batches": batches,
            "shipments": shipments,
            "actions": actions,
        }

    def start_backup_cooling(self, pack_id: str, zone_id: str, incident_id: str | None = None) -> Dict[str, Any]:
        incident = self._require_incident(pack_id, incident_id)
        signals = dict(incident["signals"])
        signals["cooling_status"] = "cooling_started"
        signals["temperature_trend"] = "falling"
        signals["stabilization_eta_minutes"] = 6
        updated_at = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE incidents
                SET status = ?, signals_json = ?, risk_score = ?, updated_at = ?
                WHERE incident_id = ?
                """,
                ("cooling_started", _json_dumps(signals), max(45, incident["risk_score"] - 18), updated_at, incident["incident_id"]),
            )
        details = {
            "zone_id": zone_id,
            "incident_status": "cooling_started",
            "temperature_trend": "falling",
            "stabilization_eta_minutes": 6,
        }
        self._log_action(incident["incident_id"], "start_backup_cooling", "completed", details)
        return {"status": "cooling_started", "details": details, "incident": self.get_incident(incident["incident_id"])}

    def quarantine_batch(
        self,
        pack_id: str,
        batch_id: str,
        reason: str,
        incident_id: str | None = None,
        via: str = "api",
    ) -> Dict[str, Any]:
        incident = self._require_incident(pack_id, incident_id)
        updated_at = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE batches
                SET status = ?, notes = ?, updated_at = ?
                WHERE batch_id = ?
                """,
                ("quarantined", reason, updated_at, batch_id),
            )
        details = {"batch_id": batch_id, "reason": reason, "execution_path": via, "batch_status": "quarantined"}
        self._log_action(incident["incident_id"], "quarantine_batch", "completed", details)
        return {"status": "quarantined", "details": details, "batch": self.get_batch(batch_id)}

    def hold_shipment(
        self,
        pack_id: str,
        shipment_id: str,
        reason: str,
        incident_id: str | None = None,
        via: str = "api",
        disposition: str = "held",
    ) -> Dict[str, Any]:
        incident = self._require_incident(pack_id, incident_id)
        updated_at = utc_now()
        route = "Inspection Bay" if disposition == "held" else "Alternate cold dock"
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE shipments
                SET status = ?, route = ?, notes = ?, updated_at = ?
                WHERE shipment_id = ?
                """,
                (disposition, route, reason, updated_at, shipment_id),
            )
        details = {
            "shipment_id": shipment_id,
            "reason": reason,
            "execution_path": via,
            "shipment_status": disposition,
            "route": route,
        }
        self._log_action(incident["incident_id"], "hold_shipment", "completed", details)
        return {"status": disposition, "details": details, "shipment": self.get_shipment(shipment_id)}

    def record_notification(
        self,
        pack_id: str,
        channel: str,
        provider: str,
        message: str,
        incident_id: str | None = None,
        external_status: str = "queued",
    ) -> Dict[str, Any]:
        incident = self._require_incident(pack_id, incident_id)
        details = {
            "channel": channel,
            "provider": provider,
            "message": message,
            "external_status": external_status,
        }
        self._log_action(incident["incident_id"], "notify_team", "completed", details)
        return {"status": "completed", "details": details}

    def get_batch(self, batch_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT batch_id, product_name, status, zone_id, notes, updated_at FROM batches WHERE batch_id = ?",
                (batch_id,),
            ).fetchone()
        if not row:
            raise KeyError(f"Unknown batch_id: {batch_id}")
        return dict(row)

    def get_shipment(self, shipment_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT shipment_id, destination, route, status, notes, updated_at FROM shipments WHERE shipment_id = ?",
                (shipment_id,),
            ).fetchone()
        if not row:
            raise KeyError(f"Unknown shipment_id: {shipment_id}")
        return dict(row)

    def search_evidence(self, pack_id: str, query_text: str, top_k: int = 4) -> Dict[str, Any]:
        self._seed_evidence_sources()
        query_tokens = _tokenize(query_text)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT source_id, pack_id, source_type, title, path, content_text, metadata_json FROM evidence_sources WHERE pack_id = ?",
                (pack_id,),
            ).fetchall()

        ranked = []
        for row in rows:
            metadata = _json_loads(row["metadata_json"], {})
            corpus_text = " ".join(
                [
                    row["title"],
                    row["content_text"],
                    metadata.get("description", ""),
                    " ".join(metadata.get("keywords", [])),
                ]
            )
            corpus_tokens = _tokenize(corpus_text)
            overlap = len(query_tokens & corpus_tokens)
            score = 0.35 + (overlap * 0.08)
            if any(token in corpus_tokens for token in {"vx", "204", "shp", "884", "zone", "temperature", "batch"}):
                score += 0.08
            score = round(min(score, 0.99), 2)
            ranked.append(
                {
                    "id": row["source_id"],
                    "pack_id": row["pack_id"],
                    "modality": row["source_type"],
                    "source_label": metadata.get("source_label", row["source_type"].title()),
                    "title": row["title"],
                    "score": score,
                    "snippet": self._snippet(row["content_text"], query_tokens),
                    "path": row["path"],
                    "metadata": metadata,
                    "matched_terms": sorted(query_tokens & corpus_tokens),
                }
            )

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return {
            "matches": ranked[:top_k],
            "trace": {
                "query": query_text,
                "query_tokens": sorted(query_tokens),
                "ranked_source_ids": [item["id"] for item in ranked[:top_k]],
            },
        }

    def run_admin_workflow(self, pack_id: str, workflow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        run_id = f"act-{uuid.uuid4().hex[:8]}"
        if workflow_id == "quarantine_batch_v1":
            result = self.quarantine_batch(
                pack_id=pack_id,
                batch_id=parameters["batch_id"],
                reason=parameters.get("reason", "Quarantined via admin workflow"),
                incident_id=parameters.get("incident_id"),
                via="nova_act_bridge",
            )
            summary = f"Batch {parameters['batch_id']} quarantined through the admin portal."
        elif workflow_id == "hold_shipment_v1":
            result = self.hold_shipment(
                pack_id=pack_id,
                shipment_id=parameters["shipment_id"],
                reason=parameters.get("reason", "Shipment held via admin workflow"),
                incident_id=parameters.get("incident_id"),
                via="nova_act_bridge",
                disposition=parameters.get("disposition", "held"),
            )
            summary = f"Shipment {parameters['shipment_id']} set to {result['status']} through the admin portal."
        elif workflow_id == "isolate_transformer_v1":
            result = {
                "status": "isolated",
                "details": {
                    "transformer_id": parameters["transformer_id"],
                    "execution_path": "nova_act_bridge",
                },
            }
            summary = f"Transformer {parameters['transformer_id']} isolated through the admin portal."
        else:
            raise ValueError(f"Unsupported workflow_id: {workflow_id}")

        step_log = [
            {"status": "completed", "title": "Open admin portal", "detail": self.admin_portal_url(pack_id)},
            {"status": "completed", "title": "Locate record", "detail": json.dumps(parameters, sort_keys=True)},
            {"status": "completed", "title": "Apply workflow", "detail": summary},
        ]
        return {
            "run_id": run_id,
            "status": "completed",
            "summary": summary,
            "portal_url": self.admin_portal_url(pack_id),
            "steps": step_log,
            "artifacts": {
                "portal_url": self.admin_portal_url(pack_id),
                "snapshot": self.get_dashboard(pack_id, incident_id=parameters.get("incident_id")),
            },
            "result": result,
        }

    def admin_portal_url(self, pack_id: str) -> str:
        return f"/admin?pack_id={pack_id}"

    def render_admin_portal_html(self, pack_id: str = "cold_chain") -> str:
        snapshot = self.get_dashboard(pack_id)
        incident = snapshot.get("incident") or {}

        def table_rows(records: Iterable[Dict[str, Any]], columns: List[str]) -> str:
            rows = []
            for record in records:
                cells = "".join(f"<td>{record.get(column, '')}</td>" for column in columns)
                rows.append(f"<tr>{cells}</tr>")
            return "".join(rows) or f"<tr><td colspan='{len(columns)}'>No records</td></tr>"

        return f"""
        <html>
          <head>
            <title>Nova A.R.C. Admin Portal</title>
            <style>
              body {{ font-family: 'Segoe UI', sans-serif; margin: 24px; background: #f4f7fb; color: #10233a; }}
              .shell {{ max-width: 1080px; margin: 0 auto; }}
              .card {{ background: white; border-radius: 18px; padding: 18px; margin-bottom: 16px; box-shadow: 0 8px 24px rgba(16,35,58,.08); }}
              table {{ width: 100%; border-collapse: collapse; }}
              th, td {{ border-bottom: 1px solid #e5edf6; text-align: left; padding: 10px; }}
              .pill {{ display: inline-block; padding: 4px 10px; border-radius: 999px; background: #dbeafe; color: #12428a; font-weight: 700; }}
            </style>
          </head>
          <body>
            <div class="shell">
              <div class="card">
                <div class="pill">Local Demo Portal</div>
                <h1>Nova A.R.C. Operations Admin</h1>
                <p>Pack: {pack_id} | Incident: {incident.get('incident_id', 'n/a')} | Status: {incident.get('status', 'idle')}</p>
              </div>
              <div class="card">
                <h2>Batches</h2>
                <table>
                  <thead><tr><th>Batch</th><th>Product</th><th>Status</th><th>Zone</th><th>Notes</th></tr></thead>
                  <tbody>{table_rows(snapshot.get('batches', []), ['batch_id', 'product_name', 'status', 'zone_id', 'notes'])}</tbody>
                </table>
              </div>
              <div class="card">
                <h2>Shipments</h2>
                <table>
                  <thead><tr><th>Shipment</th><th>Status</th><th>Destination</th><th>Route</th><th>Notes</th></tr></thead>
                  <tbody>{table_rows(snapshot.get('shipments', []), ['shipment_id', 'status', 'destination', 'route', 'notes'])}</tbody>
                </table>
              </div>
            </div>
          </body>
        </html>
        """

    def _seed_evidence_sources(self) -> None:
        self.initialize()
        for pack_id in ("cold_chain", "grid_ops"):
            manifest_path = self.sample_data_root / pack_id / "evidence" / "manifest.json"
            if not manifest_path.exists():
                continue
            entries = json.loads(manifest_path.read_text(encoding="utf-8"))
            with self._connect() as conn:
                for entry in entries:
                    existing = conn.execute(
                        "SELECT id FROM evidence_sources WHERE source_id = ?",
                        (entry["source_id"],),
                    ).fetchone()
                    source_path = manifest_path.parent / entry["path"]
                    content_text = _read_source_text(source_path)
                    if existing:
                        conn.execute(
                            """
                            UPDATE evidence_sources
                            SET pack_id = ?, source_type = ?, title = ?, path = ?, content_text = ?, metadata_json = ?
                            WHERE source_id = ?
                            """,
                            (
                                pack_id,
                                entry["source_type"],
                                entry["title"],
                                str(source_path),
                                content_text,
                                _json_dumps(entry),
                                entry["source_id"],
                            ),
                        )
                    else:
                        conn.execute(
                            """
                            INSERT INTO evidence_sources (
                                source_id, pack_id, source_type, title, path, content_text, metadata_json, created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                entry["source_id"],
                                pack_id,
                                entry["source_type"],
                                entry["title"],
                                str(source_path),
                                content_text,
                                _json_dumps(entry),
                                utc_now(),
                            ),
                        )

    def _reset_pack_state(self, pack_id: str) -> None:
        if pack_id == "cold_chain":
            self._upsert_batch(
                pack_id="cold_chain",
                batch_id=COLD_CHAIN_DEFAULTS["batch_id"],
                product_name="mRNA Vaccine Lots",
                status="at_risk",
                zone_id=COLD_CHAIN_DEFAULTS["zone_id"],
                notes="Monitoring pending containment run.",
            )
            self._upsert_shipment(
                pack_id="cold_chain",
                shipment_id=COLD_CHAIN_DEFAULTS["shipment_id"],
                destination=COLD_CHAIN_DEFAULTS["destination"],
                route="Dock-3 -> Hub-2",
                status="loading",
                notes="Outbound load in progress.",
            )

    def _upsert_batch(self, pack_id: str, batch_id: str, product_name: str, status: str, zone_id: str, notes: str) -> None:
        updated_at = utc_now()
        with self._connect() as conn:
            existing = conn.execute("SELECT 1 FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE batches
                    SET pack_id = ?, product_name = ?, status = ?, zone_id = ?, notes = ?, updated_at = ?
                    WHERE batch_id = ?
                    """,
                    (pack_id, product_name, status, zone_id, notes, updated_at, batch_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO batches (pack_id, batch_id, product_name, status, zone_id, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (pack_id, batch_id, product_name, status, zone_id, notes, updated_at),
                )

    def _upsert_shipment(self, pack_id: str, shipment_id: str, destination: str, route: str, status: str, notes: str) -> None:
        updated_at = utc_now()
        with self._connect() as conn:
            existing = conn.execute("SELECT 1 FROM shipments WHERE shipment_id = ?", (shipment_id,)).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE shipments
                    SET pack_id = ?, destination = ?, route = ?, status = ?, notes = ?, updated_at = ?
                    WHERE shipment_id = ?
                    """,
                    (pack_id, destination, route, status, notes, updated_at, shipment_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO shipments (pack_id, shipment_id, destination, route, status, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (pack_id, shipment_id, destination, route, status, notes, updated_at),
                )

    def _log_action(self, incident_id: str, tool_name: str, status: str, details: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO action_log (action_id, incident_id, tool_name, status, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (f"act-{uuid.uuid4().hex[:10]}", incident_id, tool_name, status, _json_dumps(details), utc_now()),
            )

    def _require_incident(self, pack_id: str, incident_id: str | None) -> Dict[str, Any]:
        incident = self.get_incident(incident_id) if incident_id else self.latest_incident(pack_id)
        if not incident:
            raise KeyError(f"No active incident found for pack_id: {pack_id}")
        return incident

    def _incident_row_to_dict(self, row: sqlite3.Row | None) -> Dict[str, Any]:
        if row is None:
            return {}
        data = dict(row)
        data["hazards"] = _json_loads(data.pop("hazards_json"), [])
        data["signals"] = _json_loads(data.pop("signals_json"), {})
        return data

    def _snippet(self, text: str, query_tokens: set[str], size: int = 180) -> str:
        if not text:
            return ""
        normalized_text = _normalize_whitespace(text)
        lowered = normalized_text.lower()
        for token in query_tokens:
            index = lowered.find(token)
            if index >= 0:
                start = max(0, index - 40)
                end = min(len(normalized_text), index + size)
                return normalized_text[start:end]
        return normalized_text[:size]

    def _parse_cold_chain_signals(self, transcript: str) -> Dict[str, Any]:
        zone_match = re.search(r"zone\s+([a-z])", transcript, flags=re.I)
        batch_match = re.search(r"batch\s+([A-Z0-9-]+)", transcript, flags=re.I)
        shipment_match = re.search(r"shipment\s+([A-Z0-9-]+)", transcript, flags=re.I)
        temperature_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:c|degrees)", transcript, flags=re.I)
        duration_match = re.search(r"(\d+)\s*minutes?", transcript, flags=re.I)

        zone_id = f"Zone-{zone_match.group(1).upper()}" if zone_match else COLD_CHAIN_DEFAULTS["zone_id"]
        return {
            "zone_id": zone_id,
            "batch_id": batch_match.group(1).upper() if batch_match else COLD_CHAIN_DEFAULTS["batch_id"],
            "shipment_id": shipment_match.group(1).upper() if shipment_match else COLD_CHAIN_DEFAULTS["shipment_id"],
            "destination": COLD_CHAIN_DEFAULTS["destination"],
            "temperature_c": float(temperature_match.group(1)) if temperature_match else COLD_CHAIN_DEFAULTS["temperature_c"],
            "duration_minutes": int(duration_match.group(1)) if duration_match else COLD_CHAIN_DEFAULTS["duration_minutes"],
        }

    def _parse_grid_ops_signals(self, transcript: str) -> Dict[str, Any]:
        transformer_match = re.search(r"transformer\s+([A-Z0-9-]+)", transcript, flags=re.I)
        feeder_match = re.search(r"feeder\s+([A-Z0-9-]+)", transcript, flags=re.I)
        site_match = re.search(r"substation\s+([A-Za-z-]+)", transcript, flags=re.I)
        return {
            "transformer_id": transformer_match.group(1).upper() if transformer_match else GRID_OPS_DEFAULTS["transformer_id"],
            "feeder_id": feeder_match.group(1).upper() if feeder_match else GRID_OPS_DEFAULTS["feeder_id"],
            "site": f"Substation-{site_match.group(1).title()}" if site_match else GRID_OPS_DEFAULTS["site"],
            "load_shed_percent": GRID_OPS_DEFAULTS["load_shed_percent"],
        }
