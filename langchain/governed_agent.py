"""
LangChain + Faramesh — governed tool example.

Requires:
    pip install faramesh langchain langchain-community

Start the server first:
    faramesh serve
"""

from faramesh.integrations import govern


def main():
    try:
        from langchain_community.tools import ShellTool
        from langchain_community.utilities import RequestsWrapper
        from langchain.tools import Tool
    except ImportError:
        print("Install dependencies: pip install langchain langchain-community")
        return

    # One line wraps any LangChain tool with Faramesh governance
    shell_tool = govern(ShellTool(), agent_id="langchain-demo")

    http_tool = govern(
        Tool(
            name="http_get",
            func=lambda url: RequestsWrapper().get(url)[:200],
            description="HTTP GET a URL",
        ),
        agent_id="langchain-demo",
    )

    print("Tools governed. Running test calls...")

    # HTTP GET — allowed by default policy
    try:
        result = http_tool.run("https://httpbin.org/get")
        print(f"[ALLOW] http_get: {result[:80]}...")
    except PermissionError as e:
        print(f"[DENY] http_get: {e}")

    # Shell command — requires approval by default policy
    try:
        result = shell_tool.run("echo 'hello from faramesh'")
        print(f"[ALLOW] shell: {result.strip()}")
    except PermissionError as e:
        print(f"[DENY/PENDING] shell: {e}")
        print("\nIf pending → open http://localhost:8000 and approve, then re-run.")


if __name__ == "__main__":
    main()
