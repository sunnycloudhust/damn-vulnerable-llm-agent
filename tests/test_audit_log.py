import json
import tempfile
import unittest
from pathlib import Path

from audit_log import AuditLogger


class AuditLoggerTest(unittest.TestCase):
    def test_writes_persistent_structured_event_without_raw_prompt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "audit.jsonl"
            logger = AuditLogger(str(log_path))
            prompt = "sensitive prompt"

            logger.log(
                "request_received",
                request_id="request-123",
                authenticated_user_id=1,
                prompt_sha256=logger.fingerprint(prompt),
                prompt_length=len(prompt),
            )

            record = json.loads(log_path.read_text(encoding="utf-8"))

        self.assertEqual(record["event"], "request_received")
        self.assertEqual(record["request_id"], "request-123")
        self.assertEqual(record["authenticated_user_id"], 1)
        self.assertEqual(record["prompt_length"], len(prompt))
        self.assertNotIn(prompt, json.dumps(record))
        self.assertIn("timestamp", record)


if __name__ == "__main__":
    unittest.main()
