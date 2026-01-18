import os
import aiohttp
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
ENABLE_EMAIL = os.getenv("ENABLE_EMAIL", "false").lower() == "true"

logger = logging.getLogger("alert_manager")

async def send_alert_email(subject: str, html_content: str):
    """
    Sends an email using Resend API asynchronously.
    This function is intended to be called by other modules.
    """
    if not ENABLE_EMAIL:
        logger.info("Email notifications are disabled.")
        return False

    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY is missing.")
        return False

    url = "https://api.resend.com/emails"
    
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": EMAIL_FROM,
        "to": [EMAIL_TO],
        "subject": subject,
        "html": html_content
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status in [200, 201, 202]:
                    logger.info(f"Email sent successfully to {EMAIL_TO}")
                    return True
                else:
                    text = await response.text()
                    logger.error(f"Failed to send email. Status: {response.status}, Response: {text}")
                    return False
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
