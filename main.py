import langchain
import streamlit as st
import os
import uuid
from dotenv import load_dotenv
from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.callbacks import StreamlitCallbackHandler
from langchain_litellm import ChatLiteLLM
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.agents import initialize_agent
from langchain.callbacks import get_openai_callback

from audit_log import AuditLogger
from rate_limiter import SqliteRateLimiter
from tools import create_user_tools
from utils import display_instructions, display_logo, fetch_model_config

load_dotenv()

authenticated_user_id = 1
# Repudiation mitigation: persist security events outside the temporary
# Streamlit session so requests can be attributed and investigated later.
audit_logger = AuditLogger()
rate_limiter = SqliteRateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "10")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
)
tools = create_user_tools(authenticated_user_id, audit_logger=audit_logger)

system_msg = """Assistant helps the authenticated user retrieve privacy-safe summaries of their recent bank transactions. Never claim to access another user's data or reveal fields marked as redacted. Authorization and data minimization are enforced by the tools."""

welcome_message = """Hi! I'm an helpful assistant and I can help fetch information about your recent transactions.\n\nTry asking me: "What are my recent transactions?"
"""

st.set_page_config(page_title="Damn Vulnerable LLM Agent")
st.title("Damn Vulnerable LLM Agent")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

#memory of llm initialization
msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=msgs, return_messages=True, memory_key="chat_history", output_key="output"
)

if len(msgs.messages) == 0:
    msgs.clear()
    msgs.add_ai_message(welcome_message)
    st.session_state.steps = {}

avatars = {"human": "user", "ai": "assistant"}
for idx, msg in enumerate(msgs.messages):
    with st.chat_message(avatars[msg.type]):
        # Render intermediate steps if any were saved
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)

if prompt := st.chat_input(placeholder="Show my recent transactions"):
    st.chat_message("user").write(prompt)
    request_id = str(uuid.uuid4())
    # DoS mitigation: reject repeated requests before creating the LLM client
    # or making any billable provider API call.
    rate_limit = rate_limiter.check(str(authenticated_user_id))
    if not rate_limit.allowed:
        audit_logger.log(
            "request_rejected",
            request_id=request_id,
            authenticated_user_id=authenticated_user_id,
            reason="rate_limit_exceeded",
        )
        st.error(
            "Too many requests. Try again in "
            f"{rate_limit.retry_after_seconds} seconds."
        )
        st.stop()

    # Repudiation mitigation: bind the request to a user, timestamp and unique request ID. Store a prompt hash instead of sensitive raw prompt content.
    audit_logger.log(
        "request_received",
        request_id=request_id,
        authenticated_user_id=authenticated_user_id,
        prompt_sha256=audit_logger.fingerprint(prompt),
        prompt_length=len(prompt),
    )
    request_tools = create_user_tools(
        authenticated_user_id,
        audit_logger=audit_logger,
        request_id=request_id,
    )

    llm = ChatLiteLLM(
        model=fetch_model_config(),
        temperature=0,
        streaming=True,
        # DoS mitigation: bound one provider call as well as generated output.
        request_timeout=int(os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "30")),
        max_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "500")),
        max_retries=1,
    )

    chat_agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=request_tools, verbose=True, system_message=system_msg)

    executor = AgentExecutor.from_agent_and_tools(
        agent=chat_agent,
        tools=request_tools,
        memory=memory,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        verbose=True,
        # DoS mitigation: cap both reasoning loops and wall-clock execution.
        max_iterations=6,
        max_execution_time=30,
    )
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        try:
            response = executor(prompt, callbacks=[st_cb])
            # Repudiation mitigation: record whether processing completed and
            # how many tool calls were made under the same request ID.
            audit_logger.log(
                "request_completed",
                request_id=request_id,
                authenticated_user_id=authenticated_user_id,
                tool_call_count=len(response["intermediate_steps"]),
            )
            st.write(response["output"])
            st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]
        except Exception as exc:
            audit_logger.log(
                "request_failed",
                request_id=request_id,
                authenticated_user_id=authenticated_user_id,
                error_type=type(exc).__name__,
            )
            raise


display_instructions()
display_logo()
