from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import extract, or_
from app.extensions import db
from app.models.financial import Expense, ExpenseCategory
from app.services.finance_service import FinanceService
from app.services.alert_service import AlertService
from app.utils.helpers import parse_date

expense_bp = Blueprint("expense", __name__)

PAYMENT_METHODS = ["Debit Card", "Credit Card", "Bank Transfer", "UPI", "Cash", "Other"]


@expense_bp.route("/expenses", methods=["GET"])
@login_required
def index():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)
    category_filter = request.args.get("category", type=int)
    search_query = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "date_desc")

    # Categories list (system defaults or user's custom)
    categories = ExpenseCategory.query.filter(
        or_(ExpenseCategory.is_default == True, ExpenseCategory.user_id == current_user.id)
    ).order_by(ExpenseCategory.name.asc()).all()

    query = Expense.query.filter_by(user_id=current_user.id)

    if selected_year:
        query = query.filter(extract("year", Expense.date) == selected_year)
    if selected_month:
        query = query.filter(extract("month", Expense.date) == selected_month)
    if category_filter:
        query = query.filter(Expense.category_id == category_filter)
    if search_query:
        query = query.filter(
            or_(
                Expense.description.ilike(f"%{search_query}%"),
                Expense.payment_method.ilike(f"%{search_query}%")
            )
        )

    # Sorting
    if sort_by == "date_asc":
        query = query.order_by(Expense.date.asc(), Expense.id.asc())
    elif sort_by == "amount_desc":
        query = query.order_by(Expense.amount.desc())
    elif sort_by == "amount_asc":
        query = query.order_by(Expense.amount.asc())
    else:  # date_desc
        query = query.order_by(Expense.date.desc(), Expense.id.desc())

    expenses = query.all()

    # Calculate monthly metrics
    summary = FinanceService.get_monthly_summary(current_user.id, selected_year, selected_month)

    return render_template(
        "expense/index.html",
        expenses=expenses,
        categories=categories,
        payment_methods=PAYMENT_METHODS,
        summary=summary,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_category=category_filter,
        search_query=search_query,
        sort_by=sort_by,
        today=today
    )


@expense_bp.route("/expenses/add", methods=["POST"])
@login_required
def add():
    amount_str = request.form.get("amount", "").strip()
    category_id = request.form.get("category_id", type=int)
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()
    payment_method = request.form.get("payment_method", "Debit Card").strip()
    is_recurring = bool(request.form.get("is_recurring"))

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("Expense amount must be greater than zero.", "danger")
            return redirect(url_for("expense.index"))
    except (ValueError, TypeError):
        flash("Please enter a valid numeric expense amount.", "danger")
        return redirect(url_for("expense.index"))

    category = db.session.get(ExpenseCategory, category_id)
    if not category:
        flash("Please select a valid expense category.", "danger")
        return redirect(url_for("expense.index"))

    exp_date = parse_date(date_str)
    if payment_method not in PAYMENT_METHODS:
        payment_method = "Other"

    expense = Expense(
        user_id=current_user.id,
        category_id=category_id,
        amount=round(amount, 2),
        date=exp_date,
        description=description,
        payment_method=payment_method,
        is_recurring=is_recurring
    )
    db.session.add(expense)
    db.session.commit()

    # Trigger alert engine check
    AlertService.generate_alerts_for_user(current_user, exp_date.year, exp_date.month)

    flash(f"Expense of {current_user.currency_symbol}{amount:,.2f} recorded in {category.name}.", "success")
    return redirect(url_for("expense.index", year=exp_date.year, month=exp_date.month))


@expense_bp.route("/expenses/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    categories = ExpenseCategory.query.filter(
        or_(ExpenseCategory.is_default == True, ExpenseCategory.user_id == current_user.id)
    ).order_by(ExpenseCategory.name.asc()).all()

    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        category_id = request.form.get("category_id", type=int)
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()
        payment_method = request.form.get("payment_method", "Debit Card").strip()
        is_recurring = bool(request.form.get("is_recurring"))

        try:
            amount = float(amount_str)
            if amount <= 0:
                flash("Expense amount must be greater than zero.", "danger")
                return render_template("expense/edit.html", expense=expense, categories=categories, payment_methods=PAYMENT_METHODS)
        except (ValueError, TypeError):
            flash("Please enter a valid numeric expense amount.", "danger")
            return render_template("expense/edit.html", expense=expense, categories=categories, payment_methods=PAYMENT_METHODS)

        category = db.session.get(ExpenseCategory, category_id)
        if not category:
            flash("Please select a valid expense category.", "danger")
            return render_template("expense/edit.html", expense=expense, categories=categories, payment_methods=PAYMENT_METHODS)

        expense.amount = round(amount, 2)
        expense.category_id = category_id
        expense.date = parse_date(date_str)
        expense.description = description
        expense.payment_method = payment_method if payment_method in PAYMENT_METHODS else "Other"
        expense.is_recurring = is_recurring

        db.session.commit()
        AlertService.generate_alerts_for_user(current_user, expense.date.year, expense.date.month)

        flash("Expense entry updated successfully.", "success")
        return redirect(url_for("expense.index", year=expense.date.year, month=expense.date.month))

    return render_template("expense/edit.html", expense=expense, categories=categories, payment_methods=PAYMENT_METHODS)


@expense_bp.route("/expenses/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    yr, mo = expense.date.year, expense.date.month
    db.session.delete(expense)
    db.session.commit()
    flash("Expense entry deleted successfully.", "info")
    return redirect(url_for("expense.index", year=yr, month=mo))


@expense_bp.route("/expenses/category/add", methods=["POST"])
@login_required
def add_custom_category():
    name = request.form.get("name", "").strip()
    cat_type = request.form.get("type", "Discretionary").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Category name cannot be blank.", "danger")
        return redirect(url_for("expense.index"))

    existing = ExpenseCategory.query.filter_by(name=name, user_id=current_user.id).first()
    if existing:
        flash(f"Category '{name}' already exists.", "warning")
        return redirect(url_for("expense.index"))

    cat = ExpenseCategory(
        name=name,
        type=cat_type if cat_type in ["Essential", "Discretionary", "Other"] else "Discretionary",
        description=description,
        is_default=False,
        user_id=current_user.id
    )
    db.session.add(cat)
    db.session.commit()
    flash(f"Custom category '{name}' created successfully.", "success")
    return redirect(url_for("expense.index"))
