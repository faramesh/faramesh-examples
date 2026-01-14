"""
CrewAI + Faramesh Integration Example

One-line governance for CrewAI agents.

Run: python examples/crewai/governed_agent.py
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from faramesh.integrations import govern_crewai_tool

# Example: Wrap CrewAI tools with one line
def main():
    print("=" * 60)
    print("CrewAI + Faramesh Integration")
    print("=" * 60)
    print()
    
    try:
        from crewai_tools import FileReadTool, DirectoryReadTool
        
        # One-line governance!
        file_tool = govern_crewai_tool(
            FileReadTool(),
            agent_id="crewai-demo"
        )
        
        dir_tool = govern_crewai_tool(
            DirectoryReadTool(),
            agent_id="crewai-demo"
        )
        
        print("✓ Tools wrapped with Faramesh governance")
        print()
        print("Usage in CrewAI agent:")
        print("""
        from crewai import Agent, Task, Crew
        from faramesh.integrations import govern_crewai_tool
        from crewai_tools import FileReadTool
        
        # Wrap tool with one line
        tool = govern_crewai_tool(FileReadTool(), agent_id="researcher")
        
        # Use in agent
        agent = Agent(
            role='Researcher',
            goal='Research topics',
            tools=[tool],  # Governed tool
            verbose=True
        )
        """)
        
    except ImportError:
        print("CrewAI not installed. Install with:")
        print("  pip install crewai crewai-tools")
        print()
        print("Example usage:")
        print("""
        from crewai_tools import FileReadTool
        from faramesh.integrations import govern_crewai_tool
        
        # One line to add governance!
        tool = govern_crewai_tool(FileReadTool(), agent_id="my-agent")
        
        # Use in CrewAI agent
        agent = Agent(
            role='Researcher',
            tools=[tool],
            verbose=True
        )
        """)


if __name__ == "__main__":
    main()
