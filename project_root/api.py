# api.py - Add/update these endpoints

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from models import User, Student, Test, ProctorSession, Screenshot, RiskFlag
from database import db
from datetime import datetime
import base64
import os
from utils import decrypt_test_data

api_bp = Blueprint('api', __name__)

# Secret key for decryption - Store securely in environment variables
ENCRYPTION_SECRET = os.environ.get("ENCRYPTION_SECRET", "change-this-in-production")

@api_bp.route('/validate-code', methods=['POST'])
def validate_code():
    """Validate test access code and return test details if valid"""
    data = request.get_json()
    
    # Check if using encrypted code or plain access code
    if 'encrypted_code' in data:
        try:
            # Decrypt the encrypted code
            test_data = decrypt_test_data(data['encrypted_code'], ENCRYPTION_SECRET)
            
            # Validate test exists and times
            test = Test.query.get(test_data['test_id'])
            if not test:
                return jsonify({'valid': False, 'message': 'Invalid test code.'}), 404
                
            # Verify the decrypted access code matches the database
            if test.access_code != test_data['code']:
                return jsonify({'valid': False, 'message': 'Access code mismatch.'}), 401
            
            # Check if test is active
            if not test.is_active:
                return jsonify({'valid': False, 'message': 'This test is not active.'}), 403
                
            # Check if current time is within test time window
            now = datetime.utcnow()
            if now < test_data['start'] or now > test_data['end']:
                return jsonify({
                    'valid': False, 
                    'message': 'Test is not currently active.',
                    'start_time': test_data['start'].isoformat(),
                    'end_time': test_data['end'].isoformat(),
                    'current_time': now.isoformat()
                }), 403
                
            # Return test details including whitelisted processes
            return jsonify({
                'valid': True,
                'test_id': test.id,
                'title': test.title,
                'whitelisted_processes': test_data['processes'],
                'start_time': test_data['start'].isoformat(),
                'end_time': test_data['end'].isoformat()
            })
            
        except Exception as e:
            current_app.logger.error(f"Error decrypting code: {str(e)}")
            return jsonify({'valid': False, 'message': 'Invalid encrypted code.'}), 400
    
    # Fallback to traditional access code validation
    elif 'access_code' in data:
        access_code = data.get('access_code')
        test = Test.query.filter_by(access_code=access_code).first()
        
        if not test:
            return jsonify({'valid': False, 'message': 'Invalid access code.'}), 404
            
        # Check if test is active
        if not test.is_active:
            return jsonify({'valid': False, 'message': 'This test is not active.'}), 403
            
        # Check if current time is within test time window
        now = datetime.utcnow()
        if now < test.start_time or now > test.end_time:
            return jsonify({
                'valid': False, 
                'message': 'Test is not currently active.',
                'start_time': test.start_time.isoformat(),
                'end_time': test.end_time.isoformat(),
                'current_time': now.isoformat()
            }), 403
            
        # Return test details
        return jsonify({
            'valid': True,
            'test_id': test.id,
            'title': test.title,
            'whitelisted_processes': test.get_whitelisted_processes(),
            'start_time': test.start_time.isoformat(),
            'end_time': test.end_time.isoformat()
        })
    
    else:
        return jsonify({'valid': False, 'message': 'No code provided.'}), 400

