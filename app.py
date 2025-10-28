from flask import Flask, render_template, request, redirect, session, url_for, make_response
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "change-this-to-any-random-secret"  # needed for session

# ---- DB config (EDIT ONLY THESE 4 IF NEEDED) ----
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "2085965411Pt$"
DB_NAME = "grandguard.db"   # keep exactly this; your schema is named grandguard.db
# -------------------------------------------------

def get_db():
    """Create a connection per request. No app-start crash if creds are wrong."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
        )
        return conn
    except Error as e:
        print(f"DB connect error: {e}")
        return None

@app.route("/")
def home():
    # your friend’s login page (index.html in templates/)
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    # Called by your existing script.js (fetch -> /login)
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return make_response("Missing credentials", 400)

    conn = get_db()
    if conn is None:
        # Don’t silently fall back to Guest; tell the front-end it failed
        return make_response("DB connection failed", 500)

    try:
        cur = conn.cursor(dictionary=True)
        # columns in your table: user_id, name, email, role, created_at, password
        cur.execute(
            "SELECT name, role FROM users WHERE email=%s AND password=%s",
            (email, password),
        )
        user = cur.fetchone()
        cur.close()
        conn.close()
    except Error as e:
        print(f"Query error: {e}")
        return make_response("DB query failed", 500)

    if not user:
        # invalid login
        return make_response("Invalid email or password", 401)

    # success: persist to session, so dashboard can show PI/Admin/etc.
    session["user"] = {"name": user["name"], "role": user["role"], "email": email}

    # Your current script.js checks for text like “Welcome”, so return that
    return "Welcome"

@app.route("/dashboard")
def dashboard():
    u = session.get("user")
    if not u:
        # no login yet -> keep simple
        return render_template("dashboard.html", name="User", role="Guest")
    return render_template("dashboard.html", name=u["name"], role=u["role"])

@app.route("/policies/university")
def university_policies():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM policies WHERE policy_level = 'University'")
        policies = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("policies_university.html", policies=policies)
    except Exception as e:
        return f"Database error: {e}"

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True, port=8000)
