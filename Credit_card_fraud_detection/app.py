from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import sqlite3
import pickle
import random
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from email_utils import send_fraud_email, get_user_email, send_otp_email


app = Flask(__name__)
app.secret_key = "supersecretkey"

def get_db():
    return sqlite3.connect("customers.db")

# LOAD ML
with open("fraud_model.pkl", "rb") as f:
    model = pickle.load(f)


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        customer_id = request.form["customer_id"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = generate_password_hash(request.form["password"])

        otp = str(random.randint(100000, 999999))
        otp_time = datetime.now().isoformat()

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

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "verify_email" not in session:
        return redirect(url_for("register"))

    if request.method == "POST":
        user_otp = request.form["otp"]
        email = session["verify_email"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT otp FROM customers WHERE email=?",
            (email,)
        )
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
        amount = float(request.form["amount"])
        location = request.form["location"]
        date_input = request.form["txn_date"]
        time_input = request.form["txn_time"]
        dt_obj = datetime.strptime(f"{date_input} {time_input}", "%Y-%m-%d %H:%M")
        txn_datetime = dt_obj.strftime("%d/%m/%y %H:%M")

        try:
            location_encoded = location_encoder.transform([location])[0]
            unknown_location = False
        except:
            location_encoded = -1
            unknown_location = True

        email = get_user_email(session["customer"])

        if unknown_location:
            # Generate and send OTP for unknown location
            otp = str(random.randint(100000, 999999))
            session["txn_otp"] = otp
            session["pending_txn"] = {
                "amount": amount,
                "location": location,
                "txn_datetime": txn_datetime
            }
            send_otp_email(email, otp)
            return render_template("verify_txn_otp.html", txn_datetime=txn_datetime, amount=amount, location=location)

        prediction = model.predict([[amount, location_encoded]])

        if prediction[0] == -1:
            result = "🚨 FRAUD TRANSACTION"
            send_fraud_email(email, amount, txn_datetime)
        else:
            result = "✅ VALID TRANSACTION"
            # Send notification email for valid transaction
            send_fraud_email(email, amount, txn_datetime, notify_only=True)

    return render_template("dashboard.html", result=result, txn_datetime=txn_datetime)

# New route for verifying transaction OTP
@app.route("/verify-txn-otp", methods=["POST"])
def verify_txn_otp():
    user_otp = request.form["otp"]
    if "txn_otp" not in session or "pending_txn" not in session:
        return redirect(url_for("dashboard"))

    if user_otp == session["txn_otp"]:
        txn = session.pop("pending_txn")
        session.pop("txn_otp")
        email = get_user_email(session["customer"])
        # Send notification email after successful transaction
        send_fraud_email(email, txn["amount"], txn["txn_datetime"], notify_only=True)
        result = "✅ VALID TRANSACTION (OTP Verified)"
        return render_template("dashboard.html", result=result, txn_datetime=txn["txn_datetime"])
    else:
        return "❌ Invalid OTP"

# PREDICT 
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    amount = data["amount"]
    location = data["location"]
    email = data["email"]

    location_encoded = location_encoder.transform([location])[0]
    prediction = model.predict([[amount, location_encoded]])

    if prediction[0] == -1:
        send_fraud_email(email, amount, "API Transaction")
        return jsonify({"status": "fraud"})

    return jsonify({"status": "safe"})

# LOGOUT 
@app.route("/logout")
def logout():
    session.pop("customer", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
