import json
import unittest

from data_privacy import redact_transactions_for_llm


class DataPrivacyTest(unittest.TestCase):
    def test_redacts_sensitive_transaction_fields(self):
        raw_transactions = json.dumps(
            [
                {
                    "transactionId": 1,
                    "userId": 1,
                    "reference": "Private purchase",
                    "recipient": "Sensitive Recipient",
                    "amount": 1234.56,
                }
            ]
        )

        redacted = redact_transactions_for_llm(raw_transactions)
        payload = json.loads(redacted)

        self.assertNotIn("Private purchase", redacted)
        self.assertNotIn("Sensitive Recipient", redacted)
        self.assertNotIn("1234.56", redacted)
        self.assertNotIn("userId", redacted)
        self.assertEqual(
            payload["transactions"],
            [
                {
                    "transactionId": 1,
                    "recipient": "[REDACTED]",
                    "amount": "[REDACTED]",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
