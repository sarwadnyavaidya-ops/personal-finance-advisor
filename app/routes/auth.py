from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.utils.helpers import seed_default_categories
from app.services.demo_service import DemoService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        preferred_currency = request.form.get("preferred_currency", "USD")
        monthly_income_str = request.form.get("monthly_income", "0").strip()

        # Validation
        if not full_name or not email or not password:
            flash("All required fields must be completed.", "danger")
            return render_template("auth/register.html")

        if "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "danger")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        try:
            monthly_income = float(monthly_income_str) if monthly_income_str else 0.0
            if monthly_income < 0:
                monthly_income = 0.0
        except ValueError:
            monthly_income = 0.0

        user = User(
            full_name=full_name,
            email=email,
            preferred_currency=preferred_currency,
            monthly_income=monthly_income
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Ensure default categories exist
        seed_default_categories(db.session)

        login_user(user)
        flash("Welcome to Personal Finance Advisor Bot! Your account has been created.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.full_name}!", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            full_name = request.form.get("full_name", "").strip()
            preferred_currency = request.form.get("preferred_currency", "USD")
            monthly_income_str = request.form.get("monthly_income", "0").strip()
            monthly_savings_str = request.form.get("monthly_savings_target", "0").strip()
            emergency_fund_str = request.form.get("emergency_fund_target", "0").strip()
            goals_summary = request.form.get("financial_goals_summary", "").strip()

            if not full_name:
                flash("Full name cannot be empty.", "danger")
                return redirect(url_for("auth.profile"))

            try:
                current_user.full_name = full_name
                current_user.preferred_currency = preferred_currency
                current_user.monthly_income = max(0.0, float(monthly_income_str or 0.0))
                current_user.monthly_savings_target = max(0.0, float(monthly_savings_str or 0.0))
                current_user.emergency_fund_target = max(0.0, float(emergency_fund_str or 0.0))
                current_user.financial_goals_summary = goals_summary
                db.session.commit()
                flash("Profile updated successfully.", "success")
            except ValueError:
                flash("Invalid numeric value entered for financial targets.", "danger")

        elif action == "change_password":
            current_pass = request.form.get("current_password", "")
            new_pass = request.form.get("new_password", "")
            confirm_new_pass = request.form.get("confirm_new_password", "")

            if not current_user.check_password(current_pass):
                flash("Current password entered is incorrect.", "danger")
            elif len(new_pass) < 6:
                flash("New password must be at least 6 characters.", "danger")
            elif new_pass != confirm_new_pass:
                flash("New passwords do not match.", "danger")
            else:
                current_user.set_password(new_pass)
                db.session.commit()
                flash("Password changed successfully.", "success")

        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", user=current_user)


@auth_bp.route("/demo/load/<scenario>")
def load_scenario(scenario):
    """Loads realistic sample data for one of the four required scenarios."""
    valid_scenarios = ["salaried", "student", "freelancer", "household"]
    if scenario not in valid_scenarios:
        scenario = "salaried"

    user = DemoService.setup_demo_user(scenario)
    login_user(user)
    scenario_names = {
        "salaried": "Salaried Professional",
        "student": "College Student",
        "freelancer": "Freelancer (Variable Income)",
        "household": "Household / Family Manager"
    }
    flash(f"Loaded demo dataset for '{scenario_names.get(scenario)}'! You can explore all features with this realistic sample data.", "success")
    return redirect(url_for("main.dashboard"))
