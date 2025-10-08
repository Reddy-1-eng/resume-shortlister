import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    """
    A class to handle sending emails via SMTP.
    """
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_email(self, recipient_email, name, role, match_percentage):
        """
        Sends a congratulatory email to the candidate.
        """
        if not recipient_email or recipient_email == "N/A":
            logger.warning("No valid recipient email provided")
            return False
            
        subject = f"Congratulations {name}! Your Resume Matches {role} Role"
        body = f"""
Dear {name},

We are pleased to inform you that your resume matches {match_percentage:.2f}% 
with the {role} role. Our team will reach out to you shortly for the next steps.

Best regards,
HR Team
        """
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        try:
            logger.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            
            # Connect to the SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.set_debuglevel(1)  # Enable debug output

            # Start TLS explicitly (ensures encryption of communication)
            logger.info("Starting TLS connection...")
            server.ehlo()  # Identifies itself to the server
            server.starttls()  # Initiate TLS
            server.ehlo()  # Re-identify after TLS

            # Log in to the email account
            logger.info(f"Attempting to login with: {self.sender_email}")
            server.login(self.sender_email, self.sender_password)
            logger.info("Login successful!")

            # Send the email
            logger.info(f"Sending email to: {recipient_email}")
            server.sendmail(self.sender_email, recipient_email, msg.as_string())
            server.quit()
            logger.info(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {e}")
            logger.error("Please check your email and password. For Office 365, you may need to:")
            logger.error("1. Use an App Password instead of your regular password")
            logger.error("2. Enable 2-factor authentication and generate an app password")
            logger.error("3. Check if your account allows SMTP access")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"❌ Recipient email refused: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"❌ SMTP server disconnected: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return False