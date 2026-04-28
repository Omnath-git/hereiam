# utils/email_otp.py
# ⭐ नई फाइल बनाएं

import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
# ⚠️ PRODUCTION SETTINGS - अपनी ईमेल सेटिंग्स डालें
SMTP_CONFIG = {
    'server': os.getenv("MAIL_SERVER") or 'smtp.gmail.com',
    'port': int(os.getenv("MAIL_PORT", 587)),
    'email': os.getenv("MAIL_USERNAME"),
    'password': os.getenv("MAIL_PASSWORD"),
    'use_tls': True,
}


def generate_otp(length=6):
    """6-digit OTP जनरेट करें"""
    return ''.join(random.choices(string.digits, k=length))

def send_email_otp(to_email, otp, purpose="verify"):
    """ईमेल के द्वारा OTP भेजें"""
    try:
        subject = ""
        body = ""
        
        if purpose == "verify":
            subject = "🔐 HereIAM - Email Verification OTP"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 500px; margin: auto; background: #f9fafb; border-radius: 16px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 24px;">
                        <h2 style="color: #8b5cf6; margin: 0;">HereIAM</h2>
                        <p style="color: #64748b; margin: 4px 0 0;">Email Verification</p>
                    </div>
                    
                    <div style="background: white; border-radius: 12px; padding: 24px; text-align: center;">
                        <p style="color: #374151; font-size: 15px; margin: 0 0 16px;">
                            Your verification code is:
                        </p>
                        <div style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; font-size: 36px; font-weight: 800; letter-spacing: 8px; padding: 16px 24px; border-radius: 12px; display: inline-block; margin: 0 0 16px;">
                            {otp}
                        </div>
                        <p style="color: #64748b; font-size: 13px; margin: 0;">
                            This code will expire in 5 minutes.<br>
                            Do not share this code with anyone.
                        </p>
                    </div>
                    
                    <p style="color: #94a3b8; font-size: 12px; text-align: center; margin: 20px 0 0;">
                        If you didn't request this, please ignore this email.
                    </p>
                </div>
            </body>
            </html>
            """
        elif purpose == "login":
            subject = "🔑 HereIAM - Login OTP"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 500px; margin: auto; background: #f9fafb; border-radius: 16px; padding: 30px;">
                    <h2 style="color: #8b5cf6; text-align: center;">Login Verification</h2>
                    <div style="background: white; border-radius: 12px; padding: 24px; text-align: center;">
                        <p style="color: #374151;">Your login OTP is:</p>
                        <div style="font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #8b5cf6; padding: 16px;">{otp}</div>
                        <p style="color: #64748b; font-size: 13px;">Expires in 5 minutes</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"HereIAM <{SMTP_CONFIG['email']}>"
        msg['To'] = to_email
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port']) as server:
            if SMTP_CONFIG['use_tls']:
                server.starttls()
            server.login(SMTP_CONFIG['email'], SMTP_CONFIG['password'])
            server.send_message(msg)      
        
        return True
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False
