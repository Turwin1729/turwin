import json
import copy
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from oracle.oracle import Oracle
from urllib.parse import urlparse

@dataclass
class User:
    id: str
    role: str
    auth_token: str

class AuthFuzzer:
    def __init__(self, oracle: Oracle, users: List[User]):
        """
        Initialize the authentication fuzzer.
        
        Args:
            oracle: Oracle instance for checking vulnerabilities
            users: List of User objects with their auth tokens
        """
        self.oracle = oracle
        self.users = users
        self.users_by_role = self._group_users_by_role()
        
    def _group_users_by_role(self) -> Dict[str, List[User]]:
        """Group users by their roles for easier access."""
        groups = {}
        for user in self.users:
            if user.role not in groups:
                groups[user.role] = []
            groups[user.role].append(user)
        return groups
    
    def _get_different_role_user(self, current_role: str) -> Optional[User]:
        """Get a user with a different role than the current one."""
        for role, users in self.users_by_role.items():
            if role != current_role and users:
                return users[0]
        return None
    
    def _get_same_role_user(self, current_user: User) -> Optional[User]:
        """Get a different user with the same role."""
        same_role_users = self.users_by_role[current_user.role]
        for user in same_role_users:
            if user.id != current_user.id:
                return user
        return None
    
    def _extract_auth_info(self, request: Dict) -> Optional[User]:
        """Extract user and role information from request headers."""
        auth_token = request.get("headers", {}).get("authorization")
        if not auth_token:
            return None
            
        # Remove 'Bearer ' prefix if present for comparison
        if auth_token.startswith('Bearer '):
            auth_token = auth_token[7:]
            
        # Find user with this auth token
        for user in self.users:
            # Compare without 'Bearer ' prefix
            if user.auth_token == auth_token:
                return user
        return None
    
    def _create_request_variant(self, original_request: Dict, auth_token: Optional[str] = None) -> Dict:
        """Create a variant of the request with modified authentication."""
        request = copy.deepcopy(original_request)
        if auth_token:
            # Add Bearer prefix if not present
            if not auth_token.startswith('Bearer '):
                auth_token = f'Bearer {auth_token}'
            request["headers"]["authorization"] = auth_token
        else:
            request["headers"].pop("authorization", None)
            
        # Extract path from URL and add it to request
        parsed_url = urlparse(request["url"])
        request["path"] = parsed_url.path
            
        return request
    
    def _send_request(self, request: Dict) -> Dict:
        """Send HTTP request and return response."""
        method = request["method"].lower()
        url = request["url"]
        headers = request["headers"]
        data = request.get("body")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None
            )
            
            return {
                "status": response.status_code,
                "body": response.json() if response.text else None,
                "headers": dict(response.headers)
            }
        except Exception as e:
            print(f"Error sending request: {e}")
            return {
                "status": 500,
                "body": {"error": str(e)},
                "headers": {}
            }
    
    def fuzz_request(self, request: Dict) -> List[Dict]:
        """
        Generate and test authentication variants for a request.
        
        Returns:
            List of dicts containing:
            - original_request: The request that was sent
            - response: The response received
            - is_vulnerable: Whether the oracle found a vulnerability
            - description: Description of the vulnerability if found
        """
        results = []
        current_user = self._extract_auth_info(request)
        
        if not current_user:
            print("Skipping request - no authentication token found")
            return results
            
        # Test cases to try
        test_cases = [
            # No authentication
            {
                "name": "no_auth",
                "auth_token": None,
                "description": "Request with no authentication"
            },
            
            # Same role, different user
            {
                "name": "same_role",
                "auth_token": self._get_same_role_user(current_user).auth_token if self._get_same_role_user(current_user) else None,
                "description": "Request with different user, same role"
            },
            
            # Different role
            {
                "name": "different_role",
                "auth_token": self._get_different_role_user(current_user.role).auth_token if self._get_different_role_user(current_user.role) else None,
                "description": "Request with user of different role"
            }
        ]
        
        # Run each test case
        for test in test_cases:
            if test["auth_token"] is not None or test["name"] == "no_auth":
                variant_request = self._create_request_variant(request, test["auth_token"])
                response = self._send_request(variant_request)
                
                # Check for vulnerability
                is_vulnerable = self.oracle.check_violation(variant_request, response)
                explanation = self.oracle.explain_violation(variant_request, response) if is_vulnerable else None
                
                results.append({
                    "test_case": test["name"],
                    "description": test["description"],
                    "original_request": variant_request,
                    "response": response,
                    "is_vulnerable": is_vulnerable,
                    "vulnerability_explanation": explanation
                })
        
        return results

def fuzz_requests(network_log_file: str, oracle: Oracle, users: List[User]) -> List[Dict]:
    """
    Fuzz a corpus of requests for authentication vulnerabilities.
    
    Args:
        network_log_file: Path to JSON file containing network log with requests
        oracle: Oracle instance for vulnerability checking
        users: List of users with their auth tokens
        
    Returns:
        List of vulnerability reports
    """
    # Load network log
    with open(network_log_file, 'r') as f:
        network_log = json.load(f)
    
    fuzzer = AuthFuzzer(oracle, users)
    all_results = []
    
    # Process each request in the network log
    for entry in network_log.get("requests", []):
        if "request" in entry:
            # Add request ID and timestamp to the request object
            request = entry["request"]
            request["id"] = entry["id"]
            request["timestamp"] = entry["timestamp"]
            
            # Fuzz the request
            results = fuzzer.fuzz_request(request)
            
            # Add original request metadata to results
            for result in results:
                result["original_request_id"] = entry["id"]
                result["original_timestamp"] = entry["timestamp"]
            
            all_results.extend(results)
    
    return all_results
