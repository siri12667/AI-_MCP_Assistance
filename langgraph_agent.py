import os
import sys
import asyncio

from pathlib import Path
from typing import TypedDict, Annotated

from dotenv import load_dotenv

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.graph.message import add_messages

from langchain_core.messages import (
    HumanMessage,
    ToolMessage
)

from langchain_ollama import ChatOllama

from langchain_mcp_adapters.client import (
    MultiServerMCPClient
)


# ---------------------------------------
# Load environment variables
# ---------------------------------------

load_dotenv()


# ---------------------------------------
# MCP Server location
# ---------------------------------------

SERVER_SCRIPT = (
    Path(__file__).parent / "mcp_server.py"
)


# ---------------------------------------
# LangGraph State
# ---------------------------------------

class State(TypedDict):
    messages: Annotated[list, add_messages]


# ---------------------------------------
# Build LangGraph
# ---------------------------------------

async def build_graph():

    # -----------------------------------
    # Connect to MCP Server
    # -----------------------------------

    client = MultiServerMCPClient(
        {
            "ai-personal-assistant": {
                "command": sys.executable,
                "args": [str(SERVER_SCRIPT)],
                "transport": "stdio",
            }
        }
    )

    # Get MCP tools
    mcp_tools = await client.get_tools()

    # Create lookup dictionary
    tools_by_name = {
        tool.name: tool
        for tool in mcp_tools
    }

    print(
        "\nLoaded MCP tools:"
    )

    for tool_name in tools_by_name:
        print(
            f"  - {tool_name}"
        )

    # -----------------------------------
    # Create LLM
    # -----------------------------------

    llm = ChatOllama(
    model="llama3.2",
    temperature=0
).bind_tools(mcp_tools)

    # -----------------------------------
    # LLM Node
    # -----------------------------------

    def llm_node(state: State) -> dict:

        response = llm.invoke(
            state["messages"]
        )

        return {
            "messages": [response]
        }

    # -----------------------------------
    # Tools Node
    # -----------------------------------

    async def tools_node(state: State) -> dict:

        last_message = state["messages"][-1]

        tool_messages = []

        for call in last_message.tool_calls:

            tool_name = call["name"]

            tool_args = call["args"]

            print(
                f"\nCalling MCP tool: "
                f"{tool_name}"
            )

            print(
                f"Arguments: {tool_args}"
            )

            tool = tools_by_name[tool_name]

            result = await tool.ainvoke(
                tool_args
            )

            print(
                f"Tool result: {result}"
            )

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call["id"]
                )
            )

        return{

        "message":tool_messages
        }

    # -----------------------------------
    # Router
    # -----------------------------------

    def route_after_llm(
        state: State
    ) -> str:

        last_message = state["messages"][-1]

        if getattr(
            last_message,
            "tool_calls",
            None
        ):
            return "use_tools"

        return "done"

    # -----------------------------------
    # Create Graph
    # -----------------------------------

    builder = StateGraph(State)

    builder.add_node(
        "llm",
        llm_node
    )

    builder.add_node(
        "tools",
        tools_node
    )

    # START → LLM

    builder.add_edge(
        START,
        "llm"
    )

    # LLM → Tools OR END

    builder.add_conditional_edges(
        "llm",
        route_after_llm,
        {
            "use_tools": "tools",
            "done": END
        }
    )

    # Tools → LLM

    builder.add_edge(
        "tools",
        "llm"
    )

    # Compile

    return builder.compile()


# ---------------------------------------
# Main Application
# ---------------------------------------

async def main():

    graph = await build_graph()

    print(
        "\n================================"
    )

    print(
        " AI PERSONAL ASSISTANT"
    )

    print(
        " LangGraph + MCP"
    )

    print(
        "================================\n"
    )

    while True:

        user_input = input(
            "\nYou: "
        ).strip()

        if user_input.lower() in {
            "exit",
            "quit",
            "bye"
        }:

            print(
                "\nGoodbye!"
            )

            break

        if not user_input:

            continue

        result = await graph.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content=user_input
                    )
                ]
            }
        )

        final_message = (
            result["messages"][-1]
        )

        print(
            "\nAssistant:",
            final_message.content
        )


# ---------------------------------------
# Run
# ---------------------------------------

if __name__ == "__main__":

    asyncio.run(main())