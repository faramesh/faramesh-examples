"""Example: Using Faramesh with LangChain agents.

This example demonstrates how to use Faramesh to govern LangChain agent
actions through policy enforcement.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from langchain.agents import initialize_agent, AgentType
    from langchain.llms import OpenAI
    from langchain.tools import ShellTool
    from faramesh.integrations.langchain import GovernedAgentExecutor, GovernedTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain not available. Install with: pip install langchain openai")

from faramesh.sdk import ExecutionGovernorClient


def main():
    """Example: Governed LangChain agent."""
    if not LANGCHAIN_AVAILABLE:
        print("LangChain not available. Skipping example.")
        return
    
    # Configure Faramesh client
    client = ExecutionGovernorClient.from_env()
    
    print("🚀 LangChain + Faramesh Example")
    print("=" * 50)
    
    # Example 1: Governed Tool
    print("\n1. Governed Tool Example:")
    print("-" * 30)
    
    shell_tool = ShellTool()
    governed_shell = GovernedTool(
        tool=shell_tool,
        agent_id="langchain-example",
        client=client
    )
    
    try:
        result = governed_shell.run("echo 'Hello from governed tool!'")
        print(f"✅ Tool result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Governed Agent (if OpenAI is configured)
    if os.getenv("OPENAI_API_KEY"):
        print("\n2. Governed Agent Example:")
        print("-" * 30)
        
        try:
            llm = OpenAI(temperature=0)
            tools = [
                GovernedTool(
                    tool=ShellTool(),
                    agent_id="langchain-example",
                    client=client
                )
            ]
            
            agent = initialize_agent(
                tools,
                llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )
            
            governed_agent = GovernedAgentExecutor(
                agent_executor=agent,
                agent_id="langchain-example",
                client=client
            )
            
            # This would be governed through Faramesh
            # result = governed_agent.run("List files in current directory")
            # print(f"✅ Agent result: {result}")
            
            print("✅ Governed agent created (not executing to avoid costs)")
        except Exception as e:
            print(f"❌ Error creating agent: {e}")
    else:
        print("\n2. Governed Agent Example:")
        print("-" * 30)
        print("⚠️  Set OPENAI_API_KEY to enable agent example")
    
    print("\n" + "=" * 50)
    print("✅ Example complete!")


if __name__ == "__main__":
    main()
