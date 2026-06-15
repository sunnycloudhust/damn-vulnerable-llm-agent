from langchain.agents import Tool
from dotenv import load_dotenv
from typing import Optional

from audit_log import AuditLogger
from transaction_db import TransactionDb

load_dotenv()


def create_user_tools(
    authenticated_user_id: int,
    audit_logger: Optional[AuditLogger] = None,
    request_id: Optional[str] = None,
):
    """Create tools whose authorization scope cannot be changed by the LLM."""

    def audit_tool_call(tool_name: str):
        if audit_logger is not None:
            # Repudiation mitigation: record which authorized tool was executed
            # for this user and request independently of Streamlit chat memory.
            audit_logger.log(
                "tool_call",
                request_id=request_id,
                authenticated_user_id=authenticated_user_id,
                tool=tool_name,
                authorization="allowed",
            )

    def get_current_user(_input: str = ""):
        # Spoofing mitigation: ignore any identity claimed in the prompt.
        audit_tool_call("GetCurrentUser")
        db = TransactionDb()
        try:
            return db.get_user(authenticated_user_id)
        finally:
            db.close()

    def get_my_transactions(_input: str = ""):
        # Elevation of Privilege mitigation: authorization is enforced at the
        # tool boundary; injected user IDs and fake observations are ignored.
        audit_tool_call("GetMyTransactions")
        db = TransactionDb()
        try:
            return db.get_user_transactions(authenticated_user_id)
        finally:
            db.close()

    current_user_tool = Tool(
        name="GetCurrentUser",
        func=get_current_user,
        description="Returns the authenticated user. This tool accepts no user ID.",
    )
    transactions_tool = Tool(
        name="GetMyTransactions",
        func=get_my_transactions,
        description=(
            "Returns transactions for the authenticated user. "
            "Any user ID in the tool input is ignored."
        ),
    )
    return [current_user_tool, transactions_tool]
