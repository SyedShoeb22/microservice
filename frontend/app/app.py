import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

USER_API = os.getenv("USER_API_URL", "http://user-service:5001")
PRODUCT_API = os.getenv("PRODUCT_API_URL", "http://product-service:5002")
ORDER_API = os.getenv("ORDER_API_URL", "http://order-service:5003")
SECRET_KEY = os.getenv("SECRET_KEY", "frontendsecret")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = SECRET_KEY

def is_logged_in():
    return session.get("user") is not None

@app.route("/")
def index():
    try:
        r = requests.get(f"{PRODUCT_API}/api/products", timeout=5)
        products = r.json() if r.ok else []
    except Exception:
        products = []
    return render_template("index.html", products=products, logged_in=is_logged_in())

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        payload = {
            "username": request.form.get("username", "").strip(),
            "password": request.form.get("password", ""),
            "email": request.form.get("email", "")
        }
        try:
            r = requests.post(f"{USER_API}/api/user/register", json=payload, timeout=5)
            if r.ok:
                flash("Registration successful. Please login.", "success")
                return redirect(url_for("login"))
            else:
                flash(r.json().get("error", "Registration failed"), "danger")
        except Exception as e:
            flash(f"Registration service error: {e}", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        payload = {
            "username": request.form.get("username", "").strip(),
            "password": request.form.get("password", "")
        }
        try:
            r = requests.post(f"{USER_API}/api/user/login", json=payload, timeout=5)
            if r.ok:
                data = r.json()
                session["user"] = {"id": data["id"], "username": data["username"]}
                flash("Logged in!", "success")
                return redirect(url_for("index"))
            else:
                flash(r.json().get("error", "Invalid credentials"), "danger")
        except Exception as e:
            flash(f"Login service error: {e}", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("index"))

@app.post("/buy/<int:product_id>")
def buy(product_id: int):
    if not is_logged_in():
        flash("Please login to place orders.", "warning")
        return redirect(url_for("login"))
    payload = {
        "user_id": session["user"]["id"],
        "items": [{"product_id": product_id, "qty": 1}]
    }
    try:
        r = requests.post(f"{ORDER_API}/api/orders", json=payload, timeout=5)
        if r.ok:
            flash("Order placed!", "success")
        else:
            flash(r.json().get("error", "Order failed"), "danger")
    except Exception as e:
        flash(f"Order service error: {e}", "danger")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host=os.getenv("FLASK_RUN_HOST", "0.0.0.0"), port=5000, debug=False)
