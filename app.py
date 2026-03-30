from flask import Flask, render_template, request, jsonify, redirect
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# ===== EMAIL CONFIG =====
# Replace these with your actual Gmail address and App Password.
# To get an App Password: Google Account → Security → 2-Step Verification → App Passwords
SMTP_EMAIL    = "entangledprojectbydoremination@gmail.com"
SMTP_PASSWORD = "mejk cswu kacs zste"   # 16-char App Password, NOT your normal password


def send_confirmation_email(to_email, name, phone, student_class, seats):
    """Send booking confirmation email to the user."""

    royal_seats   = [s for s in seats if s[0] in "ABCDE"]
    warrior_seats = [s for s in seats if s[0] not in "ABCDE"]

    category_parts = []
    if royal_seats:
        category_parts.append(f"Royal: {', '.join(royal_seats)}")
    if warrior_seats:
        category_parts.append(f"Warrior: {', '.join(warrior_seats)}")
    category_str = " · ".join(category_parts) or "—"

    subject = "🎭 Booking Confirmed — ENTANGLED"

    html_body = f"""
    <html>
    <body style="font-family: Georgia, serif; background: #1a1a1a; color: #fff; padding: 40px;">
        <div style="max-width: 520px; margin: auto; background: #111; border: 1px solid #e8c46b;
                    border-radius: 16px; padding: 40px;">
            <h2 style="color: #e8c46b; text-align: center; margin-top: 0;">
                Booking Confirmed!
            </h2>
            <p style="text-align:center; color: #aaa; margin-top: -10px;">
                ENTANGLED — A Production of Doremi Nation
            </p>
            <hr style="border-color: #333; margin: 24px 0;">

            <table width="150%" cellpadding="8" style="font-size: 15px; border-collapse: collapse;">
                <tr>
                    <td style="color: #aaa; width: 40%;">Name</td>
                    <td style="color: #fff;">{name}</td>
                </tr>
                <tr style="border-top: 1px solid #222;">
                    <td style="color: #aaa;">Phone</td>
                    <td style="color: #fff;">{phone}</td>
                </tr>
                <tr style="border-top: 1px solid #222;">
                    <td style="color: #aaa;">Email</td>
                    <td style="color: #fff;">{to_email}</td>
                </tr>
                <tr style="border-top: 1px solid #222;">
                    <td style="color: #aaa;">Class</td>
                    <td style="color: #fff;">{student_class}</td>
                </tr>
                <tr style="border-top: 1px solid #222;">
                    <td style="color: #aaa;">Seats</td>
                    <td style="color: #e8c46b; font-weight: bold;">{', '.join(seats)}</td>
                </tr>
                <tr style="border-top: 1px solid #222;">
                    <td style="color: #aaa;">Category</td>
                    <td style="color: #fff;">{category_str}</td>
                </tr>
            </table>

            <hr style="border-color: #333; margin: 24px 0;">
            <p style="color: #aaa; font-size: 13px; text-align: center; line-height: 1.7;">
                Pembayaran akan diverifikasi oleh panitia.<br>
                Bila mana terjadi masalah, panitia akan segera menghubungi Anda via WhatsApp.<br><br>
                📍 LT.3 Aula Atisa Dipamkara &nbsp;|&nbsp; 🗓 13 April 2026
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Entangled Project <{SMTP_EMAIL}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] Sent confirmation to {to_email}")
    except Exception as e:
        # Don't crash the booking if email fails — just log it
        print(f"[EMAIL ERROR] Failed to send to {to_email}: {e}")


# ===== DATABASE =====
def get_db():
    return sqlite3.connect("tickets.db")

# ===== ADMIN =====
@app.route("/admin")
def admin():
    password = request.args.get("key")
    if password != "entangled123":
        return "Unauthorized"

    paid    = request.args.get("paid")
    payment = request.args.get("payment")

    db  = get_db()
    cur = db.cursor()

    query = """
        SELECT id, buyer_name, seat, phone, student_class, created_at, payment_file, paid, payment_method
        FROM tickets
        WHERE 1=1
    """
    params = []

    if paid in ["0", "1"]:
        query += " AND paid = ?"
        params.append(paid)

    if payment in ["cash", "transfer"]:
        query += " AND payment_method = ?"
        params.append(payment)

    cur.execute(query, params)
    data = cur.fetchall()
    db.close()

    return render_template("admin.html", data=data)


# ===== DELETE DATA ADMIN =====
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    password = request.args.get("key")
    if password != "entangled123":
        return "Unauthorized"

    db  = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM tickets WHERE id = ?", (id,))
    db.commit()
    db.close()

    return redirect("/admin?key=entangled123")


# ===== UPDATE PAID =====
@app.route("/update_paid/<int:id>", methods=["POST"])
def update_paid(id):
    password = request.args.get("key")
    if password != "entangled123":
        return "Unauthorized"

    data = request.get_json()
    paid = data.get("paid")

    if paid not in [0, 1]:
        return "Invalid", 400

    db  = get_db()
    cur = db.cursor()
    cur.execute("UPDATE tickets SET paid = ? WHERE id = ?", (paid, id))
    db.commit()
    db.close()

    return "", 204


@app.route("/update_payment/<int:id>", methods=["POST"])
def update_payment(id):
    password = request.args.get("key")
    if password != "entangled123":
        return "Unauthorized"

    data           = request.get_json()
    payment_method = data.get("payment_method")

    if payment_method not in ["cash", "transfer", ""]:
        return "Invalid", 400

    db  = get_db()
    cur = db.cursor()
    cur.execute("UPDATE tickets SET payment_method = ? WHERE id = ?", (payment_method or None, id))
    db.commit()
    db.close()

    return "", 204


# ===== HOME =====
@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")


# ===== BUY PAGE =====
@app.route("/buy", methods=["GET"])
def buy():
    return render_template("buy.html")


# ===== GET TAKEN SEATS =====
@app.route("/get-taken-seats")
def get_taken_seats():
    db  = get_db()
    cur = db.cursor()
    cur.execute("SELECT seat FROM tickets")
    seats = [row[0] for row in cur.fetchall()]
    db.close()
    return jsonify(seats)


# ===== SAVE BOOKING =====
@app.route("/save-booking", methods=["POST"])
def save_booking():

    name           = request.form.get("name")
    phone          = request.form.get("phone")
    email          = request.form.get("email")          # ← new
    student_class  = request.form.get("student_class")
    payment_method = request.form.get("payment_method")
    seats          = request.form.getlist("seats")

    file     = request.files.get("payment")
    filename = None

    if file:
        os.makedirs("static/uploads", exist_ok=True) 
        
        ext          = os.path.splitext(file.filename)[1]
        raw_filename = f"{name}_{student_class}{ext}"
        filename     = secure_filename(raw_filename)
        save_path    = os.path.join("static/uploads", filename)
        file.save(save_path)

    db  = get_db()
    cur = db.cursor()

    try:
        for seat in seats:
            cur.execute("""
                INSERT INTO tickets
                (buyer_name, seat, phone, student_class, created_at, payment_file, payment_method, paid)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                name,
                seat,
                phone,
                student_class,
                datetime.now().isoformat(),
                filename,
                payment_method
            ))

        db.commit()

    except sqlite3.IntegrityError:
        db.rollback()
        db.close()
        return jsonify({"status": "error", "message": "Seat already taken!"}), 400

    db.close()

    except Exception as e:
    db.rollback()
    db.close()
    print("ERROR SAVE BOOKING:", e)  
    return jsonify({"status": "error", "message": str(e)}), 500

    # Send confirmation email (non-blocking — booking already saved above)
    if email:
        send_confirmation_email(email, name, phone, student_class, seats)

    return jsonify({"status": "success"})


# ===== RUN =====
if __name__ == "__main__":
    app.run(debug=True)
