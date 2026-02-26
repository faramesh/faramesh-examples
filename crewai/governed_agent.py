"""
CrewAI + Faramesh — governed tool example.

Requires:
    pip install faramesh crewai crewai-tools

Start the server first:
    faramesh serve
"""

from faramesh.integrations import govern_crewai_tool


def main():
    try:
        from crewai_tools import FileReadTool, DirectoryReadTool
        from crewai import Agent, Task, Crew
    except ImportError:
        print("Install dependencies: pip install crewai crewai-tools")
        return

    # One line wraps the tool with Faramesh governance
    file_tool = govern_crewai_tool(FileReadTool(), agent_id="crewai-demo")
    dir_tool = govern_crewai_tool(DirectoryReadTool(), agent_id="crewai-demo")

    researcher = Agent(
        role="Researcher",
        goal="Research topics using governed tools",
        backstory="You are a careful researcher who follows governance policies.",
        tools=[file_tool, dir_tool],
        verbose=True,
    )

    task = Task(
        description="List files in the current directory.",
        agent=researcher,
        expected_output="A list of files.",
    )

    crew = Crew(agents=[researcher], tasks=[task])
    result = crew.kickoff()
    print(result)


if __name__ == "__main__":
    main()
