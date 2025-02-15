# Turwin Medical Center - Vulnerable Hospital Application

A deliberately vulnerable web application designed to demonstrate common security flaws in healthcare systems. This application is for educational purposes only and should never be used in production.

## Features

- User authentication (with intentional vulnerabilities)
- Role-based access (doctor/patient)
- Medical test results management
- Profile image upload
- JWT token authentication (deliberately vulnerable)

## Security Vulnerabilities

1. Authentication Flaws:
   - Weak JWT implementation
   - Token stored in localStorage (XSS vulnerable)
   - No proper session management
   - Cookies without security flags

2. Access Control Issues:
   - Insecure Direct Object References (IDOR)
   - No proper role validation
   - Unauthorized access to patient records

3. File Upload Vulnerabilities:
   - No file type validation
   - No size restrictions
   - Path traversal possible

## Setup

1. Install backend dependencies:
```bash
pip install -r requirements.txt
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Start the backend server (default port: 1730):
```bash
python app.py
```

4. Start the frontend development server (default port: 3001):
```bash
cd frontend
npm start
```

## Database Management

### Complete Reset
To completely reset the database to a clean state:
```bash
# Remove the existing database and create a fresh one
rm -f hospital.db && python3 -c '
from app import db
db.create_all()
'
```

### State Management
The application includes a state management system that allows you to save and load different database states. This is particularly useful for:
- Saving progress before testing exploits
- Creating different scenarios for vulnerability testing
- Quickly restoring to a known good state
- Sharing specific configurations

### Managing States

Use the `manage_state.sh` script to manage database states:

```bash
# Save current state
./manage_state.sh save <state_name> -d "description"

# Load a saved state
./manage_state.sh load <state_name>

# List all saved states
./manage_state.sh list

# Delete a state
./manage_state.sh delete <state_name>
```

### Preconfigured States

1. Clean Installation
```bash
./manage_state.sh load clean_install
```
- Fresh database with no users
- Perfect for testing user registration

2. Test Users Configuration
```bash
./manage_state.sh load test_users
```
- Preconfigured with:
  - Doctor account (dr_smith / doctor123)
  - Patient accounts:
    - John Doe (john_doe / patient123)
    - Jane Smith (jane_smith / patient456)
  - Sample medical test results

## Test Accounts

### Doctor Account
- Username: dr_smith
- Password: doctor123
- Capabilities:
  - View all patients
  - Add test results
  - Upload images

### Patient Accounts
1. John Doe
   - Username: john_doe
   - Password: patient123

2. Jane Smith
   - Username: jane_smith
   - Password: patient456

## API Documentation

API documentation is available in OpenAPI format at `openapi.json`. The documentation includes:
- All available endpoints
- Request/response formats
- Authentication methods
- Known vulnerabilities

## Security Notice

 **WARNING**: This application contains intentional security vulnerabilities for educational purposes. DO NOT:
- Deploy this application in production
- Use any of the code in production applications
- Use real personal or medical data
- Host this application on a public network

## License

This project is for educational purposes only. Use at your own risk.
