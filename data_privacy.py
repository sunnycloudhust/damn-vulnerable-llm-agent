import json

# This removes senstive information before sending to the LLM
def redact_transactions_for_llm(raw_transactions: str) -> str:
    """Remove financial details before a tool observation reaches the LLM."""
    transactions = json.loads(raw_transactions)
    redacted_transactions = [
        {
            "transactionId": transaction["transactionId"],
            "recipient": "[REDACTED]",
            "amount": "[REDACTED]",
        }
        for transaction in transactions
    ]
    return json.dumps(
        {
            "privacy_notice": (
                "Sensitive transaction fields were redacted before LLM processing."
            ),
            "transactions": redacted_transactions,
        },
        indent=4,
    )
