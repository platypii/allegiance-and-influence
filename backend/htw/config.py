LANGGRAPH_CONFIG = {"configurable": {"thread_id": "1"}, "recursion_limit": 8}
MODEL_NAME = "claude-3-sonnet-20240229"
MODEL_CONFIG = {}
SEED_MESSAGE = """Hello. Introduce yourself briefly and tell me about your interests. Then ask me about mine."""

# Add this line to define LLM_CONFIG
LLM_CONFIG = {
    "temperature": 0.7,
    "max_tokens": 1000,
    # Add any other configuration parameters for your LLM here
}
