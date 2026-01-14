"""
AutoGen + Faramesh Integration Example

One-line governance for AutoGen function calling.

Run: python examples/autogen/governed_agent.py
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from faramesh.integrations import govern_autogen_function

# Example functions to govern
def http_get(url: str) -> str:
    """Fetch a URL."""
    import requests
    response = requests.get(url, timeout=5)
    return f"Status {response.status_code}: {response.text[:100]}"


def shell_command(cmd: str) -> str:
    """Execute a shell command."""
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        return f"Error: {result.stderr}"
    return result.stdout


def main():
    print("=" * 60)
    print("AutoGen + Faramesh Integration")
    print("=" * 60)
    print()
    
    try:
        import autogen
        
        # One-line governance!
        governed_http = govern_autogen_function(
            http_get,
            agent_id="autogen-demo",
            tool_name="http_get"
        )
        
        governed_shell = govern_autogen_function(
            shell_command,
            agent_id="autogen-demo",
            tool_name="shell_command"
        )
        
        print("✓ Functions wrapped with Faramesh governance")
        print()
        print("Usage in AutoGen agent:")
        print("""
        import autogen
        from faramesh.integrations import govern_autogen_function
        
        def my_function(url: str) -> str:
            import requests
            return requests.get(url).text
        
        # One line to add governance!
        governed_func = govern_autogen_function(
            my_function,
            agent_id="assistant",
            tool_name="http_get"
        )
        
        # Use in AutoGen agent
        agent = autogen.AssistantAgent(
            name="assistant",
            system_message="You are a helpful assistant.",
            function_map={"http_get": governed_func}
        )
        """)
        
    except ImportError:
        print("AutoGen not installed. Install with:")
        print("  pip install pyautogen")
        print()
        print("Example usage:")
        print("""
        import autogen
        from faramesh.integrations import govern_autogen_function
        
        def my_function(url: str) -> str:
            import requests
            return requests.get(url).text
        
        # One line to add governance!
        governed_func = govern_autogen_function(
            my_function,
            agent_id="assistant",
            tool_name="http_get"
        )
        
        agent = autogen.AssistantAgent(
            name="assistant",
            function_map={"http_get": governed_func}
        )
        """)


if __name__ == "__main__":
    main()
