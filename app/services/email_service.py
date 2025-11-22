import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings

logger = logging.getLogger("lms.email")


async def send_email(to: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Send email using SMTP or provider API.
    Currently logs email content. Replace with actual SMTP implementation.
    """
    logger.info("send_email: to=%s subject=%s", to, subject)
    logger.debug("Email body: %s", body)
    
    # TODO: Implement actual email sending
    # Example SMTP implementation:
    # import aiosmtplib
    # message = MIMEMultipart("alternative")
    # message["From"] = settings.SMTP_FROM
    # message["To"] = to
    # message["Subject"] = subject
    # message.attach(MIMEText(body, "plain"))
    # if html_body:
    #     message.attach(MIMEText(html_body, "html"))
    # await aiosmtplib.send(
    #     message,
    #     hostname=settings.SMTP_HOST,
    #     port=settings.SMTP_PORT,
    #     username=settings.SMTP_USER,
    #     password=settings.SMTP_PASSWORD,
    #     use_tls=settings.SMTP_TLS,
    # )
    
    return True


async def send_verification_email(to: str, token: str):
    """Send email verification link"""
    verify_url = f"{settings.FRONTEND_ORIGIN}/verify-email?token={token}"
    subject = "Verify your email"
    body = f"""
Hi,

Please verify your email address by clicking the link below:

{verify_url}

This link will expire in 24 hours.

Thanks,
LMS Team
    """
    html_body = f"""
    <html>
      <body>
        <h2>Verify Your Email</h2>
        <p>Please click the button below to verify your email address:</p>
        <a href="{verify_url}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Verify Email</a>
        <p>Or copy this link: {verify_url}</p>
        <p>This link expires in 24 hours.</p>
      </body>
    </html>
    """
    return await send_email(to, subject, body, html_body)


async def send_password_reset_email(to: str, token: str):
    """Send password reset link"""
    reset_url = f"{settings.FRONTEND_ORIGIN}/reset-password?token={token}"
    subject = "Reset your password"
    body = f"""
Hi,

You requested to reset your password. Click the link below:

{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.

Thanks,
LMS Team
    """
    html_body = f"""
    <html>
      <body>
        <h2>Reset Your Password</h2>
        <p>Click the button below to reset your password:</p>
        <a href="{reset_url}" style="background-color: #2196F3; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Reset Password</a>
        <p>Or copy this link: {reset_url}</p>
        <p>This link expires in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
      </body>
    </html>
    """
    return await send_email(to, subject, body, html_body)


async def send_security_notification(to: str, event: str, details: str):
    """Send security notification email"""
    subject = f"Security Alert: {event}"
    body = f"""
Hi,

We detected a security event on your account:

Event: {event}
Details: {details}

If this wasn't you, please change your password immediately and contact support.

Thanks,
LMS Team
    """
    html_body = f"""
    <html>
      <body>
        <h2 style="color: #f44336;">Security Alert</h2>
        <p><strong>Event:</strong> {event}</p>
        <p><strong>Details:</strong> {details}</p>
        <p>If this wasn't you, please change your password immediately.</p>
      </body>
    </html>
    """
    return await send_email(to, subject, body, html_body)
