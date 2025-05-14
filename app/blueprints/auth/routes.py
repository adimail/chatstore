from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlsplit
from . import auth_bp
from app.services import auth_service
from app.models import User


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember_me") is not None

        user = auth_service.authenticate_user(email, password)

        if user:
            login_user(user, remember=remember)
            flash("Login successful!", "success")
            next_page = request.args.get("next")
            if not next_page or urlsplit(next_page).netloc != "":
                next_page = url_for("web.index")
            return redirect(next_page)
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html.jinja2", title="Sign In")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("web.index"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        password2 = request.form.get("password2")

        if not name or not email or not password or not password2:
            flash("All fields are required!", "warning")
            return render_template("auth/register.html.jinja2", title="Register")

        if password != password2:
            flash("Passwords do not match!", "danger")
            return render_template("auth/register.html.jinja2", title="Register")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email address already registered.", "warning")
            return render_template("auth/register.html.jinja2", title="Register")

        try:
            auth_service.create_user(name, email, password)
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as e:
            flash(str(e), "warning")
        except Exception as e:
            flash("An error occurred during registration.", "danger")
            print(e)
        return render_template("auth/register.html.jinja2", title="Register")

    return render_template("auth/register.html.jinja2", title="Register")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("web.index"))
