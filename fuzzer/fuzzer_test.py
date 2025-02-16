import os
import sys
import json
import base64
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now import the modules
from oracle.oracle import Oracle
from oracle.permission_model import PermissionModel
from fuzzer.fuzzer import User, fuzz_requests

def decode_jwt(token: str) -> Dict:
    """Decode a JWT token without verification."""
    if token.startswith('Bearer '):
        token = token[7:]  # Remove 'Bearer ' prefix
        
    # Split the token into parts
    try:
        header, payload, signature = token.split('.')
        # Pad the payload if necessary
        payload += '=' * (-len(payload) % 4)
        # Decode the payload
        decoded = base64.b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding token: {e}")
        return {}

def extract_users_from_log(network_log_file: str) -> List[User]:
    """
    Extract unique users and their tokens from the network log.
    
    Args:
        network_log_file: Path to the network log JSON file
        
    Returns:
        List of User objects with their roles and tokens
    """
    with open(network_log_file, 'r') as f:
        network_log = json.load(f)
    
    # Track unique users and their tokens
    users_by_id: Dict[str, User] = {}
    
    # Process each request in the log
    for entry in network_log.get("requests", []):
        request = entry.get("request", {})
        headers = request.get("headers", {})
        response = entry.get("response", {})
        
        # Check for authorization token in request headers
        auth_token = headers.get("authorization")
        if auth_token:
            # Decode the JWT token
            payload = decode_jwt(auth_token)
            if payload:
                user_id = str(payload.get("user_id"))
                role = payload.get("role")
                
                if user_id and role and user_id not in users_by_id:
                    users_by_id[user_id] = User(
                        id=user_id,
                        role=role,
                        auth_token=auth_token if not auth_token.startswith('Bearer ') else auth_token[7:]
                    )
        
        # Check response headers for session token cookie
        response_headers = response.get("headers", {})
        cookie = response_headers.get("set-cookie", "")
        if "session_token=" in cookie:
            token = cookie.split("session_token=")[1].split(";")[0]
            payload = decode_jwt(token)
            if payload:
                user_id = str(payload.get("user_id"))
                role = payload.get("role")
                if user_id and role and user_id not in users_by_id:
                    users_by_id[user_id] = User(
                        id=user_id,
                        role=role,
                        auth_token=token
                    )
        
        # Check response body for token
        body = response.get("body", "")
        if isinstance(body, str) and body.strip():
            try:
                body_json = json.loads(body)
                if isinstance(body_json, dict):
                    user_id = str(body_json.get("id"))
                    role = body_json.get("role")
                    token = body_json.get("token")
                    
                    if user_id and role and token and user_id not in users_by_id:
                        users_by_id[user_id] = User(
                            id=user_id,
                            role=role,
                            auth_token=token
                        )
            except json.JSONDecodeError:
                pass
    
    return list(users_by_id.values())

def main():
    # File paths
    network_log_file = "../llm/network_log_20250216_020554.json"
    openapi_file = "../lab/openapi.json"
    objects_file = "../oracle/objects.json"
    
    # Extract users from network log
    users = extract_users_from_log(network_log_file)
    
    # Print discovered users
    print("\nDiscovered Users:")
    for user in users:
        print(f"User ID: {user.id}, Role: {user.role}")
    
    # Initialize permission model and oracle
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable must be set")
    
    permission_model = PermissionModel(api_key=api_key)
    permission_model.load_data(
        openapi_path=openapi_file,
        network_log_path=network_log_file,
        objects_path=objects_file
    )
    
    # Generate the permission matrix
    print("\nGenerating permission matrix...")
    permission_model.generate_permission_matrix()
    
    oracle = Oracle(permission_model)
    
    # Run the fuzzer
    print("\nRunning fuzzer...")
    results = fuzz_requests(network_log_file, oracle, users)
    
    # Process results
    vulnerabilities_found = False
    for result in results:
        if result["is_vulnerable"]:
            vulnerabilities_found = True
            print(f"\nVulnerability found in test case: {result['test_case']}")
            print(f"Original Request ID: {result['original_request_id']}")
            print(f"Description: {result['description']}")
            print(f"Explanation: {result['vulnerability_explanation']}")
    
    if not vulnerabilities_found:
        print("\nNo vulnerabilities found.")

if __name__ == "__main__":
    main()
