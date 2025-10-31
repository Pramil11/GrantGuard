from flask import Flask, render_template, request, redirect, session, url_for, make_response
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
app.secret_key = "change-this-to-any-random-secret"  # needed for session

# ---- DB config (use environment variables in deployment) ----
# For Render PostgreSQL, use DATABASE_URL format or individual vars
DATABASE_URL = os.getenv("DATABASE_URL")  # Render provides this

# Fallback to individual vars if DATABASE_URL not provided
if DATABASE_URL:
    # Parse DATABASE_URL: postgresql://user:pass@host:port/dbname
    import urllib.parse as urlparse
    urlparse.uses_netloc.append("postgresql")
    url = urlparse.urlparse(DATABASE_URL)
    DB_HOST = url.hostname
    DB_USER = url.username
    DB_PASS = url.password
    DB_NAME = url.path[1:]  # Remove leading /
    DB_PORT = url.port or 5432
else:
    DB_HOST = os.getenv("PGHOST", "localhost")
    DB_USER = os.getenv("PGUSER", "postgres")
    DB_PASS = os.getenv("PGPASSWORD", "")
    DB_NAME = os.getenv("PGDATABASE", "grandguard")
    DB_PORT = int(os.getenv("PGPORT", "5432"))
# ------------------------------------------------------------

def get_db():
    """Create a connection per request. No app-start crash if creds are wrong."""
    try:
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = psycopg2.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                port=DB_PORT,
            )
        return conn
    except Exception as e:
        print(f"DB connect error: {e}")
        return None

def init_db_if_needed():
    """Initialize database schema if tables don't exist"""
    conn = get_db()
    if conn is None:
        print("Warning: Could not connect to database. Schema initialization skipped.")
        return
    
    try:
        cur = conn.cursor()
        
        # Read and execute PostgreSQL schema
        schema_file = os.path.join(os.path.dirname(__file__), "schema_postgresql.sql")
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            cur.execute(schema_sql)
            conn.commit()
            print("✓ Database schema initialized")
        else:
            print(f"Warning: Schema file {schema_file} not found")
        
        cur.close()
    except Exception as e:
        print(f"DB init error: {e}")
        conn.rollback()
    finally:
        conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return make_response("Missing credentials", 400)

    conn = get_db()
    if conn is None:
        return make_response("DB connection failed", 500)

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT name, role FROM users WHERE email=%s AND password=%s",
            (email, password),
        )
        user = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Query error: {e}")
        return make_response("DB query failed", 500)

    if not user:
        return make_response("Invalid email or password", 401)

    session["user"] = {"name": user["name"], "role": user["role"], "email": email}
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
        # PostgreSQL uses ON CONFLICT instead of ON DUPLICATE KEY UPDATE
        cur.execute(
            """
            INSERT INTO users (name, email, role, password)
            VALUES (%s, %s, 'PI', %s)
            ON CONFLICT (email) DO UPDATE SET name=EXCLUDED.name
            """,
            (full_name, email, password),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"DB insert user error: {e}")
        conn.rollback()
        return make_response(f"DB insert failed: {e}", 500)
    finally:
        conn.close()

    session["user"] = {"name": full_name, "role": "PI", "email": email}
    return "Signed up"

@app.route("/dashboard")
def dashboard():
    u = session.get("user")
    if not u:
        return render_template("dashboard.html", name="User", role="Guest", awards=[])

    awards = []
    conn = get_db()
    if conn is not None:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT award_id, title, sponsor_type, amount, start_date, end_date, status, created_at FROM awards WHERE created_by_email=%s ORDER BY created_at DESC",
                (u["email"],),
            )
            awards = cur.fetchall()
            cur.close()
        except Exception as e:
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
    sponsor = None
    sponsor_type = request.form.get("sponsor_type", "").strip()
    department = request.form.get("department", "").strip()
    college = request.form.get("college", "").strip()
    contact_email = request.form.get("contact_email", "").strip()
    amount = request.form.get("amount", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()
    abstract = request.form.get("abstract", "").strip()
    keywords = request.form.get("keywords", "").strip()
    collaborators = request.form.get("collaborators", "").strip()
    budget_personnel = request.form.get("budget_personnel", "").strip() or None
    budget_equipment = request.form.get("budget_equipment", "").strip() or None
    budget_travel = request.form.get("budget_travel", "").strip() or None
    budget_materials = request.form.get("budget_materials", "").strip() or None

    if not title or not sponsor_type or not amount or not start_date or not end_date:
        return make_response("Missing required fields", 400)

    conn = get_db()
    if conn is None:
        return make_response("DB connection failed", 500)
    
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO awards (
              created_by_email, title, sponsor, sponsor_type,
              department, college, contact_email,
              amount, start_date, end_date,
              abstract, keywords, collaborators,
              budget_personnel, budget_equipment, budget_travel, budget_materials
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                u["email"], title, sponsor, sponsor_type or None,
                department or None, college or None, contact_email or None,
                amount, start_date, end_date,
                abstract or None, keywords or None, collaborators or None,
                budget_personnel, budget_equipment, budget_travel, budget_materials,
            ),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"DB insert award error: {e}")
        conn.rollback()
        return make_response(f"DB insert failed: {e}", 500)
    finally:
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/subawards")
def subawards():
    u = session.get("user")
    if not u:
        return redirect(url_for("home"))
    return render_template("subawards.html")

@app.route("/settings")
def settings():
    u = session.get("user")
    if not u:
        return redirect(url_for("home"))
    return render_template("settings.html")

@app.route("/profile")
def profile():
    u = session.get("user")
    if not u:
        return redirect(url_for("home"))
    return render_template("profile.html")

@app.route("/policies/university")
def university_policies():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM policies WHERE policy_level = 'University'")
        policies = cur.fetchall()
        cur.close()
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

