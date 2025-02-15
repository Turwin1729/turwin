from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import jwt

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials

app.config['SECRET_KEY'] = 'vulnerable-secret-key'  # Deliberately weak secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Vulnerable JWT configuration
JWT_SECRET = 'very-weak-secret'  # Deliberately weak secret
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = 24 * 60 * 60  # 24 hours

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    profile_image = db.Column(db.String(200))

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_type = db.Column(db.String(100), nullable=False)
    result = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    image_path = db.Column(db.String(200))

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=False)

def generate_token(user_id, role):
    # Vulnerable token generation - includes sensitive info and uses weak secret
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    try:
        # Vulnerable token validation - no signature verification
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password, data['password']):
        # Generate vulnerable token
        token = generate_token(user.id, user.role)
        
        response = make_response(jsonify({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'profile_image': user.profile_image,
            'token': token  # Sending token in response body (vulnerable)
        }))
        
        # Set vulnerable cookie - no secure flag, no httponly
        response.set_cookie(
            'session_token',
            token,
            max_age=JWT_EXPIRATION,
            samesite='Lax',  # Should be Strict
            path='/'
        )
        
        return response
    
    return jsonify({'error': 'Invalid credentials'}), 401

def get_current_user():
    # Vulnerable token checking - accepts token from multiple sources
    token = None
    
    # Check authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    
    # Check cookies
    if not token:
        token = request.cookies.get('session_token')
    
    # Check query parameters (very vulnerable!)
    if not token:
        token = request.args.get('token')
    
    if not token:
        return None
        
    user_data = decode_token(token)
    if user_data:
        return User.query.get(user_data['user_id'])
    
    return None

@app.route('/api/test-results/<int:patient_id>', methods=['GET'])
def get_test_results(patient_id):
    # Vulnerable - doesn't properly validate role or ownership
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
        
    # Vulnerable IDOR - any authenticated user can access any patient's results
    results = TestResult.query.filter_by(patient_id=patient_id).all()
    return jsonify([{
        'id': result.id,
        'test_type': result.test_type,
        'result': result.result,
        'date': result.date,
        'image_path': result.image_path,
        'doctor_id': result.doctor_id
    } for result in results])

@app.route('/api/test-results', methods=['POST'])
def add_test_result():
    # Vulnerable - doesn't properly validate doctor role
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
        
    # Vulnerable - no validation if the user is actually a doctor
    data = request.get_json()
    test_result = TestResult(
        patient_id=data['patient_id'],
        doctor_id=data['doctor_id'],
        test_type=data['test_type'],
        result=data['result'],
        date=data.get('date', datetime.now().strftime('%Y-%m-%d'))
    )
    
    db.session.add(test_result)
    db.session.commit()
    
    return jsonify({
        'id': test_result.id,
        'test_type': test_result.test_type,
        'result': test_result.result,
        'date': test_result.date
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
        
    user = User(
        username=data['username'],
        password=generate_password_hash(data['password']),
        role=data['role']
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'id': user.id,
            'username': user.username,
            'role': user.role
        })
    except:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/upload-image/<int:user_id>', methods=['POST'])
def upload_image(user_id):
    # Vulnerable to IDOR - no verification of user_id
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        if 'test_result_id' in request.form:
            test_result = TestResult.query.get(request.form['test_result_id'])
            if test_result:
                test_result.image_path = filename
                db.session.commit()
                return jsonify({'path': filename})
            return jsonify({'error': 'Test result not found'}), 404
        else:
            user = User.query.get(user_id)
            if user:
                user.profile_image = filename
                db.session.commit()
                return jsonify({'path': filename})
            return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/patients', methods=['GET'])
def get_patients():
    # Vulnerable to IDOR - no verification if requester is a doctor
    patients = User.query.filter_by(role='patient').all()
    return jsonify([{
        'id': patient.id,
        'username': patient.username,
        'profile_image': patient.profile_image
    } for patient in patients])

@app.route('/api/users/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    # Vulnerable to IDOR - no verification of user_id
    data = request.get_json()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    if 'username' in data:
        user.username = data['username']
    
    try:
        db.session.commit()
        return jsonify({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'profile_image': user.profile_image
        })
    except:
        db.session.rollback()
        return jsonify({'error': 'Update failed'}), 500

@app.route('/uploads/<path:filename>')
def serve_image(filename):
    # Vulnerable to IDOR - no access control on images
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=1730, debug=True)
