from typing import Dict, List, Tuple, Any
import json
from dataclasses import dataclass
from enum import Enum

class Operation(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

@dataclass
class Request:
    method: str
    path: str
    body: Dict[str, Any]
    headers: Dict[str, str]
    user: str  # The user making the request

@dataclass
class Response:
    status_code: int
    body: Dict[str, Any]
    headers: Dict[str, str]

class AccessControlOracle:
    def __init__(
        self,
        permission_model: List[Tuple[str, str, str, bool]],  # List of (user, object, method, allowed)
        object_table: Dict[str, Dict[str, Any]],  # Map of object IDs to their data
        object_schema: Dict[str, Dict[str, str]],  # Schema definitions for object types
        operations: Dict[str, Dict[str, Any]]  # API endpoint definitions
    ):
        self.permission_model = permission_model
        self.object_table = object_table
        self.object_schema = object_schema
        self.operations = operations

    def _get_operation_type(self, method: str) -> Operation:
        """Map HTTP method to CRUD operation"""
        method = method.lower()
        if method == "post":
            return Operation.CREATE
        elif method == "get":
            return Operation.READ
        elif method in ["put", "patch"]:
            return Operation.UPDATE
        elif method == "delete":
            return Operation.DELETE
        raise ValueError(f"Unsupported HTTP method: {method}")

    def _extract_object_id(self, path: str) -> str:
        """Extract object ID from path parameters"""
        # Example: /api/users/123 -> users[123]
        parts = path.split("/")
        if len(parts) >= 3:
            resource = parts[2]
            if len(parts) >= 4:
                return f"{resource}[{parts[3]}]"
        return None

    def _check_permission(self, user: str, object_id: str, operation: Operation) -> bool:
        """Check if user has permission for operation on object"""
        for u, obj, op, allowed in self.permission_model:
            if u == user and obj == object_id and op == operation.value:
                return allowed
        return False  # Default deny

    def is_vulnerable(self, request: Request, response: Response) -> Tuple[bool, str]:
        """
        Determine if a request-response pair represents a vulnerability.
        Returns (is_vulnerable: bool, reason: str)
        """
        # Extract operation type and target object
        operation = self._get_operation_type(request.method)
        object_id = self._extract_object_id(request.path)

        # If we can't identify the object, we can't make a determination
        if not object_id:
            return False, "Unable to identify target object"

        # Check if user has permission
        has_permission = self._check_permission(request.user, object_id, operation)

        # Analyze response to determine if access was granted
        access_granted = 200 <= response.status_code < 300

        # Detect vulnerabilities
        if not has_permission and access_granted:
            return True, f"User {request.user} accessed {object_id} without permission"
        
        if has_permission and not access_granted:
            return True, f"User {request.user} denied access to {object_id} despite having permission"

        return False, "No vulnerability detected"

    def validate_request_schema(self, request: Request) -> Tuple[bool, str]:
        """
        Validate that a request conforms to the defined schema
        Returns (is_valid: bool, error_message: str)
        """
        endpoint_key = f"{request.method.lower()}_{request.path}"
        if endpoint_key not in self.operations:
            return False, f"Unknown endpoint: {endpoint_key}"

        endpoint_schema = self.operations[endpoint_key]["schema"]
        
        # Validate request body against schema
        for field, field_type in endpoint_schema.items():
            if field in request.body:
                value = request.body[field]
                if field_type == "string" and not isinstance(value, str):
                    return False, f"Field {field} should be string, got {type(value)}"
                elif field_type == "integer" and not isinstance(value, int):
                    return False, f"Field {field} should be integer, got {type(value)}"

        return True, "Request schema is valid"
