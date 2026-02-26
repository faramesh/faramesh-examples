"""
AutoGen + Faramesh — governed function calling example.

Requires:
    pip install faramesh pyautogen

Start the server first:
    faramesh serve
"""

from faramesh.integrations import govern_autogen_function


def http_get(url: str) -> str:
    """Fetch a URL and return status + first 200 chars."""
    import requests
    r = requests.get(url, timeout=5)
    return f"HTTP {r.status_code}: {r.text[:200]}"


def shell_run(cmd: str) -> str:
    """Run a shell command and return output."""
    import subprocess
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    return r.stdout if r.returncode == 0 else f"Error: {r.stderr}"


def main():
    try:
        import autogen
    except ImportError:
        print("Install AutoGen: pip install pyautogen")
        return

    # One line wraps each function with Faramesh governance
    governed_http = govern_autogen_function(http_get, agent_id="autogen-demo", tool_name="http_get")
    governed_shell = govern_autogen_function(shell_run, agent_id="autogen-demo", tool_name="shell_run")

    assistant = autogen.AssistantAgent(
        name="assistant",
        system_message="You are a helpful assistant. Use the available functions to answer questions.",
        llm_config={
            "functions": [
                {"name": "http_get", "description": "Fetch a URL", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
                {"name": "shell_run", "description": "Run a shell command", "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}},
            ]
        },
    )

    user = autogen.UserProxyAgent(
        name="user",
        function_map={"http_get": governed_http, "shell_run": governed_shell},
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
    )

    user.initiate_chat(assistant, message="Fetch https://httpbin.org/get and show me the response.")


if __name__ == "__main__":
    main()
