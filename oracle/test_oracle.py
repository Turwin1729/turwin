import unittest
import json
from oracle import Oracle
from permission_model import PermissionModel

class TestOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create sample OpenAPI spec
        cls.openapi_spec = {
            "paths": {
                "/users/{id}": {
                    "get": {
                        "operationId": "getUser",
                        "summary": "Get user details"
                    },
                    "put": {
                        "operationId": "updateUser",
                        "summary": "Update user details"
                    }
                },
                "/patients/{id}/records": {
                    "get": {
                        "operationId": "getPatientRecords",
                        "summary": "Get patient records"
                    }
                }
            }
        }
        
        with open('test_openapi.json', 'w') as f:
            json.dump(cls.openapi_spec, f)
            
        # Create sample network log
        cls.network_log = [
            {
                "user": "doctor",
                "method": "GET",
                "path": "/patients/1/records",
                "status_code": 200
            }
        ]
        
        with open('test_network_log.json', 'w') as f:
            json.dump(cls.network_log, f)
            
        # Create sample objects
        cls.objects = {
            "users": [{"id": "1", "type": "user"}],
            "patients": [{"id": "1", "type": "patient"}]
        }
        
        with open('test_objects.json', 'w') as f:
            json.dump(cls.objects, f)

    def setUp(self):
        # Initialize permission model and oracle
        api_key = "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"
        self.permission_model = PermissionModel(api_key)
        self.permission_model.load_data(
            openapi_path='test_openapi.json',
            network_log_path='test_network_log.json',
            objects_path='test_objects.json'
        )
        self.permission_model.generate_permission_matrix()
        self.oracle = Oracle(self.permission_model)

    def test_path_matching(self):
        """Test if paths are correctly matched to templates"""
        template = self.oracle._match_path_to_template('/users/123')
        self.assertEqual(template, '/users/{id}')
        
        template = self.oracle._match_path_to_template('/patients/456/records')
        self.assertEqual(template, '/patients/{id}/records')

    def test_object_id_extraction(self):
        """Test if object IDs are correctly extracted"""
        object_id = self.oracle._extract_object_id('/users/{id}', '/users/123')
        self.assertEqual(object_id, 'users[123]')
        
        object_id = self.oracle._extract_object_id('/patients/{id}/records', '/patients/456/records')
        self.assertEqual(object_id, 'patients[456]')

    def test_user_extraction(self):
        """Test if user information is correctly extracted"""
        # Test Bearer token
        request = {
            'headers': {
                'Authorization': 'Bearer user123'
            }
        }
        user = self.oracle._extract_user(request)
        self.assertEqual(user, 'user123')
        
        # Test cookie
        request = {
            'headers': {
                'Cookie': 'user=john.doe; session=abc123'
            }
        }
        user = self.oracle._extract_user(request)
        self.assertEqual(user, 'john.doe')
        
        # Test request body
        request = {
            'body': json.dumps({
                'user': 'jane.doe'
            })
        }
        user = self.oracle._extract_user(request)
        self.assertEqual(user, 'jane.doe')

    def test_violation_check(self):
        """Test if violations are correctly identified"""
        # Mock the permission model's check_permission method
        def mock_check_permission(user, object_id, method):
            if user == 'doctor' and object_id == 'patients[1]' and method == 'GET':
                return True
            return False
            
        self.permission_model.check_permission = mock_check_permission
        
        # Test allowed operation
        request = {
            'method': 'GET',
            'path': '/patients/1/records',
            'headers': {
                'Authorization': 'Bearer doctor'
            }
        }
        response = {
            'status': 200,
            'body': {'records': []}
        }
        
        violation = self.oracle.check_violation(request, response)
        self.assertFalse(violation)
        
        # Test disallowed operation
        request = {
            'method': 'GET',
            'path': '/patients/1/records',
            'headers': {
                'Authorization': 'Bearer unauthorized_user'
            }
        }
        response = {
            'status': 200,
            'body': {'records': []}
        }
        
        violation = self.oracle.check_violation(request, response)
        self.assertTrue(violation)

    def test_violation_explanation(self):
        """Test if violation explanations are helpful"""
        request = {
            'method': 'GET',
            'path': '/patients/1/records',
            'headers': {
                'Authorization': 'Bearer unauthorized_user'
            }
        }
        response = {
            'status': 200,
            'body': {'records': []}
        }
        
        explanation = self.oracle.explain_violation(request, response)
        self.assertIn('not allowed', explanation.lower())
        self.assertIn('unauthorized_user', explanation)
        self.assertIn('GET', explanation)
        self.assertIn('patients[1]', explanation)

    @classmethod
    def tearDownClass(cls):
        """Clean up test files"""
        import os
        test_files = [
            'test_openapi.json',
            'test_network_log.json',
            'test_objects.json',
            'test_permission_matrix.csv'
        ]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)

if __name__ == '__main__':
    unittest.main()