@api_bp.route('/start-session', methods=['POST'])
def start_session():
    """Start a new proctoring session"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['test_id', 'student_id', 'enrollment_number', 'full_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    # Check if test exists
    test = Test.query.get(data['test_id'])
    if not test:
        return jsonify({'success': False, 'message': 'Test not found.'}), 404
    
    # Check if student exists by student_id or enrollment number
    student = None
    
    # Try to find by numeric ID
    try:
        student_id = int(data['student_id'])
        student = Student.query.get(student_id)
    except (ValueError, TypeError):
        pass
    
    # If not found, try to find by enrollment number
    if not student:
        # Check if student exists in our system by enrollment number
        user = User.query.filter_by(username=data['enrollment_number']).first()
        if user and user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
    
    # If still not found, create a temporary student record
    if not student:
        # Create a new user
        new_user = User(
            username=data['enrollment_number'],
            email=f"{data['enrollment_number']}@temp.edu",  # Temporary email
            role='student'
        )
        new_user.set_password(secrets.token_hex(8))  # Random password
        db.session.add(new_user)
        db.session.flush()  # Get the user ID without committing
        
        # Create a new student
        student = Student(
            user_id=new_user.id,
            student_id=data['enrollment_number']
        )
        db.session.add(student)
        db.session.flush()
    
    # Create new session
    new_session = ProctorSession(
        student_id=student.id,
        test_id=test.id,
        start_time=datetime.utcnow(),
        session_status='active'
    )
    
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'session_id': new_session.id,
        'message': 'Session started successfully.'
    })

@api_bp.route('/submit-screenshot', methods=['POST'])
def submit_screenshot():
    """Submit a screenshot for a proctoring session"""
    # Check if form data or JSON
    if request.content_type.startswith('application/json'):
        data = request.get_json()
        session_id = data.get('session_id')
        image_data_base64 = data.get('image_data')
        risk_score = data.get('risk_score', 0.0)
        
        if not session_id or not image_data_base64:
            return jsonify({'success': False, 'message': 'Missing required fields.'}), 400
            
        # Decode base64 image
        try:
            image_data = base64.b64decode(image_data_base64)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Invalid image data: {str(e)}'}), 400
    else:
        # Handle multipart/form-data
        session_id = request.form.get('session_id')
        risk_score = float(request.form.get('risk_score', 0.0))
        
        if not session_id or 'image' not in request.files:
            return jsonify({'success': False, 'message': 'Missing required fields.'}), 400
            
        image_file = request.files['image']
        image_data = image_file.read()
    
    # Check if session exists
    session = ProctorSession.query.get(session_id)
    if not session:
        return jsonify({'success': False, 'message': 'Session not found.'}), 404
        
    # Check if session is active
    if session.session_status != 'active':
        return jsonify({'success': False, 'message': 'Session is not active.'}), 403
    
    # Create screenshot record
    new_screenshot = Screenshot(
        session_id=session_id,
        timestamp=datetime.utcnow(),
        image_data=image_data,
        risk_score=risk_score
    )
    
    db.session.add(new_screenshot)
    
    # Update session risk score if needed
    if risk_score > 0:
        # Simple average calculation
        existing_screenshots = Screenshot.query.filter_by(session_id=session_id).count()
        if existing_screenshots > 0:
            new_total = (session.total_risk_score * existing_screenshots + risk_score) / (existing_screenshots + 1)
            session.total_risk_score = new_total
        else:
            session.total_risk_score = risk_score
        
        # Flag session if risk is high
        if risk_score > 0.7 and session.session_status != 'flagged':
            session.session_status = 'flagged'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'screenshot_id': new_screenshot.id,
        'message': 'Screenshot submitted successfully.'
    })

@api_bp.route('/submit-risk-flag', methods=['POST'])
def submit_risk_flag():
    """Submit a risk flag for a proctoring session"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['session_id', 'flag_type', 'severity']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    session_id = data['session_id']
    flag_type = data['flag_type']
    severity = float(data['severity'])
    description = data.get('description', '')
    
    # Check if session exists
    session = ProctorSession.query.get(session_id)
    if not session:
        return jsonify({'success': False, 'message': 'Session not found.'}), 404
        
    # Check if session is active
    if session.session_status != 'active' and session.session_status != 'flagged':
        return jsonify({'success': False, 'message': 'Session is not active.'}), 403
    
    # Create risk flag record
    new_flag = RiskFlag(
        session_id=session_id,
        flag_type=flag_type,
        severity=severity,
        timestamp=datetime.utcnow(),
        description=description
    )
    
    db.session.add(new_flag)
    
    # Update session risk score
    # Simple average calculation with existing risk
    session.total_risk_score = max(session.total_risk_score, severity)
    
    # Flag session if risk is high
    if severity > 0.7 and session.session_status != 'flagged':
        session.session_status = 'flagged'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'flag_id': new_flag.id,
        'message': 'Risk flag submitted successfully.'
    })

