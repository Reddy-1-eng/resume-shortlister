import google.generativeai as genai
from docx import Document
import os
import re
import json
import hashlib
from datetime import datetime
from scipy.stats import percentileofscore
import math
from email_sender import EmailSender
import PyPDF2

# DataProcessor Class
class DataProcessor:
    """Unified data processor for resume shortlisting system."""

    # --- 1. Utility/Helper Methods ---
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model_name = model_name
        self.supported_extensions = {'.pdf', '.docx'}
        # Configure Gemini API
        genai.configure(api_key="AIzaSyDYcXNBn1XEZLAnD0eKJ2-1N2LTxzu14yE")
        self.model = genai.GenerativeModel(model_name)
        self.email_sender = EmailSender(
            smtp_server="smtp.office365.com",
            smtp_port=587,
            sender_email="bbaweekdayoutgatepermission@woxsen.edu.in",
            sender_password="Bbaoutgate@2024"
        )

    def log(self, message, level="DEBUG"):
        print(f"[{level}] {message}")

    def execute_ai_operation(self, prompt, operation_name, fallback_func=None, fallback_args=None):
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            self.log(f"{operation_name} RAW response: {response_text}")  # Log raw output for debugging
            # Robustly extract the first valid JSON object from the output
            # Remove code block markers if present
            response_text = re.sub(r'```[a-zA-Z]*', '', response_text)
            # Find the first JSON object in the text
            json_match = re.search(r'\{[\s\S]*?\}', response_text)
            if json_match:
                json_text = json_match.group(0)
                parsed_data = json.loads(json_text)
            else:
                # Fallback: try to parse the whole response
                parsed_data = json.loads(response_text)
            self.log(f"{operation_name} PARSED data: {parsed_data}")
            return parsed_data
        except Exception as e:
            self.log(f"Error during {operation_name}: {e}. Using fallback.")
            if fallback_func and fallback_args:
                self.log(f"Using fallback for {operation_name} due to error")
                return fallback_func(*fallback_args)
            else:
                raise e

    def normalize_score(self, score):
        return score * 100 if score <= 1.0 else score

    def create_fallback_data(self, data_type="evaluation", **kwargs):
        if data_type == "evaluation":
            basic_score = kwargs.get("basic_score", 0)
            return {
                "overall_score": basic_score,
                "technical_skills_score": basic_score,
                "experience_score": basic_score,
                "education_score": basic_score,
                "soft_skills_score": basic_score,
                "detailed_feedback": "Basic word overlap analysis (AI evaluation failed)",
                "strengths": ["Basic keyword matching"],
                "areas_for_improvement": ["AI evaluation unavailable"],
                "recommendation": "MAYBE" if basic_score >= 50 else "REJECT"
            }
        elif data_type == "ner":
            return {
                "name": kwargs.get("name", "N/A"),
                "email": kwargs.get("email", "N/A"),
                "phone": kwargs.get("phone", "N/A"),
            }
        return {}

    def parse_json_response(self, response_text, function_name="Unknown"):
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                parsed_data = json.loads(json_text)
            else:
                parsed_data = json.loads(response_text)
            if isinstance(parsed_data, list):
                parsed_data = parsed_data[0] if parsed_data else {}
            self.log(f"Successfully parsed {function_name} data: {parsed_data}")
            return parsed_data
        except json.JSONDecodeError as e:
            self.log(f"JSON parsing failed for {function_name}: {e}")
            raise ValueError(f"JSON parsing failed for {function_name}")

    def safe_str(self, val):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return ""
        return str(val)

    # --- 2. File/Data Extraction ---
    def validate_file_type(self, file_path):
        return os.path.splitext(file_path)[1].lower() in self.supported_extensions

    def extract_file_content(self, file_path):
        try:
            if not self.validate_file_type(file_path):
                self.log(f"Unsupported file type: {os.path.splitext(file_path)[1].lower()}")
                return []
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                blocks = []
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            lines = [line.strip() for line in text.split('\n') if line.strip()]
                            blocks.extend(lines)
                return blocks
            elif ext == ".docx":
                doc = Document(file_path)
                return [para.text for para in doc.paragraphs if para.text.strip()]
        except Exception as e:
            self.log(f"Error extracting content from {file_path}: {e}")
            return []

    def load_job_data(self, filename="job_descriptions/all_jobs.json"):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Could not load job data: {e}")
            return {}

    def get_job_info(self, role=None, title=None, action="load"):
        all_jobs = self.load_job_data()
        if action == "load" and role:
            role_key = role.lower().replace(' ', '_') if ' ' in role else role
            return all_jobs.get(role_key, {})
        elif action == "names":
            return [job_data["title"] for job_data in all_jobs.values() if isinstance(job_data, dict) and "title" in job_data]
        elif action == "key" and title:
            for key, job_data in all_jobs.items():
                if isinstance(job_data, dict) and job_data.get("title") == title:
                    return key
        return None

    def extract_job_description_text(self, jd_data):
        if isinstance(jd_data, dict):
            return " ".join([
                jd_data.get("title", ""),
                jd_data.get("summary", ""),
                " ".join(jd_data.get("responsibilities", [])),
                " ".join(jd_data.get("qualifications", []))
            ])
        return str(jd_data)

    # --- 3. AI Operations ---
    def compute_similarity(self, resume_text, job_description):
        prompt = f'''
        ### HR Resume Evaluation Specialist
        You are an experienced HR professional with expertise in technical recruitment. Your task is to evaluate a candidate's resume against a specific job description and provide a comprehensive assessment.
        ### Evaluation Criteria:
        1. *Technical Skills Match* (40% weight):
           - Evaluate how well the candidate's technical skills align with job requirements
           - Consider programming languages, frameworks, tools, and technologies
           - Assess depth and breadth of technical expertise
        2. *Experience Relevance* (30% weight):
           - Analyze work experience relevance to the role
           - Consider industry experience, project complexity, and achievements
           - Evaluate progression and growth in career
        3. *Education & Certifications* (15% weight):
           - Assess educational background alignment
           - Consider relevant certifications and training
           - Evaluate academic performance and achievements
        4. *Soft Skills & Cultural Fit* (15% weight):
           - Evaluate communication skills, leadership, teamwork
           - Assess problem-solving abilities and adaptability
           - Consider cultural alignment and values
        ### Job Description:
        {job_description}
        ### Resume Content:
        {resume_text}
        ### Evaluation Instructions:
        - Act as a senior HR professional with 10+ years of experience
        - Be thorough but fair in your assessment
        - Consider both explicit qualifications and transferable skills
        - Look for potential and growth indicators
        - Provide specific reasoning for your score
        ### Output Format:
        Respond ONLY with a single valid JSON object and NOTHING else. Do NOT include any code block markers, comments, or extra text. The output must be a single JSON object in the following format:
        {{
            "overall_score": <score between 0-100>,
            "technical_skills_score": <score between 0-100>,
            "experience_score": <score between 0-100>,
            "education_score": <score between 0-100>,
            "soft_skills_score": <score between 0-100>,
            "detailed_feedback": "<detailed explanation of the evaluation>",
            "strengths": ["<strength1>", "<strength2>", "<strength3>"],
            "areas_for_improvement": ["<area1>", "<area2>", "<area3>"],
            "recommendation": "<RECOMMEND/MAYBE/REJECT>"
        }}
        '''
        def basic_word_overlap_fallback():
            job_words = set(job_description.lower().split())
            resume_words = set(resume_text.lower().split())
            match_count = len(job_words & resume_words)
            total_job_words = len(job_words)
            basic_score = (match_count / total_job_words) * 100 if total_job_words > 0 else 0
            if match_count > 0:
                match_ratio = match_count / total_job_words
                if match_ratio > 0.3:
                    basic_score = min(100, basic_score * 1.2)
                elif match_ratio < 0.1:
                    basic_score = max(0, basic_score * 0.8)
                if basic_score < 10:
                    basic_score = 10
            self.log(f"Fallback word overlap: {match_count}/{total_job_words} words matched, score: {basic_score:.1f}")
            fallback_data = self.create_fallback_data("evaluation", basic_score=basic_score)
            self.log(f"Fallback evaluation data: {fallback_data}")
            return fallback_data
        return self.execute_ai_operation(
            prompt=prompt,
            operation_name="AI evaluation",
            fallback_func=basic_word_overlap_fallback,
            fallback_args=()
        )

    def fallback_ner_extraction(self, text):
        name_patterns = [
            r"([A-Z][a-z]+\s[A-Z][a-z]+\s[A-Z][a-z]+)",
            r"([A-Z][a-z]+\s[A-Z][a-z]+)",
            r"([A-Z][A-Z]+\s[A-Z][A-Z]+)",
        ]
        name = "N/A"
        for pattern in name_patterns:
            name_match = re.search(pattern, text)
            if name_match:
                name = name_match.group(1)
                if name.lower() not in ['machine learning', 'data science', 'artificial intelligence', 'deep learning']:
                    break
        # If still no name, use first non-empty line
        if name == "N/A":
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if lines:
                name = lines[0]
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        phone_match = re.search(r"(\+?\d[\d\s\-]{7,14}\d)", text)
        email = email_match.group(0) if email_match else None
        if not email:
            # Generate a pseudo-unique email using a hash of name+text
            base = (name or "N/A") + text[:100]
            pseudo_email = f"{hashlib.md5(base.encode()).hexdigest()[:8]}@noemail.local"
            email = pseudo_email
        self.log(f"[FALLBACK NER] Extracted name: {name}, email: {email}")
        return self.create_fallback_data("ner", 
            name=name,
            email=email,
            phone=phone_match.group(0) if phone_match else "N/A"
        )

    def extract_ner(self, text, role=None):
        job_key = self.get_job_info(title=role, action="key") if role else None
        jd_context = self.get_job_info(role=job_key, action="load") if job_key else {}
        prompt = f'''
        ### Resume Entity Extractor
        You are an advanced Named Entity Recognition specialist trained specifically for resume/CV parsing. Extract personal identifiers with maximum precision.
        ### Target Entities:
        1. Full Name
        2. Email Address
        3. Phone Number
        ### Extraction Guidelines:
        #### Name Extraction (Highest Priority):
        - Look for names in header sections, "About Me", or after phrases like "Name:", "I am", etc.
        - Extract complete names (first, middle, last) with proper capitalization
        - Focus on personal names only, not organizations, degrees, or locations
        - Check for names in signature blocks or contact information sections
        - Ignore common resume headings that might be misidentified as names
        - DO NOT return organization names, university names, or location names as person names
        - If multiple name candidates exist, prioritize those in header/contact sections
        #### Email Extraction:
        - Extract standard email format (username@domain.tld)
        - Verify email has proper domain structure
        - Ignore emails that appear to be examples or templates
        - Look for emails near contact information sections
        #### Phone Extraction:
        - Identify phone numbers in various formats (international, local)
        - Handle numbers with different separators (spaces, dots, dashes)
        - Recognize numbers with country codes and extensions
        - Look for nearby context words like "Phone:", "Mobile:", "Tel:", etc.
        ### Verification Steps:
        1. Verify that extracted names are actual person names (not companies, locations, or section headings)
        2. Confirm that emails follow proper format
        3. Ensure phone numbers have sufficient digits to be valid
        4. Apply additional validation against known invalid patterns
        ### Job Description Context (for better extraction):
        {jd_context}
        ### Resume Text:
        {text}
        ### Output Format:
        Respond ONLY with a single valid JSON object and NOTHING else. Do NOT include any code block markers, comments, or extra text. The output must be a single JSON object in the following format:
        {{"name": "<full name>", "email": "<email address>", "phone": "<phone number>"}}
        '''
        return self.execute_ai_operation(
            prompt=prompt,
            operation_name="NER extraction",
            fallback_func=self.fallback_ner_extraction,
            fallback_args=(text,)
        )

    # --- 4. Result Construction ---
    def build_result_dict(self, ner_data, evaluation_data, overall_score, technical_score, 
                         experience_score, education_score, soft_skills_score, 
                         recommendation, message_suffix=""):
        overall_score = self.normalize_score(overall_score)
        technical_score = self.normalize_score(technical_score)
        experience_score = self.normalize_score(experience_score)
        education_score = self.normalize_score(education_score)
        soft_skills_score = self.normalize_score(soft_skills_score)
        result_str = f"✅ Processed {ner_data['name']} ({ner_data['email']}) - Overall: {round(overall_score, 1)}% | Tech: {round(technical_score, 1)}% | Exp: {round(experience_score, 1)}% | Edu: {round(education_score, 1)}% | Soft: {round(soft_skills_score, 1)}% | Rec: {recommendation}{message_suffix}"
        return {
            "result_str": result_str,
            "overall_score": overall_score,
            "technical_score": technical_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "soft_skills_score": soft_skills_score,
            "recommendation": recommendation,
            "ner_data": ner_data,
            "evaluation_data": evaluation_data
        }

    def create_error_result(self, error_message, error_type="General"):
        return {
            "result_str": f"❌ {error_type} error: {error_message}",
            "overall_score": 0,
            "technical_score": 0,
            "experience_score": 0,
            "education_score": 0,
            "soft_skills_score": 0,
            "recommendation": "REJECT",
            "ner_data": {"name": "N/A", "email": "N/A", "phone": "N/A"},
            "evaluation_data": {}
        }

    def send_shortlist_email(self, recipient_email, name, role, match_percentage):
        return self.email_sender.send_email(
            recipient_email=recipient_email,
            name=name,
            role=role,
            match_percentage=match_percentage
        )

    # --- 5. Excel/Historical Data Management ---
    def manage_data(self, action="save", **kwargs):
        try:
            import pandas as pd
            if action == "save" and all(k in kwargs for k in ["results_data", "role", "threshold"]):
                results_dir = os.path.join(os.getcwd(), "results")
                os.makedirs(results_dir, exist_ok=True)
                excel_file = os.path.join(results_dir, "ranked_resume_results.xlsx")
                # Build DataFrame directly from results_data
                records = []
                for result in kwargs["results_data"]:
                    if isinstance(result, dict) and "result_str" in result:
                        candidate_name = result.get("ner_data", {}).get("name", "N/A")
                        email = result.get("ner_data", {}).get("email", "N/A")
                        overall_score = result.get("overall_score", 0)
                        records.append({
                            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'Job Role': kwargs["role"],
                            'Threshold': kwargs["threshold"],
                            'Candidate Name': candidate_name,
                            'Email': email,
                            'Overall Score (%)': round(overall_score, 1),
                            'Technical Skills (%)': round(result.get("technical_score", 0), 1),
                            'Experience (%)': round(result.get("experience_score", 0), 1),
                            'Education (%)': round(result.get("education_score", 0), 1),
                            'Soft Skills (%)': round(result.get("soft_skills_score", 0), 1),
                            'Recommendation': result.get("recommendation", "MAYBE"),
                            'Status': "Ready for Email" if (overall_score >= kwargs["threshold"] and email != "N/A") else "Below Threshold",
                            'Detailed Feedback': result.get("evaluation_data", {}).get("detailed_feedback", "N/A"),
                            'Strengths': "; ".join(result.get("evaluation_data", {}).get("strengths", [])),
                            'Areas for Improvement': "; ".join(result.get("evaluation_data", {}).get("areas_for_improvement", [])),
                            'Full Result': result["result_str"]
                        })
                    else:
                        records.append({
                            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'Job Role': kwargs["role"],
                            'Threshold': kwargs["threshold"],
                            'Candidate Name': 'N/A',
                            'Email': 'N/A',
                            'Overall Score (%)': 0,
                            'Technical Skills (%)': 0,
                            'Experience (%)': 0,
                            'Education (%)': 0,
                            'Soft Skills (%)': 0,
                            'Recommendation': 'REJECT',
                            'Status': 'Error',
                            'Detailed Feedback': 'N/A',
                            'Strengths': 'N/A',
                            'Areas for Improvement': 'N/A',
                            'Full Result': str(result) if isinstance(result, str) else 'Error processing'
                        })
                df = pd.DataFrame(records)
                # Calculate percentiles efficiently using pandas
                if not df.empty:
                    df['Percentile'] = df['Overall Score (%)'].rank(pct=True, method='max') * 100
                else:
                    df['Percentile'] = 0
                # Add Rank
                df = df.sort_values('Overall Score (%)', ascending=False).reset_index(drop=True)
                df['Rank'] = range(1, len(df) + 1)
                # Save to Excel
                df.to_excel(excel_file, index=False)
                self.log(f"Ranked results saved to Excel: {excel_file}")
                return excel_file
            elif action == "load" and "role" in kwargs:
                results_dir = os.path.join(os.getcwd(), "results")
                if not os.path.exists(results_dir):
                    return []
                all_results = []
                for filename in os.listdir(results_dir):
                    if filename.endswith('.xlsx') and 'ranked_resume_results' in filename:
                        file_path = os.path.join(results_dir, filename)
                        try:
                            df = pd.read_excel(file_path)
                            role_results = df[df['Job Role'] == kwargs["role"]]
                            for _, row in role_results.iterrows():
                                result_data = {
                                    'result_str': row.get('Full Result', ''),
                                    'overall_score': float(row.get('Overall Score (%)', 0) or 0),
                                    'technical_score': float(row.get('Technical Skills (%)', 0) or 0),
                                    'experience_score': float(row.get('Experience (%)', 0) or 0),
                                    'education_score': float(row.get('Education (%)', 0) or 0),
                                    'soft_skills_score': float(row.get('Soft Skills (%)', 0) or 0),
                                    'recommendation': row.get('Recommendation', 'MAYBE'),
                                    'ner_data': {
                                        'name': self.safe_str(row.get('Candidate Name', 'N/A')) or 'N/A',
                                        'email': self.safe_str(row.get('Email', 'N/A')),
                                        'phone': 'N/A'
                                    },
                                    'evaluation_data': {
                                        'detailed_feedback': row.get('Detailed Feedback', 'N/A'),
                                        'strengths': (row.get('Strengths') or '').split('; '),
                                        'areas_for_improvement': (row.get('Areas for Improvement') or '').split('; ')
                                    },
                                    'timestamp': row.get('Timestamp', ''),
                                    'batch_id': filename
                                }
                                all_results.append(result_data)
                        except Exception as e:
                            self.log(f"Error reading Excel file {filename}: {e}")
                            continue
                # Deduplicate by (name, email)
                seen_keys = set()
                deduped_results = []
                for result in all_results:
                    name = str(result.get('ner_data', {}).get('name', '')).lower()
                    email = str(result.get('ner_data', {}).get('email', '')).lower()
                    key = (name, email)
                    if key not in seen_keys:
                        deduped_results.append(result)
                        seen_keys.add(key)
                self.log(f"Deduplicated results: {len(deduped_results)} out of {len(all_results)}")
                return deduped_results
            elif action == "rank" and "all_results" in kwargs:
                top_n = kwargs.get("top_n", 5)
                sorted_results = sorted(kwargs["all_results"], key=lambda x: x.get('overall_score', 0), reverse=True)
                top_results = sorted_results[:top_n]
                for i, result in enumerate(top_results, 1):
                    result['global_rank'] = i
                    result['total_candidates'] = len(kwargs["all_results"])
                self.log(f"Top {len(top_results)} candidates selected from {len(kwargs['all_results'])} total candidates")
                return top_results
            return []
        except Exception as e:
            self.log(f"Error in data operation: {e}")
            return []

    # --- 6. Main Orchestration ---
    def process_uploaded_resume(self, file_path, role, threshold):
        try:
            self.log(f"Starting process_uploaded_resume for file: {file_path}, role: {role}, threshold: {threshold}")
            
            # Validate file exists
            if not os.path.exists(file_path):
                return self.create_error_result("File not found. Please ensure the file was uploaded correctly.", "File Not Found")
            
            blocks = self.extract_file_content(file_path)
            if not blocks:
                return self.create_error_result("No content could be extracted from the file.", "Content Extraction")
            self.log(f"Extracted {len(blocks)} blocks from file.")
            full_text = " ".join(blocks)
            self.log(f"Full text length: {len(full_text)}")
            
            # Simplified job description loading
            jd_data = self.get_job_info(role=role, action="load")
            if not jd_data:
                return self.create_error_result(f"Unknown or missing job title: {role}. Please check the available job roles.", "Job Title")
            jd_text = self.extract_job_description_text(jd_data)
            
            evaluation_data = self.compute_similarity(full_text, jd_text)
            self.log(f"AI evaluation data: {evaluation_data}")
            scores = {
                "overall": evaluation_data.get("overall_score", 0),
                "technical": evaluation_data.get("technical_skills_score", 0),
                "experience": evaluation_data.get("experience_score", 0),
                "education": evaluation_data.get("education_score", 0),
                "soft_skills": evaluation_data.get("soft_skills_score", 0)
            }
            recommendation = evaluation_data.get("recommendation", "MAYBE")
            self.log(f"Raw scores: {scores}")
            
            ner_data = self.extract_ner(full_text, role=role)
            self.log(f"NER data: {ner_data}")
            
            if scores["overall"] >= threshold and ner_data["email"] != "N/A":
                message_suffix = " (Ready to send email)"
                # Email sending is now handled in batch via /send-emails endpoint in app.py
            else:
                self.log(f"Below threshold or no valid email. Score: {scores['overall']}, Email: {ner_data['email']}")
                message_suffix = " (Below threshold or no valid email)"
            
            result_data = self.build_result_dict(
                ner_data=ner_data,
                evaluation_data=evaluation_data,
                overall_score=scores["overall"],
                technical_score=scores["technical"],
                experience_score=scores["experience"],
                education_score=scores["education"],
                soft_skills_score=scores["soft_skills"],
                recommendation=recommendation,
                message_suffix=message_suffix
            )
            self.log(f"Returning detailed result: {result_data['result_str']}")
            return result_data
        except FileNotFoundError:
            return self.create_error_result("File not found. Please ensure the file was uploaded correctly.", "File Not Found")
        except PermissionError:
            return self.create_error_result("Permission denied accessing the file.", "Permission Denied")
        except Exception as e:
            # Check if this is a Gemini API connection error that should have been handled by fallback
            if "Failed to connect to Gemini" in str(e) or "Gemini" in str(e):
                self.log(f"Gemini API connection error but fallback should have handled this: {str(e)}")
            # Try to create a basic fallback result
            try:
                fallback_evaluation = self.create_fallback_data("evaluation", basic_score=50)
                fallback_ner = self.fallback_ner_extraction(full_text)
                result_data = self.build_result_dict(
                    ner_data=fallback_ner,
                    evaluation_data=fallback_evaluation,
                    overall_score=fallback_evaluation["overall_score"],
                    technical_score=fallback_evaluation["technical_skills_score"],
                    experience_score=fallback_evaluation["experience_score"],
                    education_score=fallback_evaluation["education_score"],
                    soft_skills_score=fallback_evaluation["soft_skills_score"],
                    recommendation=fallback_evaluation["recommendation"],
                    message_suffix=" (Fallback processing)"
                )
                self.log(f"Created fallback result: {result_data['result_str']}")
                return result_data
            except Exception as fallback_error:
                self.log(f"Fallback also failed: {fallback_error}")
                return self.create_error_result(f"AI and fallback processing failed: {str(e)}", "Processing Error")

