import os
import random
import string
import base64
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, jsonify, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import desc

from app import app, db
from models import User, Teacher, Student, Test, ProctorSession, Screenshot, RiskFlag
from utils import requires_roles, generate_access_code


# Home route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')


# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Create role-specific profile
        if role == 'teacher':
            teacher = Teacher(user_id=user.id)
            db.session.add(teacher)
        elif role == 'student':
            student_id = request.form.get('student_id')
            student = Student(user_id=user.id, student_id=student_id)
            db.session.add(student)
        
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        # Admin view - all tests and recent sessions
        recent_tests = Test.query.order_by(desc(Test.created_at)).limit(5).all()
        recent_sessions = ProctorSession.query.order_by(desc(ProctorSession.start_time)).limit(10).all()
        
        # Count of high-risk sessions
        high_risk_count = ProctorSession.query.filter(ProctorSession.total_risk_score > 0.7).count()
        
        return render_template(
            'dashboard.html',
            recent_tests=recent_tests,
            recent_sessions=recent_sessions,
            high_risk_count=high_risk_count
        )
    
    elif current_user.role == 'teacher':
        # Teacher view - their tests and sessions
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        recent_tests = Test.query.filter_by(teacher_id=teacher.id).order_by(desc(Test.created_at)).limit(5).all()
        
        active_test_ids = [test.id for test in Test.query.filter_by(teacher_id=teacher.id, is_active=True).all()]
        active_sessions = ProctorSession.query.filter(
            ProctorSession.test_id.in_(active_test_ids),
            ProctorSession.session_status == 'active'
        ).count()
        
        return render_template(
            'dashboard.html',
            recent_tests=recent_tests,
            active_sessions=active_sessions,
            teacher=teacher
        )
    
    elif current_user.role == 'student':
        # Student view - their sessions
        student = Student.query.filter_by(user_id=current_user.id).first()
        recent_sessions = ProctorSession.query.filter_by(student_id=student.id).order_by(desc(ProctorSession.start_time)).limit(5).all()
        
        return render_template(
            'dashboard.html',
            recent_sessions=recent_sessions,
            student=student
        )
    
    return render_template('dashboard.html')


# Code Generation route
@app.route('/code-generation', methods=['GET', 'POST'])
@login_required
@requires_roles(['admin', 'teacher'])
def code_generation():
    if current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    else:  # admin
        teacher = None
    
    # Initialize variables
    test = None
    encrypted_code = None
    access_code = None
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        # Get whitelisted processes from form (checkboxes)
        whitelisted_processes = request.form.getlist('whitelisted_processes')
        
        # Add custom processes if provided
        custom_processes = request.form.get('custom_processes', '')
        if custom_processes:
            custom_list = [p.strip() for p in custom_processes.split(',') if p.strip()]
            whitelisted_processes.extend(custom_list)
        
        if teacher is None and current_user.role == 'admin':
            teacher_id = request.form.get('teacher_id')
            teacher = Teacher.query.get(teacher_id)
        
        # Parse datetime strings
        try:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('code_generation'))
        
        # Generate unique access code
        access_code = generate_access_code()
        
        # Create new test
        test = Test(
            title=title,
            description=description,
            access_code=access_code,
            teacher_id=teacher.id,
            start_time=start_time,
            end_time=end_time,
            is_active=False
        )
        
        # Set whitelisted processes
        test.set_whitelisted_processes(whitelisted_processes)
        
        db.session.add(test)
        db.session.commit()
        
        # Generate encrypted test data for desktop client
        from utils import CRYPTO_AVAILABLE, encrypt_test_data
        encrypted_code = None
        
        # Secret key for encryption - should be stored in environment variables in production
        secret_key = os.environ.get('ENCRYPTION_SECRET', 'proctoring-default-key')
        
        if CRYPTO_AVAILABLE:
            encrypted_code = encrypt_test_data(
                test.id,
                access_code,
                test.get_whitelisted_processes(),
                start_time,
                end_time,
                secret_key
            )
            
            if encrypted_code:
                flash('Test created successfully with secure encrypted code!', 'success')
            else:
                flash(f'Test created successfully! Access code: {access_code}', 'success')
                flash('Warning: Could not generate encrypted code.', 'warning')
        else:
            flash(f'Test created successfully! Access code: {access_code}', 'success')
            flash('Note: Encrypted code generation is disabled. Install cryptography package to enable.', 'info')
        
        # If encrypted code was generated, show it on the page
        if encrypted_code:
            return render_template('code_generation.html', 
                                   teacher=teacher, 
                                   teachers=Teacher.query.all() if current_user.role == 'admin' else None,
                                   encrypted_code=encrypted_code,
                                   access_code=access_code,
                                   test=test)
        else:
            # Otherwise redirect to test management
            return redirect(url_for('test_management'))
    
    # If admin, get all teachers for selection
    teachers = None
    if current_user.role == 'admin':
        teachers = Teacher.query.all()
    
    return render_template('code_generation.html', teacher=teacher, teachers=teachers, test=test)


