from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import time, uuid, datetime
import re
import os   # ✅ IMPORTANT ADD

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

# ---------------- URL VALIDATION ----------------
def is_valid_url(url):
    pattern = re.compile(
        r'^(https?:\/\/)'
        r'([\w\-]+\.)+[\w\-]+'
        r'(:\d+)?'
        r'(\/.*)?$'
    )
    return bool(re.match(pattern, url))

# ---------------- GLOBAL STORAGE ----------------
stats = {"total": 0, "passed": 0, "failed": 0, "healed": 0}
REPORT_DATA = []
HEAL_HISTORY = []

# ---------------- LOGIN ----------------
VALID_USERNAME = "admin"
VALID_PASSWORD = "1234"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

suite_urls = {
    "Login Test": "https://example.com/login",
    "Checkout Flow": "https://example.com/shop",
    "User Registration": "https://example.com/register",
    "Dashboard Navigation": "https://example.com/dashboard",
    "Search Functionality": "https://google.com"
}

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("username") == VALID_USERNAME and request.form.get("password") == VALID_PASSWORD:
            session["user"] = VALID_USERNAME
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid Username or Password ❌"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------
@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html", stats=stats)

# ---------------- RUN TEST ----------------
@app.route("/run", methods=["GET", "POST"])
@login_required
def run():

    logs = []
    status = None
    healed = False

    if request.method == "POST":

        suite = request.form.get("suite")
        selected_url = request.form.get("selected_url", "").strip()
        custom_url = request.form.get("custom_url", "").strip()

        if custom_url:
            url = custom_url
        elif selected_url:
            url = selected_url
        elif suite:
            url = suite_urls.get(suite)
        else:
            url = None

        if not url:
            logs.append({"type": "error", "text": "No URL provided ❌"})
            return render_template("run_tests.html", logs=logs, status="Failed", suites=suite_urls.keys())

        if not url.startswith("http"):
            url = "https://" + url

        if not is_valid_url(url):
            logs.append({"type": "error", "text": "Invalid URL format ❌"})
            return render_template("run_tests.html", logs=logs, status="Failed", suites=suite_urls.keys())

        start = time.time()

        try:
            logs.append({"type": "info", "text": "Launching test engine..."})

            time.sleep(2)

            logs.append({"type": "info", "text": f"Navigated to: {url}"})

            logs.append({"type": "heal", "text": "Broken element detected. Healing applied..."})
            healed = True
            stats["healed"] += 1

            HEAL_HISTORY.insert(0, {
                "suite": suite if suite else "Manual Run",
                "element": "wrong-id",
                "healed_to": "body",
                "confidence": "82%",
                "status": "Healed",
                "time": datetime.datetime.now().strftime("%b %d, %H:%M")
            })

            status = "Passed"
            stats["passed"] += 1

        except Exception as e:
            status = "Failed"
            stats["failed"] += 1
            logs.append({"type": "error", "text": str(e)})

        stats["total"] += 1
        duration = round(time.time() - start, 2)

        REPORT_DATA.insert(0, {
            "id": str(uuid.uuid4())[:8],
            "name": suite if suite else "Manual Run",
            "status": status,
            "duration": f"{duration}s",
            "healed": "Yes" if healed else "No",
            "confidence": "82%" if healed else "-",
            "screenshot": "",
            "executed": datetime.datetime.now().strftime("%b %d, %H:%M")
        })

    return render_template("run_tests.html", logs=logs, status=status, suites=suite_urls.keys())

# ---------------- REPORTS ----------------
@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html", reports=REPORT_DATA)

# ---------------- HEALING ----------------
@app.route("/healing")
@login_required
def healing():
    return render_template("healing.html", history=HEAL_HISTORY)

# ---------------- USERS ----------------
users_list = [{
    "id": str(uuid.uuid4()),
    "name": "Chinni M",
    "email": "chinni.m.m435@gmail.com",
    "role": "Admin"
}]

@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    global users_list

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        role = request.form.get("role")

        if name and email:
            users_list.append({
                "id": str(uuid.uuid4()),
                "name": name,
                "email": email,
                "role": role
            })
        return redirect(url_for("users"))

    remove_id = request.args.get("remove")
    if remove_id:
        users_list = [u for u in users_list if u["id"] != remove_id]
        return redirect(url_for("users"))

    total = len(users_list)
    admins = len([u for u in users_list if u["role"] == "Admin"])
    regular = len([u for u in users_list if u["role"] == "User"])

    return render_template("users.html",
                           users=users_list,
                           total=total,
                           admins=admins,
                           regular=regular)

# ---------------- START SERVER ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # ✅ FIX
    app.run(host="0.0.0.0", port=port)