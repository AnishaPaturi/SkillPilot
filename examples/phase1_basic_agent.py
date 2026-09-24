"""
Phase 1: Basic Agent Demonstration
Architecture: User -> LLM -> Response using LangGraph
"""
import os
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()


class MinimalAgentState(TypedDict):
    user_query: str
    response: str


def call_llm(state: MinimalAgentState) -> MinimalAgentState:
    query = state["user_query"]
    api_key = os.getenv("OPENROUTER_API_KEY")

    if api_key and api_key != "your_openrouter_api_key_here":
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        model_name = os.getenv("MODEL_NAME", "google/gemini-2.0-flash-001")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        llm = ChatOpenAI(model=model_name, openai_api_key=api_key, openai_api_base=base_url)
        res = llm.invoke([HumanMessage(content=query)])
        answer = res.content
    else:
        answer = f"[Simulated LLM Response to: '{query}']"

    return {"user_query": query, "response": answer}


def build_minimal_graph():
    graph = StateGraph(MinimalAgentState)
    graph.add_node("llm_node", call_llm)
    graph.set_entry_point("llm_node")
    graph.add_edge("llm_node", END)
    return graph.compile()


if __name__ == "__main__":
    app = build_minimal_graph()
    test_query = "What is the purpose of a skill-driven AI agent?"
    print(f"\n[Phase 1] User: {test_query}")
    output = app.invoke({"user_query": test_query})
    print(f"[Phase 1] Response:\n{output['response']}\n")
