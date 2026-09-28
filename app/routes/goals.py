from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.financial import FinancialGoal
from app.utils.helpers import parse_date

goals_bp = Blueprint("goals", __name__)

GOAL_CATEGORIES = [
    "Emergency Fund",
    "Laptop / Tech Upgrade",
    "Education / Courses",
    "Travel / Vacation",
    "Vehicle / Car",
    "House Down Payment",
    "Investment / Retirement",
    "Debt Payoff",
    "Other"
]


@goals_bp.route("/goals", methods=["GET"])
@login_required
def index():
    goals = FinancialGoal.query.filter_by(user_id=current_user.id).order_by(FinancialGoal.target_date.asc()).all()

    total_target = sum(g.target_amount for g in goals)
    total_saved = sum(g.current_amount for g in goals)
    total_remaining = max(0.0, total_target - total_saved)
    overall_progress = round((total_saved / total_target * 100), 1) if total_target > 0 else 0.0

    return render_template(
        "goals/index.html",
        goals=goals,
        total_target=total_target,
        total_saved=total_saved,
        total_remaining=total_remaining,
        overall_progress=overall_progress,
        goal_categories=GOAL_CATEGORIES,
        today=date.today()
    )


@goals_bp.route("/goals/add", methods=["POST"])
@login_required
def add():
    name = request.form.get("name", "").strip()
    target_amount_str = request.form.get("target_amount", "").strip()
    current_amount_str = request.form.get("current_amount", "0").strip()
    target_date_str = request.form.get("target_date", "").strip()

    if not name:
        flash("Goal name is required.", "danger")
        return redirect(url_for("goals.index"))

    try:
        target_amount = float(target_amount_str)
        current_amount = float(current_amount_str or 0.0)
        if target_amount <= 0:
            flash("Target amount must be positive.", "danger")
            return redirect(url_for("goals.index"))
        if current_amount < 0:
            current_amount = 0.0
    except (ValueError, TypeError):
        flash("Please enter valid numeric amounts.", "danger")
        return redirect(url_for("goals.index"))

    target_date = parse_date(target_date_str)
    status = "Achieved" if current_amount >= target_amount else "In Progress"

    goal = FinancialGoal(
        user_id=current_user.id,
        name=name,
        target_amount=round(target_amount, 2),
        current_amount=round(current_amount, 2),
        target_date=target_date,
        status=status
    )
    db.session.add(goal)
    db.session.commit()

    flash(f"Financial goal '{name}' created successfully.", "success")
    return redirect(url_for("goals.index"))


@goals_bp.route("/goals/contribute/<int:goal_id>", methods=["POST"])
@login_required
def contribute(goal_id):
    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    amount_str = request.form.get("amount", "0").strip()

    try:
        contribution = float(amount_str)
        if contribution <= 0:
            flash("Contribution amount must be greater than zero.", "danger")
            return redirect(url_for("goals.index"))
    except (ValueError, TypeError):
        flash("Invalid contribution amount entered.", "danger")
        return redirect(url_for("goals.index"))

    goal.current_amount = round(goal.current_amount + contribution, 2)
    if goal.current_amount >= goal.target_amount:
        goal.status = "Achieved"
        flash(f"Congratulations! You achieved your goal for '{goal.name}'!", "success")
    else:
        flash(f"Added {current_user.currency_symbol}{contribution:,.2f} towards '{goal.name}'.", "success")

    db.session.commit()
    return redirect(url_for("goals.index"))


@goals_bp.route("/goals/edit/<int:goal_id>", methods=["GET", "POST"])
@login_required
def edit(goal_id):
    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        target_amount_str = request.form.get("target_amount", "").strip()
        current_amount_str = request.form.get("current_amount", "").strip()
        target_date_str = request.form.get("target_date", "").strip()
        status = request.form.get("status", goal.status)

        if not name:
            flash("Goal name cannot be empty.", "danger")
            return render_template("goals/edit.html", goal=goal)

        try:
            target_amount = float(target_amount_str)
            current_amount = float(current_amount_str)
            if target_amount <= 0 or current_amount < 0:
                flash("Amounts must be valid positive values.", "danger")
                return render_template("goals/edit.html", goal=goal)
        except (ValueError, TypeError):
            flash("Invalid numeric value entered.", "danger")
            return render_template("goals/edit.html", goal=goal)

        goal.name = name
        goal.target_amount = round(target_amount, 2)
        goal.current_amount = round(current_amount, 2)
        goal.target_date = parse_date(target_date_str)
        goal.status = status

        db.session.commit()
        flash(f"Goal '{goal.name}' updated successfully.", "success")
        return redirect(url_for("goals.index"))

    return render_template("goals/edit.html", goal=goal)


@goals_bp.route("/goals/delete/<int:goal_id>", methods=["POST"])
@login_required
def delete(goal_id):
    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash(f"Goal '{goal.name}' removed.", "info")
    return redirect(url_for("goals.index"))
