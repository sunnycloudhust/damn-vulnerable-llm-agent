from langchain.agents import Tool
from dotenv import load_dotenv

from transaction_db import TransactionDb

load_dotenv()


def create_user_tools(authenticated_user_id: int):
    """Create tools scoped to the authenticated user."""

    def get_current_user(_input: str = ""):
        db = TransactionDb()
        try:
            return db.get_user(authenticated_user_id)
        finally:
            db.close()

    def get_my_transactions(_input: str = ""):
        # Authorization is enforced here, outside the LLM's control.
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
