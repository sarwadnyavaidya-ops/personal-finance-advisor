from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.financial import Budget, ExpenseCategory
from app.services.finance_service import FinanceService
from app.services.alert_service import AlertService

budget_bp = Blueprint("budget", __name__)


@budget_bp.route("/budget", methods=["GET"])
@login_required
def index():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)

    # All active categories
    categories = ExpenseCategory.query.filter(
        or_(ExpenseCategory.is_default == True, ExpenseCategory.user_id == current_user.id)
    ).order_by(ExpenseCategory.name.asc()).all()

    # Calculate status
    status = FinanceService.get_budget_status(current_user.id, selected_year, selected_month)
    summary = FinanceService.get_monthly_summary(current_user.id, selected_year, selected_month)

    # Existing budgets for this month
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        year=selected_year,
        month=selected_month
    ).all()

    return render_template(
        "budget/index.html",
        status=status,
        summary=summary,
        budgets=budgets,
        categories=categories,
        selected_year=selected_year,
        selected_month=selected_month,
        today=today
    )


@budget_bp.route("/budget/set", methods=["POST"])
@login_required
def set_budget():
    category_id_raw = request.form.get("category_id", "").strip()
    amount_str = request.form.get("amount", "").strip()
    month = request.form.get("month", date.today().month, type=int)
    year = request.form.get("year", date.today().year, type=int)

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("Budget amount must be a positive number.", "danger")
            return redirect(url_for("budget.index", year=year, month=month))
    except (ValueError, TypeError):
        flash("Please enter a valid numeric budget amount.", "danger")
        return redirect(url_for("budget.index", year=year, month=month))

    category_id = int(category_id_raw) if category_id_raw and category_id_raw != "overall" else None

    # Check if budget entry already exists for this user/month/year/category
    existing = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=category_id,
        year=year,
        month=month
    ).first()

    if existing:
        existing.amount = round(amount, 2)
        flash("Budget updated successfully.", "success")
    else:
        budget = Budget(
            user_id=current_user.id,
            category_id=category_id,
            amount=round(amount, 2),
            month=month,
            year=year
        )
        db.session.add(budget)
        flash("Budget created successfully.", "success")

    db.session.commit()
    AlertService.generate_alerts_for_user(current_user, year, month)

    return redirect(url_for("budget.index", year=year, month=month))


@budget_bp.route("/budget/delete/<int:budget_id>", methods=["POST"])
@login_required
def delete(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    yr, mo = budget.year, budget.month
    db.session.delete(budget)
    db.session.commit()
    flash("Budget deleted successfully.", "info")
    return redirect(url_for("budget.index", year=yr, month=mo))
