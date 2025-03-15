from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Text
from database import db  # Import db from database.py, not app.py
# User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


# Teacher model
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department = db.Column(db.String(100))
    
    # Relationships
    user = db.relationship('User', backref='teacher_profile')
    tests = db.relationship('Test', backref='teacher', lazy='dynamic')
    
    def __repr__(self):
        return f'<Teacher {self.user.username}>'


# Student model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='student_profile')
    proctor_sessions = db.relationship('ProctorSession', backref='student', lazy='dynamic')
    
    def __repr__(self):
        return f'<Student {self.user.username}>'


# Test/Exam model
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    access_code = db.Column(db.String(10), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    whitelisted_processes = db.Column(db.Text)  # Comma-separated list of allowed processes
    
    # Relationships
    proctor_sessions = db.relationship('ProctorSession', backref='test', lazy='dynamic')
    
    def __repr__(self):
        return f'<Test {self.title}>'
        
    def get_whitelisted_processes(self):
        """Returns a list of whitelisted processes"""
        if not self.whitelisted_processes:
            return []
        return [p.strip() for p in self.whitelisted_processes.split(',')]
        
    def set_whitelisted_processes(self, process_list):
        """Sets whitelisted processes from a list"""
        if not process_list:
            self.whitelisted_processes = None
        else:
            self.whitelisted_processes = ','.join(process_list)


# Proctoring Session model
class ProctorSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_risk_score = db.Column(db.Float, default=0.0)
    session_status = db.Column(db.String(20), default='active')  # active, completed, flagged
    
    # Relationships
    screenshots = db.relationship('Screenshot', backref='session', lazy='dynamic')
    risk_flags = db.relationship('RiskFlag', backref='session', lazy='dynamic')
    
    def __repr__(self):
        return f'<ProctorSession {self.id}>'


# Screenshot model
class Screenshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('proctor_session.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_data = db.Column(db.LargeBinary(length=(2**32)-1))  # Use LONGBLOB in MySQL
    image_path = db.Column(db.String(255))  # Path to image if stored on disk
    risk_score = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<Screenshot {self.id}>'


# Risk Flag model (for flagging suspicious activities)
class RiskFlag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('proctor_session.id'), nullable=False)
    flag_type = db.Column(db.String(50), nullable=False)  # e.g., 'multiple_faces', 'no_face', 'phone_detected'
    severity = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<RiskFlag {self.flag_type} - {self.severity}>'
