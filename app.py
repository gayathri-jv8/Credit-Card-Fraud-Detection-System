from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import sqlite3
import pickle
import random
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from email_utils import send_fraud_email, get_user_email, send_otp_email

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database connection
def get_db():
    return sqlite3.connect("customers.db")

# Load ML model
with open("fraud_model.pkl", "rb") as f:
    saved = pickle.load(f)

model = saved["model"]
location_encoder = saved["location_encoder"]
purpose_encoder = saved["purpose_encoder"]

feature_columns = ["amount", "location", "purpose", "day", "month", "hour"]


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        customer_id = request.form["customer_id"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = generate_password_hash(request.form["password"])

        otp = str(random.randint(100000, 999999))

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO customers 
                (customer_id, email, phone, password, otp, is_verified)
                VALUES (?,?,?,?,?,0)""",
                (customer_id, email, phone, password, otp)
            )
            conn.commit()
            conn.close()

            send_otp_email(email, otp)
            session["verify_email"] = email
            return redirect(url_for("verify_otp"))
        except:
            return "⚠️ Email or Customer ID already exists"

    return render_template("register.html")

# VERIFY OTP
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "verify_email" not in session:
        return redirect(url_for("register"))

    if request.method == "POST":
        user_otp = request.form["otp"]
        email = session["verify_email"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT otp FROM customers WHERE email=?", (email,))
        record = cursor.fetchone()

        if record and record[0] == user_otp:
            cursor.execute(
                "UPDATE customers SET is_verified=1, otp=NULL WHERE email=?",
                (email,)
            )
            conn.commit()
            conn.close()
            session.pop("verify_email")
            return redirect(url_for("login"))

        conn.close()
        return "❌ Invalid OTP"

    return render_template("verify_otp.html")

# LOGIN
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        customer_id = request.form["customer_id"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM customers WHERE customer_id=? AND is_verified=1",
            (customer_id,)
        )
        customer = cursor.fetchone()
        conn.close()

        if customer and check_password_hash(customer[4], password):
            session["customer"] = customer_id
            return redirect(url_for("dashboard"))

        return "❌ Invalid credentials"

    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "customer" not in session:
        return redirect(url_for("login"))

    result = None
    txn_datetime = None

    if request.method == "POST":
        try:

            amount = float(request.form["amount"])
            location = request.form["location"]
            purpose = request.form["purpose"]
            date_input = request.form["txn_date"]
            time_input = request.form["txn_time"]

            dt_obj = datetime.strptime(f"{date_input} {time_input}", "%Y-%m-%d %H:%M")
            txn_datetime = dt_obj.strftime("%d/%m/%Y %H:%M")
            day, month, hour = dt_obj.day, dt_obj.month, dt_obj.hour

            location_encoded = location_encoder.transform([location])[0] if location in location_encoder.classes_ else -1
            purpose_encoded = purpose_encoder.transform([purpose])[0] if purpose in purpose_encoder.classes_ else -1

            if location_encoded == -1 or purpose_encoded == -1:
                result = "🚨 FRAUD TRANSACTION "
                email = get_user_email(session["customer"])
                send_fraud_email(email, amount, txn_datetime)
            else:

                input_df = pd.DataFrame(
                    [[amount, location_encoded, purpose_encoded, day, month, hour]],
                    columns=["amount", "location", "purpose", "day", "month", "hour"]
                )

                prediction = model.predict(input_df)
                if prediction[0] == 1:
                    result = "🚨 FRAUD TRANSACTION"
                    email = get_user_email(session["customer"])
                    send_fraud_email(email, amount, txn_datetime)
                else:
                    result = "✅ VALID TRANSACTION"

        except Exception as e:
            result = f"⚠️ Error: {e}"

    return render_template("dashboard.html", result=result, txn_datetime=txn_datetime)

# LOGOUT
@app.route("/logout")
def logout():
    session.pop("customer", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
