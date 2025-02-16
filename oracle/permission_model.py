import json
import pandas as pd
from openai import OpenAI
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PermissionModel:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.permissions_df = None

    def load_data(self, openapi_path: str, network_log_path: str, objects_path: str) -> None:
        """Load all required data sources."""
        try:
            with open(openapi_path, 'r') as f:
                self.openapi_spec = json.load(f)
            
            with open(network_log_path, 'r') as f:
                self.network_log = json.load(f)
            
            with open(objects_path, 'r') as f:
                self.objects = json.load(f)
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def _extract_crud_operations(self) -> List[Dict[str, Any]]:
        """Extract CRUD operations from OpenAPI spec."""
        operations = []
        
        for path, methods in self.openapi_spec.get('paths', {}).items():
            for method, details in methods.items():
                operation = {
                    'path': path,
                    'method': method.upper(),
                    'operation_id': details.get('operationId'),
                    'summary': details.get('summary'),
                    'description': details.get('description')
                }
                operations.append(operation)
        
        return operations

    def _analyze_network_traffic(self) -> List[Dict[str, Any]]:
        """Analyze network traffic to understand access patterns."""
        access_patterns = []
        
        for entry in self.network_log:
            pattern = {
                'user': entry.get('user'),
                'method': entry.get('method'),
                'path': entry.get('path'),
                'status_code': entry.get('status_code')
            }
            access_patterns.append(pattern)
        
        return access_patterns

    def generate_permission_matrix(self) -> pd.DataFrame:
        """Generate permission matrix using OpenAI."""
        crud_operations = self._extract_crud_operations()
        access_patterns = self._analyze_network_traffic()
        
        # Prepare context for OpenAI
        context = {
            'operations': crud_operations,
            'access_patterns': access_patterns,
            'objects': self.objects
        }
        
        prompt = f"""Based on the following application context, generate a permission matrix.
You must respond with ONLY a JSON array of permission objects, with no additional text.
Each permission object must have these exact fields: "user", "object", "method", "value"

Context:
OpenAPI Operations:
{json.dumps(crud_operations, indent=2)}

Access Patterns:
{json.dumps(access_patterns, indent=2)}

Objects:
{json.dumps(self.objects, indent=2)}

Example response format:
[
    {{"user": "john", "object": "user[1]", "method": "GET", "value": true}},
    {{"user": "alice", "object": "user[1]", "method": "PUT", "value": false}}
]"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a security expert helping to generate a permission matrix."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            # Parse the response and convert to DataFrame
            permissions = json.loads(response.choices[0].message.content)
            self.permissions_df = pd.DataFrame(permissions)
            return self.permissions_df
            
        except Exception as e:
            logger.error(f"Error generating permission matrix: {str(e)}")
            raise

    def save_permission_matrix(self, output_path: str) -> None:
        """Save the permission matrix to a CSV file."""
        if self.permissions_df is not None:
            self.permissions_df.to_csv(output_path, index=False)
            logger.info(f"Permission matrix saved to {output_path}")
        else:
            raise ValueError("Permission matrix has not been generated yet")

    def check_permission(self, user: str, object_id: str, method: str) -> bool:
        """Check if a user has permission to perform an operation on an object."""
        if self.permissions_df is None:
            raise ValueError("Permission matrix has not been generated yet")
            
        mask = (
            (self.permissions_df['user'] == user) &
            (self.permissions_df['object'] == object_id) &
            (self.permissions_df['method'] == method)
        )
        
        matching_permissions = self.permissions_df[mask]
        
        if matching_permissions.empty:
            return False
            
        return matching_permissions.iloc[0]['value']

def main():
    # Initialize the permission model
    api_key = "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"
    model = PermissionModel(api_key)
    
    # Load required data
    model.load_data(
        openapi_path='openapi.json',
        network_log_path='network_log.json',
        objects_path='objects.json'
    )
    
    # Generate and save permission matrix
    permission_matrix = model.generate_permission_matrix()
    model.save_permission_matrix('permission_matrix.csv')
    
    logger.info("Permission matrix generated successfully")
    
if __name__ == "__main__":
    main()
