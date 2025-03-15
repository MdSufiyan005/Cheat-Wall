import os
import logging
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for debugging
logging_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, logging_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"Initializing application with logging level: {logging_level}")

# Create the Flask app
app = Flask(__name__)

# Configure the app with secure secret key
secret_key = os.environ.get("FLASK_SECRET_KEY")
if not secret_key:
    if app.debug:
        logger.warning("No FLASK_SECRET_KEY set, using a random one for development. DO NOT USE IN PRODUCTION!")
        import secrets
        secret_key = secrets.token_hex(32)
    else:
        logger.critical("No FLASK_SECRET_KEY environment variable set in production mode!")
        raise RuntimeError("FLASK_SECRET_KEY environment variable must be set in production mode")

app.secret_key = secret_key

# Set the database URL from environment variable
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    logger.warning("No DATABASE_URL environment variable set! Using SQLite database for development.")
    database_url = "sqlite:///cheatwall.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Import db after configuring app
from database import db

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models after initializing db
import models
from models import User

# Setup login manager user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processors
@app.context_processor
def inject_current_year():
    from datetime import datetime
    return {'current_year': datetime.now().year}

# Create database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# Import and register routes
import routes

# Register API endpoints
from api import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)