@api_bp.route('/report-unauthorized-process', methods=['POST'])
def report_unauthorized_process():
    """Report an unauthorized process for a session"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['session_id', 'process_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    session_id = data['session_id']
    process_name = data['process_name']
    
    # Check if session exists
    session = ProctorSession.query.get(session_id)
    if not session:
        return jsonify({'success': False, 'message': 'Session not found.'}), 404
    
    # Check test whitelisted processes
    test = Test.query.get(session.test_id)
    whitelisted = test.get_whitelisted_processes()
    
    # If process is actually whitelisted, don't flag it
    if process_name in whitelisted:
        return jsonify({
            'success': True,
            'is_authorized': True,
            'message': 'Process is authorized.'
        })
    
    # Create risk flag for unauthorized process
    new_flag = RiskFlag(
        session_id=session_id,
        flag_type='unauthorized_process',
        severity=0.8,  # High severity for unauthorized processes
        timestamp=datetime.utcnow(),
        description=f"Unauthorized process detected: {process_name}"
    )
    
    db.session.add(new_flag)
    
    # Update session risk score and status
    session.total_risk_score = max(session.total_risk_score, 0.8)
    
    if session.session_status != 'flagged':
        session.session_status = 'flagged'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_authorized': False,
        'flag_id': new_flag.id,
        'message': f'Unauthorized process "{process_name}" reported successfully.'
    })

@api_bp.route('/end-session', methods=['POST'])
def end_session():
    """End a proctoring session"""
    data = request.get_json()
    
    if 'session_id' not in data:
        return jsonify({'success': False, 'message': 'Missing session_id field.'}), 400
    
    session_id = data['session_id']
    
    # Check if session exists
    session = ProctorSession.query.get(session_id)
    if not session:
        return jsonify({'success': False, 'message': 'Session not found.'}), 404
        
    # Update session status and end time
    session.end_time = datetime.utcnow()
    if session.session_status == 'active':  # Only change if not already flagged
        session.session_status = 'completed'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Session ended successfully.'
    })

@api_bp.route('/submit-test-results', methods=['POST'])
def submit_test_results():
    """
    API endpoint for desktop app to submit completed test results
    
    Expected JSON format:
    {
        "access_code": "ABC123",
        "student_id": "12345",
        "end_time": "2023-06-20T15:30:00",
        "screenshots": [
            {
                "timestamp": "2023-06-20T14:05:00",
                "image_data": "base64_encoded_image",
                "risk_score": 0.2
            },
            ...
        ],
        "risk_flags": [
            {
                "flag_type": "multiple_faces",
                "severity": 0.8,
                "timestamp": "2023-06-20T14:10:00",
                "description": "Multiple faces detected in the frame"
            },
            ...
        ],
        "total_risk_score": 0.35
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
            
        required_fields = ['access_code', 'student_id', 'end_time']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Find the test by access code
        test = Test.query.filter_by(access_code=data['access_code']).first()
        if not test:
            return jsonify({
                'success': False,
                'message': 'Invalid access code'
            }), 404
            
        # Find the student by student_id
        student = Student.query.filter_by(student_id=data['student_id']).first()
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404
            
        # Check if a session already exists
        session = ProctorSession.query.filter_by(
            student_id=student.id,
            test_id=test.id
        ).first()
        
        if not session:
            # Create a new session if it doesn't exist
            session = ProctorSession(
                student_id=student.id,
                test_id=test.id,
                start_time=datetime.fromisoformat(data.get('start_time', datetime.now().isoformat())),
                session_status='active'
            )
            db.session.add(session)
            db.session.commit()
        
        # Update session with completed data
        session.end_time = datetime.fromisoformat(data['end_time'])
        session.total_risk_score = data.get('total_risk_score', 0.0)
        session.session_status = 'completed'
        
        # Process screenshots if provided
        if 'screenshots' in data and data['screenshots']:
            for screenshot_data in data['screenshots']:
                # Create screenshot record
                screenshot = Screenshot(
                    session_id=session.id,
                    timestamp=datetime.fromisoformat(screenshot_data['timestamp']),
                    risk_score=screenshot_data['risk_score']
                )
                
                # Prioritize image link over image data for better performance
                if 'image_link' in screenshot_data:
                    # Validate URL format (basic validation)
                    if not screenshot_data['image_link'].startswith(('http://', 'https://')):
                        return jsonify({
                            'success': False,
                            'message': f'Invalid image URL format: {screenshot_data["image_link"]}'
                        }), 400
                    
                    screenshot.image_path = screenshot_data['image_link']
                    
                # Fall back to image data if no link is provided
                elif 'image_data' in screenshot_data:
                    try:
                        image_bytes = base64.b64decode(screenshot_data['image_data'])
                        screenshot.image_data = image_bytes
                    except Exception as e:
                        return jsonify({
                            'success': False,
                            'message': f'Invalid base64 image data: {str(e)}'
                        }), 400
                else:
                    # No image data provided
                    logger.warning(f"Screenshot missing both image_link and image_data")
                
                db.session.add(screenshot)
        
        # Process risk flags if provided
        if 'risk_flags' in data and data['risk_flags']:
            for flag_data in data['risk_flags']:
                # Create risk flag record
                risk_flag = RiskFlag(
                    session_id=session.id,
                    flag_type=flag_data['flag_type'],
                    severity=flag_data['severity'],
                    timestamp=datetime.fromisoformat(flag_data['timestamp']),
                    description=flag_data.get('description', '')
                )
                
                db.session.add(risk_flag)
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Test results submitted successfully',
            'session_id': session.id
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500

@api_bp.route('/screenshot/<int:screenshot_id>', methods=['GET'])
def get_screenshot(screenshot_id):
    """Retrieve a screenshot by ID"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    
    # Check if user has permission to view this session
    # This would need proper authentication and authorization
    # which would typically use flask_login decorators
    
    # If there's an image link, return it
    if screenshot.image_path:
        return jsonify({
            'success': True,
            'screenshot_id': screenshot.id,
            'timestamp': screenshot.timestamp.isoformat(),
            'risk_score': screenshot.risk_score,
            'image_link': screenshot.image_path,
            'is_link': True
        })
    
    # If there's image data, encode it as base64
    elif screenshot.image_data:
        image_data_base64 = base64.b64encode(screenshot.image_data).decode('utf-8')
        return jsonify({
            'success': True,
            'screenshot_id': screenshot.id,
            'timestamp': screenshot.timestamp.isoformat(),
            'risk_score': screenshot.risk_score,
            'image_data': image_data_base64,
            'is_link': False
        })
    
    # If there's no image data or link
    else:
        return jsonify({
            'success': False,
            'message': 'No image data available for this screenshot'
        }), 404