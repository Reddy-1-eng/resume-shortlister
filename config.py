"""
Configuration settings for Resume Shortlister Pro
"""

import os
from datetime import datetime

class Config:
    """Base configuration class"""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    # Directory paths
    RESULTS_FOLDER = 'results'
    LOGS_FOLDER = 'logs'
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    JOB_DESCRIPTIONS_FOLDER = 'job_descriptions'
    
    # Email settings
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.office365.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'your-email@domain.com')
    SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', 'your-password')
    
    # Processing settings
    DEFAULT_THRESHOLD = 70
    MAX_CANDIDATES_DISPLAY = 5
    PROCESSING_TIMEOUT = 300  # 5 minutes
    
    # UI settings
    APP_NAME = 'Resume Shortlister Pro'
    APP_VERSION = '2.0.0'
    APP_DESCRIPTION = 'AI-Powered Resume Analysis & Candidate Ranking System'
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(LOGS_FOLDER, 'app.log')
    
    # Security settings
    CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Performance settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create required directories
        directories = [
            Config.UPLOAD_FOLDER,
            Config.RESULTS_FOLDER,
            Config.LOGS_FOLDER,
            Config.STATIC_FOLDER,
            Config.TEMPLATES_FOLDER,
            Config.JOB_DESCRIPTIONS_FOLDER
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # Set Flask configuration
        app.config['SECRET_KEY'] = Config.SECRET_KEY
        app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
        app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
        
        # Configure logging
        import logging
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format=Config.LOG_FORMAT,
            handlers=[
                logging.FileHandler(Config.LOG_FILE),
                logging.StreamHandler()
            ]
        )

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SESSION_COOKIE_SECURE = True
    
    # Override with environment variables for production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required for production")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    UPLOAD_FOLDER = 'test_uploads'
    RESULTS_FOLDER = 'test_results'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    return config.get(config_name, config['default'])

# Utility functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def generate_filename(original_filename):
    """Generate secure filename with timestamp"""
    from werkzeug.utils import secure_filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    secure_name = secure_filename(original_filename)
    return f"{timestamp}_{secure_name}"

def get_excel_filename(job_role):
    """Generate Excel filename with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_job_role = job_role.replace(' ', '_').replace('/', '_')
    return f'ranked_resume_results_{safe_job_role}_{timestamp}.xlsx'

# Email templates
EMAIL_TEMPLATES = {
    'congratulations': {
        'subject': 'Congratulations {name}! Your Resume Matches {role} Role',
        'body': """
Dear {name},

We are pleased to inform you that your resume matches {match_percentage:.2f}% 
with the {role} role. Our team will reach out to you shortly for the next steps.

Best regards,
HR Team
        """
    },
    'rejection': {
        'subject': 'Thank you for your application - {role} Role',
        'body': """
Dear {name},

Thank you for your interest in the {role} position. After careful review of your application, 
we regret to inform you that we will not be moving forward with your candidacy at this time.

We appreciate your interest and wish you the best in your future endeavors.

Best regards,
HR Team
        """
    }
}

# Job role definitions (fallback if JSON file is not available)
DEFAULT_JOB_ROLES = {
    "Software Engineer": {
        "description": "Full-stack development role",
        "requirements": ["Python", "JavaScript", "React", "Node.js", "SQL"],
        "experience": "2-5 years",
        "education": "Bachelor's in Computer Science or related field"
    },
    "Data Scientist": {
        "description": "Data analysis and machine learning role",
        "requirements": ["Python", "R", "SQL", "Machine Learning", "Statistics"],
        "experience": "3-7 years",
        "education": "Master's in Data Science, Statistics, or related field"
    },
    "Product Manager": {
        "description": "Product strategy and management role",
        "requirements": ["Product Strategy", "Agile", "User Research", "Analytics"],
        "experience": "3-8 years",
        "education": "Bachelor's degree, MBA preferred"
    },
    "UI/UX Designer": {
        "description": "User interface and experience design role",
        "requirements": ["Figma", "Adobe Creative Suite", "User Research", "Prototyping"],
        "experience": "2-6 years",
        "education": "Design degree or equivalent experience"
    },
    "DevOps Engineer": {
        "description": "Infrastructure and deployment automation role",
        "requirements": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux"],
        "experience": "3-6 years",
        "education": "Computer Science or related technical degree"
    },
    "Business Analyst": {
        "description": "Business process analysis and improvement role",
        "requirements": ["Requirements Gathering", "Process Modeling", "SQL", "Analytics"],
        "experience": "2-5 years",
        "education": "Business, IT, or related degree"
    },
    "Marketing Specialist": {
        "description": "Digital marketing and campaign management role",
        "requirements": ["Digital Marketing", "SEO", "Social Media", "Analytics"],
        "experience": "2-4 years",
        "education": "Marketing or Communications degree"
    },
    "HR Manager": {
        "description": "Human resources management and recruitment role",
        "requirements": ["Recruitment", "Employee Relations", "HRIS", "Compliance"],
        "experience": "5-10 years",
        "education": "Human Resources or Business degree"
    }
}

# Scoring weights for different criteria
SCORING_WEIGHTS = {
    'technical_skills': 0.25,
    'experience': 0.25,
    'education': 0.20,
    'soft_skills': 0.15,
    'recommendation': 0.15
}

# File size limits for different file types
FILE_SIZE_LIMITS = {
    'pdf': 50 * 1024 * 1024,  # 50MB
    'doc': 30 * 1024 * 1024,  # 30MB
    'docx': 30 * 1024 * 1024  # 30MB
}

# Supported languages for internationalization
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'zh': '中文'
}

# Default language
DEFAULT_LANGUAGE = 'en' 