# Test Management route
@app.route('/test-management')
@login_required
@requires_roles(['admin', 'teacher'])
def test_management():
    if current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        tests = Test.query.filter_by(teacher_id=teacher.id).order_by(desc(Test.created_at)).all()
    else:  # admin
        tests = Test.query.order_by(desc(Test.created_at)).all()
    
    return render_template('test_management.html', tests=tests)


# Test Detail route
@app.route('/test/<int:test_id>')
@login_required
@requires_roles(['admin', 'teacher'])
def test_detail(test_id):
    test = Test.query.get_or_404(test_id)
    
    # Check if user has permission to view this test
    if current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if test.teacher_id != teacher.id:
            abort(403)
    
    # Get active sessions for this test
    active_sessions = ProctorSession.query.filter_by(
        test_id=test.id,
        session_status='active'
    ).all()
    
    # Get completed sessions for this test
    completed_sessions = ProctorSession.query.filter_by(
        test_id=test.id,
        session_status='completed'
    ).all()
    
    # Get flagged sessions for this test
    flagged_sessions = ProctorSession.query.filter_by(
        test_id=test.id,
        session_status='flagged'
    ).all()
    
    return render_template(
        'test_detail.html',
        test=test,
        active_sessions=active_sessions,
        completed_sessions=completed_sessions,
        flagged_sessions=flagged_sessions
    )


# Toggle Test Activation route
@app.route('/test/<int:test_id>/toggle-activation', methods=['POST'])
@login_required
@requires_roles(['admin', 'teacher'])
def toggle_test_activation(test_id):
    test = Test.query.get_or_404(test_id)
    
    # Check if user has permission to modify this test
    if current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if test.teacher_id != teacher.id:
            abort(403)
    
    # Toggle activation status
    test.is_active = not test.is_active
    db.session.commit()
    
    status = 'activated' if test.is_active else 'deactivated'
    flash(f'Test {status} successfully!', 'success')
    
    return redirect(url_for('test_detail', test_id=test.id))


# Student Detail/Session Detail route
@app.route('/session/<int:session_id>')
@login_required
@requires_roles(['admin', 'teacher'])
def student_detail(session_id):
    session = ProctorSession.query.get_or_404(session_id)
    
    # Check if user has permission to view this session
    if current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if session.test.teacher_id != teacher.id:
            abort(403)
    
    # Get screenshots for this session
    screenshots = Screenshot.query.filter_by(session_id=session.id).order_by(Screenshot.timestamp).all()
    
    # Get risk flags for this session
    risk_flags = RiskFlag.query.filter_by(session_id=session.id).order_by(desc(RiskFlag.severity)).all()
    
    return render_template(
        'student_detail.html',
        session=session,
        screenshots=screenshots,
        risk_flags=risk_flags
    )


# Test Completion Dashboard route
@app.route('/completed-tests')
@login_required
@requires_roles(['admin', 'teacher'])
def completed_tests():
    """Dashboard showing all completed test sessions with student data and risk scores."""
    
    # Get all completed sessions based on user role
    if current_user.role == 'admin':
        # Admins can see all completed sessions
        completed_sessions = ProctorSession.query.filter_by(session_status='completed').order_by(desc(ProctorSession.end_time)).all()
    else:
        # Teachers can only see their own tests' sessions
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher:
            abort(403)
        
        # Get all tests from this teacher
        teacher_test_ids = [test.id for test in Test.query.filter_by(teacher_id=teacher.id).all()]
        
        # Get completed sessions for these tests
        completed_sessions = ProctorSession.query.filter(
            ProctorSession.test_id.in_(teacher_test_ids),
            ProctorSession.session_status == 'completed'
        ).order_by(desc(ProctorSession.end_time)).all()
    
    # Get aggregated data for each session
    session_data = []
    for session in completed_sessions:
        # Get screenshot count
        screenshot_count = Screenshot.query.filter_by(session_id=session.id).count()
        
        # Get risk flag count
        risk_flag_count = RiskFlag.query.filter_by(session_id=session.id).count()
        
        # Add to session data
        session_data.append({
            'session': session,
            'screenshot_count': screenshot_count,
            'risk_flag_count': risk_flag_count
        })
    
    return render_template(
        'completed_tests.html',
        session_data=session_data,
        current_year=datetime.now().year
    )
