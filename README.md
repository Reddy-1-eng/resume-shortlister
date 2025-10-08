# 🎯 Resume Shortlister Pro

> **AI-Powered Resume Analysis & Candidate Ranking System**

A modern, web-based application that uses artificial intelligence to analyze resumes, rank candidates based on job requirements, and automate the email notification process for qualified candidates.

![Resume Shortlister Pro](https://img.shields.io/badge/Version-2.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Flask](https://img.shields.io/badge/Flask-2.0+-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🚀 Core Functionality
- **AI-Powered Resume Analysis**: Intelligent parsing and scoring of resumes
- **Multi-Format Support**: PDF, DOC, DOCX file formats
- **Smart Ranking**: Algorithm-based candidate ranking with multiple criteria
- **Batch Processing**: Handle multiple resumes simultaneously
- **Email Automation**: Automated email notifications to qualified candidates
- **Excel Export**: Detailed reports in Excel format

### 🎨 Modern UI/UX
- **Glassmorphism Design**: Beautiful glass-like interface
- **Responsive Layout**: Works perfectly on all devices
- **Drag & Drop Upload**: Intuitive file upload experience
- **Real-time Updates**: Live progress indicators and status updates
- **Smooth Animations**: Engaging user interactions
- **Dark Mode Support**: Automatic theme detection

### 🔧 Technical Features
- **Modular Architecture**: Clean, organized code structure
- **Error Handling**: Comprehensive error management
- **Logging System**: Detailed application logs
- **Security**: File validation and secure uploads
- **Performance**: Optimized for speed and efficiency

## 📁 Project Structure

```
resume_shortlister/
├── 📁 static/                    # Static assets
│   ├── 📁 css/                   # Stylesheets
│   │   └── style.css             # Main stylesheet
│   ├── 📁 js/                    # JavaScript files
│   │   └── app.js                # Main application logic
│   └── 📁 images/                # Images and icons
├── 📁 templates/                 # HTML templates
│   └── index.html                # Main application page
├── 📁 uploads/                   # Uploaded resume files
├── 📁 results/                   # Generated Excel reports
├── 📁 logs/                      # Application logs
├── 📁 job_descriptions/          # Job role definitions
│   └── all_jobs.json             # Job descriptions data
├── 📁 assets/                    # Additional assets
├── 📁 uploaded_files/            # Legacy uploaded files
├── app.py                        # Main Flask application
├── email_sender.py               # Email functionality
├── core.py                       # Core processing logic (optional)
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/resume-shortlister.git
cd resume-shortlister
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SENDER_EMAIL=your-email@domain.com
SENDER_PASSWORD=your-password
```

### Step 5: Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 🚀 Usage Guide

### 1. Upload Resumes
- **Drag & Drop**: Simply drag resume files onto the upload area
- **Browse Files**: Click the upload area to select files manually
- **Supported Formats**: PDF, DOC, DOCX
- **File Size Limit**: 50MB per file

### 2. Configure Processing
- **Select Job Role**: Choose from predefined job roles or add custom ones
- **Set Threshold**: Define minimum score threshold (0-100%)
- **Processing Criteria**:
  - Technical Skills
  - Experience
  - Education
  - Soft Skills
  - Overall Recommendation

### 3. Process & Analyze
- Click "Process Resumes" to start AI analysis
- View real-time processing progress
- Get instant results with candidate rankings

### 4. Review Results
- **Top 5 Candidates**: Automatically displayed
- **Detailed Scores**: Individual criteria breakdown
- **Ranking System**: AI-powered candidate ranking
- **Export Options**: Download complete Excel report

### 5. Send Emails
- **Batch Email**: Send notifications to qualified candidates
- **Customizable Templates**: Professional email templates
- **Delivery Tracking**: Monitor email delivery status

## 🔧 Configuration

### Job Roles Configuration
Edit `job_descriptions/all_jobs.json` to customize job roles:

```json
{
  "Software Engineer": {
    "description": "Full-stack development role",
    "requirements": ["Python", "JavaScript", "React", "Node.js"],
    "experience": "2-5 years",
    "education": "Bachelor's in Computer Science"
  },
  "Data Scientist": {
    "description": "Data analysis and ML role",
    "requirements": ["Python", "R", "SQL", "Machine Learning"],
    "experience": "3-7 years",
    "education": "Master's in Data Science"
  }
}
```

### Email Configuration
Update email settings in `email_sender.py`:

```python
email_sender = EmailSender(
    smtp_server="smtp.office365.com",
    smtp_port=587,
    sender_email="your-email@domain.com",
    sender_password="your-password"
)
```

### Custom Styling
Modify `static/css/style.css` to customize the appearance:

```css
:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --accent-color: #4ECDC4;
    --text-primary: #ffffff;
}
```

## 📊 API Endpoints

### File Upload
```http
POST /upload
Content-Type: multipart/form-data

Response: {
    "success": true,
    "message": "Successfully uploaded 3 file(s)",
    "files": ["file1.pdf", "file2.docx"]
}
```

### Resume Processing
```http
POST /process
Content-Type: application/json

{
    "job_role": "Software Engineer",
    "threshold": 70,
    "files": ["file1.pdf", "file2.docx"]
}

Response: {
    "success": true,
    "candidates": [...],
    "total_candidates": 5,
    "excel_file": "ranked_resume_results_20241201_143022.xlsx"
}
```

### Email Sending
```http
POST /send-emails
Content-Type: application/json

{
    "candidates": [...],
    "threshold": 70,
    "job_role": "Software Engineer"
}

Response: {
    "success": true,
    "message": "Successfully sent 3 out of 5 emails"
}
```

## 🎨 UI Components

### Design System
- **Color Palette**: Modern gradient-based design
- **Typography**: Inter font family for readability
- **Icons**: Font Awesome icon library
- **Animations**: Smooth CSS transitions and keyframes

### Responsive Breakpoints
- **Desktop**: 1200px and above
- **Tablet**: 768px - 1199px
- **Mobile**: Below 768px

### Interactive Elements
- **Hover Effects**: Enhanced user feedback
- **Loading States**: Progress indicators
- **Error Handling**: User-friendly error messages
- **Success Notifications**: Toast-style notifications

## 🔒 Security Features

### File Security
- **File Type Validation**: Only allowed extensions
- **File Size Limits**: 50MB maximum per file
- **Secure Filenames**: Timestamp-based naming
- **Upload Directory**: Isolated upload folder

### Data Protection
- **Input Sanitization**: XSS prevention
- **CSRF Protection**: Cross-site request forgery protection
- **Secure Headers**: Security-focused HTTP headers
- **Error Handling**: No sensitive data exposure

## 📈 Performance Optimization

### Frontend Optimization
- **Minified Assets**: Compressed CSS and JS
- **Lazy Loading**: On-demand resource loading
- **Caching**: Browser cache optimization
- **CDN Integration**: Fast asset delivery

### Backend Optimization
- **Async Processing**: Non-blocking operations
- **Database Optimization**: Efficient queries
- **Memory Management**: Proper resource cleanup
- **Logging**: Performance monitoring

## 🐛 Troubleshooting

### Common Issues

#### File Upload Problems
```bash
# Check file permissions
chmod 755 uploads/
chmod 755 results/

# Verify file size limits
# Check app.py MAX_CONTENT_LENGTH setting
```

#### Email Sending Issues
```bash
# Verify SMTP settings
# Check firewall settings
# Test with different email provider
```

#### Processing Errors
```bash
# Check Python dependencies
pip install -r requirements.txt

# Verify core.py availability
# Check log files in logs/ directory
```

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
python app.py
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style
- Follow PEP 8 Python style guide
- Use meaningful variable names
- Add comments for complex logic
- Include docstrings for functions

### Testing
```bash
# Run tests (if available)
python -m pytest tests/

# Manual testing checklist
- [ ] File upload functionality
- [ ] Resume processing
- [ ] Email sending
- [ ] Excel export
- [ ] Responsive design
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask Framework**: Web application framework
- **Font Awesome**: Icon library
- **Inter Font**: Typography
- **OpenAI**: AI processing inspiration
- **Community**: Contributors and feedback

## 📞 Support

### Getting Help
- **Documentation**: Check this README first
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Email**: Contact support@resumeshortlister.com

### Feature Requests
We welcome feature requests! Please:
1. Check existing issues first
2. Describe the feature clearly
3. Explain the use case
4. Provide mockups if possible

---

**Made with ❤️ by the Resume Shortlister Pro Team**

*Transform your recruitment process with AI-powered resume analysis* 