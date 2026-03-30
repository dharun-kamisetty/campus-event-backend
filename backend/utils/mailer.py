import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


async def send_email(to_email: str, subject: str, body: str):
    """
    Send email notification using SMTP
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Email credentials not configured. Skipping email notification.")
        return
    
    message = MIMEMultipart()
    message["From"] = SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject
    
    message.attach(MIMEText(body, "html"))
    
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True
        )
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


async def send_approval_email(
    user_email: str,
    event_name: str,
    venue_name: str,
    date: str,
    time: str,
    admin_comment: str = None
):
    """Send approval notification email"""
    subject = f"Venue Request Approved - {event_name}"
    body = f"""
    <html>
        <body>
            <h2>Venue Request Approved ✅</h2>
            <p>Your venue booking request has been approved!</p>
            <ul>
                <li><strong>Event:</strong> {event_name}</li>
                <li><strong>Venue:</strong> {venue_name}</li>
                <li><strong>Date:</strong> {date}</li>
                <li><strong>Time:</strong> {time}</li>
            </ul>
            {f'<p><strong>Admin Comment:</strong> {admin_comment}</p>' if admin_comment else ''}
            <p>Please proceed with your event planning.</p>
        </body>
    </html>
    """
    await send_email(user_email, subject, body)


async def send_rejection_email(
    user_email: str,
    event_name: str,
    date: str,
    admin_comment: str = None
):
    """Send rejection notification email"""
    subject = f"Venue Request Update - {event_name}"
    body = f"""
    <html>
        <body>
            <h2>Venue Request Update ❌</h2>
            <p>Unfortunately, your venue booking request could not be approved.</p>
            <ul>
                <li><strong>Event:</strong> {event_name}</li>
                <li><strong>Date:</strong> {date}</li>
            </ul>
            {f'<p><strong>Reason:</strong> {admin_comment}</p>' if admin_comment else ''}
            <p>Please contact the admin for more information or submit a new request.</p>
        </body>
    </html>
    """
    await send_email(user_email, subject, body)
