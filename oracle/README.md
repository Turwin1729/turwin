# Access Control Oracle

An LLM-based security testing oracle for detecting access control vulnerabilities in web applications. This tool generates and enforces permission models by analyzing OpenAPI specifications, network traffic, and application objects.

## Features

- **Permission Model Generation**: Uses OpenAI's GPT models to generate comprehensive permission matrices
- **Intelligent Path Matching**: Maps API requests to OpenAPI templates
- **User Context Extraction**: Extracts user information from various sources (headers, cookies, body)
- **Violation Detection**: Identifies unauthorized access attempts
- **Detailed Explanations**: Provides human-readable explanations of detected violations

## Prerequisites

- Python 3.8+
- OpenAI API key
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd oracle
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```python
api_key = "your-openai-api-key"
```

## Usage

### 1. Initialize Permission Model

```python
from permission_model import PermissionModel
from oracle import Oracle

# Initialize and train permission model
model = PermissionModel(api_key="your-openai-api-key")
model.load_data(
    openapi_path='openapi.json',
    network_log_path='network_log.json',
    objects_path='objects.json'
)
model.generate_permission_matrix()

# Create oracle
oracle = Oracle(model)
```

### 2. Check for Violations

```python
# Example request-response pair
request = {
    'method': 'GET',
    'path': '/patients/123/records',
    'headers': {
        'Authorization': 'Bearer doctor-token'
    }
}

response = {
    'status': 200,
    'body': {'records': []}
}

# Check for violation
violation = oracle.check_violation(request, response)
if violation:
    explanation = oracle.explain_violation(request, response)
    print(f"Violation detected: {explanation}")
```

## Input Files

### 1. OpenAPI Specification (openapi.json)
```json
{
    "paths": {
        "/users/{id}": {
            "get": {
                "operationId": "getUser",
                "summary": "Get user details"
            }
        }
    }
}
```

### 2. Network Traffic Log (network_log.json)
```json
[
    {
        "user": "doctor",
        "method": "GET",
        "path": "/patients/1/records",
        "status_code": 200
    }
]
```

### 3. Objects Definition (objects.json)
```json
{
    "users": [
        {
            "id": "1",
            "type": "user",
            "attributes": ["id", "name", "role"]
        }
    ]
}
```

## Components

### Permission Model (`permission_model.py`)
- Generates permission matrices using OpenAI
- Maps users, objects, and CRUD operations
- Provides permission checking functionality

### Oracle (`oracle.py`)
- Matches requests to OpenAPI templates
- Extracts object IDs and user information
- Detects permission violations
- Generates violation explanations

## Testing

Run the test suite:
```bash
python -m unittest test_permission_model.py -v
python -m unittest test_oracle.py -v
```

The test suite covers:
- Permission model generation
- Path template matching
- Object ID extraction
- User information extraction
- Violation detection
- Explanation generation

## How It Works

1. **Permission Model Generation**
   - Analyzes OpenAPI spec to understand available operations
   - Studies network traffic to learn access patterns
   - Uses LLM to generate comprehensive permission matrix

2. **Violation Detection**
   - Maps incoming requests to OpenAPI templates
   - Extracts object IDs and user information
   - Checks if successful operations are allowed
   - Flags unauthorized access attempts

3. **User Identification**
   Extracts user context from:
   - Authorization headers
   - Cookies
   - Request body

## Limitations

- Requires accurate OpenAPI specification
- Depends on representative network traffic logs
- May need manual refinement of permission matrices
- OpenAI API key required

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your chosen license]

## Contact

[Your contact information]
