import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3

# EMAIL CONFIG 
EMAIL_ADDRESS = "creditcard794@gmail.com"
EMAIL_PASSWORD = "xvth mknd yirc zrhm"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


# DB CONNECTION
def get_db():
    return sqlite3.connect("customers.db")

def send_otp_email(to_email, otp):
    subject = "🔐 Verify Your Email - OTP"

    body = f"""
Dear User,

Your OTP for email verification is:

🔑 OTP: {otp}

This OTP is valid for a short time.
Please do not share it with anyone.

— Credit Card Fraud Detection System
"""

    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

# GET USER EMAIL 
def get_user_email(customer_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT email FROM customers WHERE customer_id=?",
        (customer_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return None


# SEND FRAUD EMAIL 
def send_fraud_email(to_email, amount, txn_datetime):
    if not to_email:
        print("❌ No email found for user")
        return

    subject = "🚨 Fraud Alert: Suspicious Transaction Detected"

    body = f"""
Dear Customer,

⚠️ A suspicious transaction has been detected on your account.

Transaction Details:
Amount: ₹{amount}
Date & Time: {txn_datetime}

If this transaction was NOT done by you:
• Immediately block your card
• Change your password
• Contact customer support

— Fraud Detection System
"""

    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Fraud alert email sent successfully")

    except Exception as e:
        print("❌ Email sending failed:", e)