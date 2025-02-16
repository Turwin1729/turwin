from oracle import AccessControlOracle, Request, Response

def test_oracle():
    # Example permission model
    permission_model = [
        ("alice", "users[1]", "read", True),
        ("bob", "users[1]", "read", False),
        ("alice", "users[1]", "update", True),
        ("bob", "users[1]", "update", False),
    ]

    # Example object table
    object_table = {
        "users[1]": {
            "id": 1,
            "username": "alice",
            "role": "admin",
            "profile_image": "alice.jpg"
        }
    }

    # Example object schema
    object_schema = {
        "users": {
            "id": "integer",
            "username": "string",
            "role": "string",
            "profile_image": "string"
        }
    }

    # Example operations
    operations = {
        "get_/api/users/1": {
            "path": "/api/users/1",
            "method": "get",
            "schema": {
                "id": "integer",
                "username": "string",
                "role": "string",
                "profile_image": "string"
            }
        }
    }

    # Create oracle
    oracle = AccessControlOracle(
        permission_model=permission_model,
        object_table=object_table,
        object_schema=object_schema,
        operations=operations
    )

    # Test case 1: Unauthorized access that succeeds (vulnerability)
    unauthorized_request = Request(
        method="GET",
        path="/api/users/1",
        body={},
        headers={},
        user="bob"
    )
    successful_response = Response(
        status_code=200,
        body={"id": 1, "username": "alice"},
        headers={}
    )
    
    is_vulnerable, reason = oracle.is_vulnerable(unauthorized_request, successful_response)
    print(f"Test 1 - Unauthorized access:")
    print(f"Vulnerable: {is_vulnerable}")
    print(f"Reason: {reason}")
    print()

    # Test case 2: Authorized access that succeeds (not a vulnerability)
    authorized_request = Request(
        method="GET",
        path="/api/users/1",
        body={},
        headers={},
        user="alice"
    )
    
    is_vulnerable, reason = oracle.is_vulnerable(authorized_request, successful_response)
    print(f"Test 2 - Authorized access:")
    print(f"Vulnerable: {is_vulnerable}")
    print(f"Reason: {reason}")

if __name__ == "__main__":
    test_oracle()