# --- 7. Legacy/Wrapper Functions ---

def create_fallback_data(data_type="evaluation", **kwargs):
    processor = DataProcessor()
    return processor.create_fallback_data(data_type, **kwargs)

def parse_json_response(response_text, function_name="Unknown"):
    processor = DataProcessor()
    return processor.parse_json_response(response_text, function_name)

def manage_excel_data(results_data=None, role=None, threshold=None, action="save"):
    processor = DataProcessor()
    return processor.manage_data(action=action, results_data=results_data, role=role, threshold=threshold)

def manage_historical_data(role=None, all_results=None, action="load", top_n=5):
    processor = DataProcessor()
    return processor.manage_data(action=action, role=role, all_results=all_results, top_n=top_n)

def load_job_data(filename="job_descriptions/all_jobs.json"):
    processor = DataProcessor()
    return processor.load_job_data(filename)

def get_job_info(role=None, title=None, action="load"):
    processor = DataProcessor()
    return processor.get_job_info(role=role, title=title, action=action)

def extract_file_content(file_path):
    processor = DataProcessor()
    return processor.extract_file_content(file_path)

def compute_similarity(resume_text, job_description, model_name="gemini-2.5-flash"):
    processor = DataProcessor(model_name)
    return processor.compute_similarity(resume_text, job_description)

def extract_ner(text, model_name="gemini-2.5-flash", role=None):
    processor = DataProcessor(model_name)
    return processor.extract_ner(text, role)

def create_error_result(error_message, error_type="General"):
    processor = DataProcessor()
    return processor.create_error_result(error_message, error_type)

def process_uploaded_resume(file_path, role, threshold, model_name="gemini-2.5-flash"):
    processor = DataProcessor(model_name)
    return processor.process_uploaded_resume(file_path, role, threshold)