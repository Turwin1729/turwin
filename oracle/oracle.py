import json
import logging
from typing import Dict, Any, Optional
from permission_model import PermissionModel
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Oracle:
    def __init__(self, permission_model: PermissionModel):
        """Initialize the Oracle with a permission model."""
        self.permission_model = permission_model
        self.openapi_spec = permission_model.openapi_spec
        self._path_templates = self._extract_path_templates()

    def _extract_path_templates(self) -> Dict[str, str]:
        """Extract path templates from OpenAPI spec and map them to their patterns."""
        templates = {}
        for path in self.openapi_spec.get('paths', {}):
            # Convert OpenAPI path template to regex pattern
            # e.g., /users/{id} -> /users/[^/]+
            template = path.replace('{', '[^/]+').replace('}', '')
            templates[template] = path
        return templates

    def _match_path_to_template(self, request_path: str) -> Optional[str]:
        """Match a request path to its OpenAPI template."""
        parsed = urlparse(request_path)
        path = parsed.path
        
        # Try direct match first
        if path in self._path_templates:
            return path
            
        # Try pattern matching
        for template_pattern, original_template in self._path_templates.items():
            if path.startswith(template_pattern.split('[')[0]):
                return original_template
                
        return None

    def _extract_object_id(self, template: str, actual_path: str) -> Optional[str]:
        """Extract object ID from the actual path based on the template."""
        template_parts = template.split('/')
        path_parts = actual_path.split('/')
        
        if len(template_parts) != len(path_parts):
            return None
            
        # Find the part with {id} or similar in template
        for i, (template_part, path_part) in enumerate(zip(template_parts, path_parts)):
            if template_part.startswith('{') and template_part.endswith('}'):
                # Extract the type from the path template
                obj_type = template_parts[i-1] if i > 0 else 'unknown'
                return f"{obj_type}[{path_part}]"
                
        return None

    def _extract_user(self, request: Dict[str, Any]) -> Optional[str]:
        """Extract user information from request headers or body."""
        # Try Authorization header
        auth_header = request.get('headers', {}).get('Authorization')
        if auth_header:
            if auth_header.startswith('Bearer '):
                # You might want to decode JWT token here
                return auth_header[7:]  # Remove 'Bearer ' prefix
                
        # Try user information in cookies
        cookies = request.get('headers', {}).get('Cookie', '')
        if 'user=' in cookies:
            return cookies.split('user=')[1].split(';')[0]
            
        # Try user information in request body
        body = request.get('body', {})
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                pass
                
        if isinstance(body, dict):
            return body.get('user') or body.get('username') or body.get('user_id')
            
        return None

    def check_violation(self, request: Dict[str, Any], response: Dict[str, Any]) -> bool:
        """
        Check if a request-response pair violates the permission model.
        
        Args:
            request: Dictionary containing request details (method, path, headers, body)
            response: Dictionary containing response details (status, body)
            
        Returns:
            bool: True if permission model is violated, False otherwise
        """
        try:
            # Extract request information
            method = request.get('method', '').upper()
            path = request.get('path', '')
            
            # Match path to OpenAPI template
            template = self._match_path_to_template(path)
            if not template:
                logger.warning(f"Path {path} not found in OpenAPI specification")
                return False  # Can't determine violation without matching template
                
            # Extract object ID from path
            object_id = self._extract_object_id(template, path)
            if not object_id:
                logger.warning(f"Could not extract object ID from path {path}")
                return False
                
            # Extract user information
            user = self._extract_user(request)
            if not user:
                logger.warning("Could not extract user information from request")
                return False
                
            # Check if operation was successful
            status_code = response.get('status', 0)
            if 200 <= status_code < 300:  # Successful response
                # Check permission model
                allowed = self.permission_model.check_permission(
                    user=user,
                    object_id=object_id,
                    method=method
                )
                
                # If operation succeeded but permission model denies it,
                # we have a violation
                return not allowed
                
            return False  # No violation if operation failed
            
        except Exception as e:
            logger.error(f"Error checking violation: {str(e)}")
            return False  # Err on the side of caution
            
    def explain_violation(self, request: Dict[str, Any], response: Dict[str, Any]) -> str:
        """
        Provide a detailed explanation of why a request-response pair violates the permission model.
        
        Args:
            request: Dictionary containing request details
            response: Dictionary containing response details
            
        Returns:
            str: Explanation of the violation or why it's not a violation
        """
        method = request.get('method', '').upper()
        path = request.get('path', '')
        template = self._match_path_to_template(path)
        object_id = self._extract_object_id(template, path) if template else None
        user = self._extract_user(request)
        status_code = response.get('status', 0)
        
        if not template:
            return f"Path {path} not found in OpenAPI specification"
            
        if not object_id:
            return f"Could not extract object ID from path {path}"
            
        if not user:
            return "Could not extract user information from request"
            
        if 200 <= status_code < 300:
            allowed = self.permission_model.check_permission(
                user=user,
                object_id=object_id,
                method=method
            )
            
            if not allowed:
                return f"User '{user}' is not allowed to perform '{method}' operation on '{object_id}'"
            else:
                return f"Operation is allowed: User '{user}' can perform '{method}' on '{object_id}'"
        
        return f"No violation: Operation failed with status code {status_code}"
