from langchain.agents import Tool
from dotenv import load_dotenv
from typing import Optional

from audit_log import AuditLogger
from data_privacy import redact_transactions_for_llm
from transaction_db import TransactionDb

load_dotenv()


def create_user_tools(
    authenticated_user_id: int,
    audit_logger: Optional[AuditLogger] = None,
    request_id: Optional[str] = None):

    # Logging for mitigating repudiation
    def audit_tool_call(tool_name: str):
        if audit_logger is not None:
            audit_logger.log(
                "tool_call",
                request_id=request_id,
                authenticated_user_id=authenticated_user_id,
                tool=tool_name,
                authorization="allowed",
            )
            
    # GetCurrentUser tool
    def get_current_user(_input: str = ""):
        # Spoofing mitigation: ignore any identity claimed in the prompt.
        audit_tool_call("GetCurrentUser")
        db = TransactionDb()
        try:
            return db.get_user(authenticated_user_id)
        finally:
            db.close()

    # GetMyTransactions tool
    def get_my_transactions(_input: str = ""):
        # Elevation of Privilege mitigation: authorization is enforced at the
        # tool boundary; injected user IDs and fake observations are ignored.
        audit_tool_call("GetMyTransactions")
        db = TransactionDb()
        try:
            raw_transactions = db.get_user_transactions(authenticated_user_id)
            # Information Disclosure mitigation: exact financial details stay
            # in the backend and are removed before the Observation reaches LLM.
            return redact_transactions_for_llm(raw_transactions)
        finally:
            db.close()

    current_user_tool = Tool(
        name="GetCurrentUser",
        func=get_current_user,
        description="Returns the authenticated user only",
    )
    transactions_tool = Tool(
        name="GetMyTransactions",
        func=get_my_transactions,
        description=(
            "Returns redacted transaction summaries for the authenticated user"
        ),
    )
    return [current_user_tool, transactions_tool]
