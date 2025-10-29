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

def init_db_if_needed():
    conn = get_db()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        # awards table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS awards (
                award_id INT AUTO_INCREMENT PRIMARY KEY,
                created_by_email VARCHAR(255) NOT NULL,
                title VARCHAR(255) NOT NULL,
                sponsor VARCHAR(255) NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status VARCHAR(50) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
            """
        )
        # users table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                role ENUM('PI','Admin','Finance') NOT NULL DEFAULT 'PI',
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
            """
        )
        conn.commit()
        cur.close()
    except Error as e:
        print(f"DB init error: {e}")
    finally:
        conn.close()

# Flask 3+ removed before_first_request; initialize schema at startup instead

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

@app.route("/signup", methods=["POST"])
def signup():
    first = request.form.get("firstName", "").strip()
    last = request.form.get("lastName", "").strip()
    email = request.form.get("email", "").strip() or request.form.get("signupEmail", "").strip()
    password = request.form.get("password", "").strip() or request.form.get("signupPassword", "").strip()

    if not first or not last or not email or not password:
        return make_response("Missing required fields", 400)

    full_name = f"{first} {last}".strip()

    conn = get_db()
    if conn is None:
        return make_response("DB connection failed", 500)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (name, email, role, password)
            VALUES (%s, %s, 'PI', %s)
            ON DUPLICATE KEY UPDATE name=VALUES(name)
            """,
            (full_name, email, password),
        )
        conn.commit()
        cur.close()
    except Error as e:
        print(f"DB insert user error: {e}")
        return make_response("DB insert failed", 500)
    finally:
        conn.close()

    # Auto-login after signup
    session["user"] = {"name": full_name, "role": "PI", "email": email}
    return "Signed up"

@app.route("/dashboard")
def dashboard():
    u = session.get("user")
    if not u:
        # no login yet -> keep simple
        return render_template("dashboard.html", name="User", role="Guest", awards=[])

    # fetch awards created by this user
    awards = []
    conn = get_db()
    if conn is not None:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT award_id, title, sponsor, amount, start_date, end_date, status, created_at FROM awards WHERE created_by_email=%s ORDER BY created_at DESC",
                (u["email"],),
            )
            awards = cur.fetchall()
            cur.close()
        except Error as e:
            print(f"DB fetch awards error: {e}")
        finally:
            conn.close()

    return render_template("dashboard.html", name=u["name"], role=u["role"], awards=awards)

@app.route("/awards/new")
def awards_new():
    u = session.get("user")
    if not u:
        return redirect(url_for("home"))
    return render_template("awards_new.html")

@app.route("/awards", methods=["POST"])
def awards_create():
    u = session.get("user")
    if not u:
        return redirect(url_for("home"))

    title = request.form.get("title", "").strip()
    sponsor = request.form.get("sponsor", "").strip()
    amount = request.form.get("amount", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()

    if not title or not sponsor or not amount or not start_date or not end_date:
        return make_response("Missing required fields", 400)

    conn = get_db()
    if conn is None:
        return make_response("DB connection failed", 500)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO awards (created_by_email, title, sponsor, amount, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (u["email"], title, sponsor, amount, start_date, end_date),
        )
        conn.commit()
        cur.close()
    except Error as e:
        print(f"DB insert award error: {e}")
        return make_response("DB insert failed", 500)
    finally:
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/subawards")
def subawards():
    u = session.get("user")
    if not u:
        return redirect(url_for("home"))
    # Placeholder for now
    return render_template("placeholder.html", title="Subawards")

@app.route("/settings")
def settings():
    u = session.get("user")
    if not u:
        return redirect(url_for("home"))
    return render_template("placeholder.html", title="Settings")

@app.route("/profile")
def profile():
    u = session.get("user")
    if not u:
        return redirect(url_for("home"))
    return render_template("placeholder.html", title="Profile")

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
    init_db_if_needed()
    app.run(debug=True, port=8000)
