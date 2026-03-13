from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User
import qrcode
import os
from datetime import datetime
from app.models import QRCode
from flask import current_app


auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="../templates"
)

@auth_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))
    return render_template("home.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("User already exists", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password,
            role="user"
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful", "success")

            if user.role == "admin":
                return redirect(url_for("auth.admin_dashboard"))
            else:
                return redirect(url_for("auth.dashboard"))

        flash("Invalid email or password", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "user":
        return redirect(url_for("auth.admin_dashboard"))
    return render_template("dashboard.html")

@auth_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("auth.dashboard"))

    users = User.query.all()
    return render_template("admin_dashboard.html", users=users)

@auth_bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate_qr():
    if current_user.role != "user":
        return redirect(url_for("auth.admin_dashboard"))

    qr_image = None

    if request.method == "POST":
        data = request.form.get("data")

        if not data:
            flash("Please enter text or URL", "danger")
            return redirect(url_for("auth.generate_qr"))

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"qr_{current_user.id}_{timestamp}.png"

        qr_path = os.path.join("static", "qrcodes", filename)

        img = qrcode.make(data)
        img.save(qr_path)

        qr = QRCode(
            data=data,
            image_path=qr_path,
            user_id=current_user.id
        )

        db.session.add(qr)
        db.session.commit()

        qr_image = qr_path
        flash("QR Code generated successfully", "success")

    return render_template("generate.html", qr_image=qr_image)

@auth_bp.route("/history")
@login_required
def history():
    if current_user.role != "user":
        return redirect(url_for("auth.admin_dashboard"))

    qrcodes = QRCode.query.filter_by(user_id=current_user.id).all()
    return render_template("history.html", qrcodes=qrcodes)

@auth_bp.route("/delete/<int:qr_id>")
@login_required
def delete_qr(qr_id):
    qr = QRCode.query.get_or_404(qr_id)

    if qr.user_id != current_user.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for("auth.history"))

    # Delete image file
    if os.path.exists(qr.image_path):
        os.remove(qr.image_path)

    db.session.delete(qr)
    db.session.commit()

    flash("QR Code deleted successfully", "success")
    return redirect(url_for("auth.history"))

@auth_bp.route("/admin/user/<int:user_id>/qrcodes")
@login_required
def admin_user_qrcodes(user_id):
    if current_user.role != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("auth.dashboard"))

    user = User.query.get_or_404(user_id)
    qrcodes = QRCode.query.filter_by(user_id=user.id).all()

    return render_template(
        "admin_user_qrcodes.html",
        user=user,
        qrcodes=qrcodes
    )
