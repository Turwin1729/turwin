import unittest
import json
import os
from permission_model import PermissionModel

class TestPermissionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create sample test data
        cls.sample_openapi = {
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
                }
            }
        }
        
        cls.sample_network_log = [
            {
                "user": "doctor",
                "method": "GET",
                "path": "/users/1",
                "status_code": 200
            },
            {
                "user": "nurse",
                "method": "GET",
                "path": "/users/1",
                "status_code": 200
            },
            {
                "user": "admin",
                "method": "PUT",
                "path": "/users/1",
                "status_code": 200
            }
        ]
        
        cls.sample_objects = {
            "users": [
                {
                    "id": "1",
                    "type": "user",
                    "attributes": ["id", "name", "role"]
                }
            ]
        }
        
        # Write sample data to files
        with open('test_openapi.json', 'w') as f:
            json.dump(cls.sample_openapi, f)
        
        with open('test_network_log.json', 'w') as f:
            json.dump(cls.sample_network_log, f)
            
        with open('test_objects.json', 'w') as f:
            json.dump(cls.sample_objects, f)

    def setUp(self):
        api_key = "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"
        self.model = PermissionModel(api_key)
        self.model.load_data(
            openapi_path='test_openapi.json',
            network_log_path='test_network_log.json',
            objects_path='test_objects.json'
        )

    def test_data_loading(self):
        """Test if data is loaded correctly"""
        self.assertIsNotNone(self.model.openapi_spec)
        self.assertIsNotNone(self.model.network_log)
        self.assertIsNotNone(self.model.objects)
        
        self.assertEqual(
            self.model.openapi_spec['paths']['/users/{id}']['get']['operationId'],
            'getUser'
        )

    def test_crud_operation_extraction(self):
        """Test if CRUD operations are extracted correctly from OpenAPI spec"""
        operations = self.model._extract_crud_operations()
        self.assertTrue(any(op['operation_id'] == 'getUser' for op in operations))
        self.assertTrue(any(op['operation_id'] == 'updateUser' for op in operations))

    def test_network_traffic_analysis(self):
        """Test if network traffic is analyzed correctly"""
        patterns = self.model._analyze_network_traffic()
        self.assertEqual(len(patterns), 3)
        self.assertTrue(any(
            pattern['user'] == 'doctor' and pattern['method'] == 'GET'
            for pattern in patterns
        ))

    def test_permission_matrix_generation(self):
        """Test if permission matrix is generated correctly"""
        matrix = self.model.generate_permission_matrix()
        
        # Check if matrix is created
        self.assertIsNotNone(matrix)
        
        # Check if matrix has correct columns
        required_columns = {'user', 'object', 'method', 'value'}
        self.assertTrue(all(col in matrix.columns for col in required_columns))
        
        # Check if permissions make sense based on network log
        # Doctor should have read access
        self.assertTrue(
            self.model.check_permission('doctor', 'user[1]', 'GET')
        )
        
        # Admin should have update access
        self.assertTrue(
            self.model.check_permission('admin', 'user[1]', 'PUT')
        )

    def test_permission_matrix_saving(self):
        """Test if permission matrix can be saved correctly"""
        matrix = self.model.generate_permission_matrix()
        test_output = 'test_permission_matrix.csv'
        self.model.save_permission_matrix(test_output)
        
        self.assertTrue(os.path.exists(test_output))
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test files"""
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
