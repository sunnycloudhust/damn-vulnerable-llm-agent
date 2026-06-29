import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


class AuditLogger:
    """Repudiation mitigation: persist structured security events as JSON Lines."""

    def __init__(self, log_path: str = "logs/audit.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._logger = logging.getLogger("security.audit")

    @staticmethod
    def fingerprint(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def log(self, event: str, **details: Any) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **details,
        }

        try:
            with self._lock:
                with self.log_path.open("a", encoding="utf-8") as audit_file:
                    audit_file.write(
                        json.dumps(record, sort_keys=True, separators=(",", ":"))
                    )
                    audit_file.write("\n")
        except OSError:
            # Audit failure must be visible to operators without exposing secrets.
            self._logger.exception("Failed to persist security audit event")
