import sys
import os

# Add the src folder to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Now import the ExecutionGovernorClient and guarded_function
from faramesh.sdk.client import ExecutionGovernorClient, guarded_function, GovernorConfig

# Create config instance with the base URL
config = GovernorConfig(base_url="http://localhost:8000", agent_id="test-agent")

# Create the ExecutionGovernorClient instance using the config
client = ExecutionGovernorClient(config)

# Sample function to test
def sample_function(*args):
    print(f"Executing with args: {args}")
    return True

# Define action parameters
action_params = {
    'tool': 'http',
    'operation': 'fetch',
    'params': ['https://example.com', {'headers': {'Authorization': 'Bearer xyz'}}],
}

# Use guarded_function to wrap and test the function
try:
    # This should call the client.submit_action method
    result = client.submit_action(action_params['tool'], action_params['operation'], action_params['params'])
    print("Execution Result:", result)
except Exception as e:
    print(f"Execution failed: {e}")
