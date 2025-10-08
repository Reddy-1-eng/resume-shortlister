import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
from email_sender import EmailSender      # Email sending logic
import traceback

# Ensure directories exist early
os.makedirs('logs', exist_ok=True)

# Import core functionality if available
try:
    from core import process_uploaded_resume  # AI resume processing logic
    CORE_AVAILABLE = True
except Exception as e:
    CORE_AVAILABLE = False
    print("Warning: core.py not found or failed to import. Using mock processing.")
    print("Import error details:", e)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('results', exist_ok=True)

# Initialize EmailSender
email_sender = EmailSender(
    smtp_server="smtp.office365.com",
    smtp_port=587,
    sender_email="bbaweekdayoutgatepermission@woxsen.edu.in",
    sender_password="Bbaoutgate@2024"
)

# Initialize resume processor if available
resume_processor = None
if CORE_AVAILABLE:
    try:
        # resume_processor = ResumeProcessor() # This line is no longer needed
        logger.info("Core functionality initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize core functionality: {e}")
        CORE_AVAILABLE = False

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_job_descriptions():
    """Load job descriptions from JSON file"""
    try:
        with open('job_descriptions/all_jobs.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Job descriptions file not found")
        return {}
    except Exception as e:
        logger.error(f"Error loading job descriptions: {e}")
        return {}

def mock_process_resume(file_path, job_role):
    """Mock resume processing for testing"""
    import random
    
    # Simulate processing time
    import time
    time.sleep(0.5)
    
    # Generate mock scores
    scores = {
        'overall': random.randint(60, 95),
        'tech': random.randint(50, 90),
        'exp': random.randint(40, 85),
        'edu': random.randint(60, 95),
        'soft': random.randint(70, 95),
        'rec': random.randint(80, 100)
    }
    
    # Extract name from filename
    name = os.path.splitext(os.path.basename(file_path))[0]
    name = name.replace('_', ' ').replace('-', ' ').title()
    
    # Generate mock email
    email = f"{name.lower().replace(' ', '.')}@example.com"
    
    return {
        'name': name,
        'email': email,
        'scores': scores,
        'file_path': file_path
    }

@app.route('/')
def index():
    """Main page"""
    try:
        job_descriptions = get_job_descriptions()
        return render_template('index.html', 
                             job_descriptions=job_descriptions,
                             core_available=CORE_AVAILABLE)
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return render_template('index.html', 
                             job_descriptions={},
                             core_available=False)

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads from frontend"""
    try:
        print("Received upload request")
        if 'files' not in request.files:
            print("No files in request.files")
            return jsonify({'success': False, 'error': 'No files provided'})
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            print("No files selected")
            return jsonify({'success': False, 'error': 'No files selected'})
        uploaded_files = []
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                uploaded_files.append(filename)
                print(f"File uploaded: {filename}")
            else:
                print(f"Invalid file type: {file.filename if file else 'None'}")
                return jsonify({'success': False, 'error': f'Invalid file type: {file.filename or "unknown"}'})
        return jsonify({'success': True, 'message': f'Successfully uploaded {len(uploaded_files)} file(s)', 'files': uploaded_files})
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'success': False, 'error': 'Upload failed'})

@app.route('/process', methods=['POST'])
def process_resumes():
    try:
        data = request.get_json()
        job_role = data.get('job_role')
        threshold = int(data.get('threshold', 70))
        files = data.get('files', [])

        if not job_role:
            return jsonify({'success': False, 'error': 'Job role is required'})
        if not files:
            return jsonify({'success': False, 'error': 'No files to process'})

        candidates = []
        for filename in files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
            try:
                if CORE_AVAILABLE:
                    result = process_uploaded_resume(file_path, job_role, threshold)
                    print("REAL process_uploaded_resume called")
                    print(result)
                else:
                    result = mock_process_resume(file_path, job_role)
                    print("MOCK process_resume called")
                overall = result.get('overall_score', 0) if CORE_AVAILABLE else result['scores']['overall']
                candidate = {
                    'name': result.get('ner_data', {}).get('name', 'Unknown') if CORE_AVAILABLE else result['name'],
                    'email': result.get('ner_data', {}).get('email', '') if CORE_AVAILABLE else result['email'],
                    'overall': overall,
                    'tech': result.get('technical_score', 0) if CORE_AVAILABLE else result['scores']['tech'],
                    'exp': result.get('experience_score', 0) if CORE_AVAILABLE else result['scores']['exp'],
                    'edu': result.get('education_score', 0) if CORE_AVAILABLE else result['scores']['edu'],
                    'soft': result.get('soft_skills_score', 0) if CORE_AVAILABLE else result['scores']['soft'],
                    'rec': result.get('recommendation', '') if CORE_AVAILABLE else result['scores']['rec'],
                    'file_path': file_path
                }
                candidates.append(candidate)
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                continue

        # Only proceed if there are candidates
        if not candidates:
            return jsonify({'success': False, 'error': 'No valid resumes processed.'})

        # Sort and filter by threshold
        candidates.sort(key=lambda x: x['overall'], reverse=True)
        filtered_candidates = [c for c in candidates if c['overall'] >= threshold]
        for i, candidate in enumerate(filtered_candidates, 1):
            candidate['rank'] = i

        top_candidates = filtered_candidates[:5]
        excel_filename = None
        if filtered_candidates:
            excel_filename = generate_excel_report(filtered_candidates, job_role)

        return jsonify({
            'success': True,
            'message': f'Processed {len(candidates)} resumes. Found {len(filtered_candidates)} candidates above {threshold}%.',
            'candidates': top_candidates,
            'total_candidates': len(candidates),
            'excel_file': excel_filename
        })
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({'success': False, 'error': 'Processing failed'})

@app.route('/test-email', methods=['POST'])
def test_email():
    """Test email configuration"""
    try:
        data = request.get_json()
        test_email = data.get('test_email', 'test@example.com')
        
        logger.info(f"Testing email configuration with: {test_email}")
        
        # Capture error message
        error_message = None
        try:
            success = email_sender.send_email(
                recipient_email=test_email,
                name="Test User",
                role="Test Role",
                match_percentage=85.0
            )
        except Exception as e:
            success = False
            error_message = str(e)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Test email sent successfully to {test_email}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to send test email' + (f': {error_message}' if error_message else '')
            })
    except Exception as e:
        logger.error(f"Test email error: {e}")
        return jsonify({'success': False, 'error': f'Test email failed: {str(e)}'})

@app.route('/send-emails', methods=['POST'])
def send_emails():
    """Send batch emails to candidates using EmailSender from email_sender.py"""
    try:
        data = request.get_json()
        candidates = data.get('candidates', [])
        threshold = data.get('threshold', 70)
        job_role = data.get('job_role', 'Software Engineer')
        
        logger.info(f"Email request received: {len(candidates)} candidates, threshold: {threshold}")
        
        if not candidates:
            return jsonify({'success': False, 'error': 'No candidates to email'})
        
        # Filter candidates above threshold and with valid emails
        qualified_candidates = []
        for candidate in candidates:
            if candidate.get('overall', 0) >= threshold:
                email = candidate.get('email', '').strip()
                if email and email != 'N/A' and '@' in email:
                    qualified_candidates.append(candidate)
                    logger.info(f"Qualified candidate: {candidate.get('name')} - {email} - Score: {candidate.get('overall')}")
                else:
                    logger.warning(f"Candidate {candidate.get('name')} has invalid email: {email}")
        
        if not qualified_candidates:
            return jsonify({'success': False, 'error': 'No candidates meet the threshold and have valid emails'})
        
        logger.info(f"Sending emails to {len(qualified_candidates)} qualified candidates")
        
        sent_count = 0
        failed_count = 0
        failed_details = []
        
        for candidate in qualified_candidates:
            try:
                logger.info(f"Attempting to send email to {candidate['email']}")
                success = email_sender.send_email(
                    recipient_email=candidate['email'],
                    name=candidate['name'],
                    role=job_role,
                    match_percentage=candidate['overall']
                )
                if success:
                    sent_count += 1
                    logger.info(f"✅ Email sent successfully to {candidate['email']}")
                else:
                    failed_count += 1
                    failed_details.append({'email': candidate['email'], 'error': 'Unknown error'})
                    logger.warning(f"❌ Failed to send email to {candidate['email']}")
            except Exception as e:
                failed_count += 1
                failed_details.append({'email': candidate['email'], 'error': str(e)})
                logger.error(f"❌ Error sending email to {candidate['email']}: {e}")
        
        message = f'Successfully sent {sent_count} out of {len(qualified_candidates)} emails'
        if failed_count > 0:
            message += f' ({failed_count} failed)'
        
        logger.info(f"Email sending completed: {message}")
        
        return jsonify({
            'success': True if sent_count > 0 else False,
            'message': message,
            'sent_count': sent_count,
            'total_attempted': len(qualified_candidates),
            'failed_details': failed_details
        })
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        return jsonify({'success': False, 'error': f'Email sending failed: {str(e)}'})

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated files"""
    try:
        file_path = os.path.join('results', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': 'Download failed'}), 500

def generate_excel_report(candidates, job_role):
    """Generate Excel report with all candidates"""
    try:
        # Create DataFrame
        df = pd.DataFrame(candidates)
        
        # Ensure all required columns exist
        required_columns = ['rank', 'name', 'email', 'overall', 'tech', 'exp', 'edu', 'soft', 'rec']
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0 if col in ['overall', 'tech', 'exp', 'edu', 'soft'] else 'N/A'
        
        # Reorder columns
        columns = ['rank', 'name', 'email', 'overall', 'tech', 'exp', 'edu', 'soft', 'rec']
        df = df[columns]
        
        # Rename columns for better readability
        df.columns = ['Rank', 'Name', 'Email', 'Overall Score', 'Technical Skills', 
                     'Experience', 'Education', 'Soft Skills', 'Recommendation']
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ranked_resume_results_{job_role}_{timestamp}.xlsx'
        file_path = os.path.join('results', filename)
        
        # Save to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Ranked Results', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Ranked Results']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Excel report generated: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Excel generation error: {e}")
        return None

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    """Handle file too large errors"""
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

if __name__ == '__main__':
    # Check if required directories exist
    required_dirs = ['uploads', 'logs', 'results', 'static', 'templates']
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
    
    print("=" * 60)
    print("🚀 Resume Shortlister Pro - Starting Application")
    print("=" * 60)
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"📊 Results folder: {os.path.abspath('results')}")
    print(f"📝 Logs folder: {os.path.abspath('logs')}")
    print(f"🔧 Core processing: {'Available' if CORE_AVAILABLE else 'Mock mode'}")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 