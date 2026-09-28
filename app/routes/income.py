from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import extract
from app.extensions import db
from app.models.financial import Income
from app.utils.helpers import parse_date

income_bp = Blueprint("income", __name__)

INCOME_SOURCES = [
    "Salary",
    "Freelance",
    "Business",
    "Scholarship",
    "Allowance",
    "Investment",
    "Other"
]


@income_bp.route("/income", methods=["GET"])
@login_required
def index():
    today = date.today()
    selected_year = request.args.get("year", type=int)
    selected_month = request.args.get("month", type=int)
    source_filter = request.args.get("source", "").strip()

    query = Income.query.filter_by(user_id=current_user.id)

    if selected_year:
        query = query.filter(extract("year", Income.date) == selected_year)
    if selected_month:
        query = query.filter(extract("month", Income.date) == selected_month)
    if source_filter and source_filter in INCOME_SOURCES:
        query = query.filter(Income.source == source_filter)

    incomes = query.order_by(Income.date.desc(), Income.id.desc()).all()
    total_income = sum(i.amount for i in incomes)

    # Breakdown by source
    source_breakdown = {}
    for inc in incomes:
        source_breakdown[inc.source] = round(source_breakdown.get(inc.source, 0.0) + inc.amount, 2)

    return render_template(
        "income/index.html",
        incomes=incomes,
        total_income=total_income,
        source_breakdown=source_breakdown,
        sources=INCOME_SOURCES,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_source=source_filter,
        today=today
    )


@income_bp.route("/income/add", methods=["POST"])
@login_required
def add():
    amount_str = request.form.get("amount", "").strip()
    source = request.form.get("source", "Other").strip()
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("Income amount must be greater than zero.", "danger")
            return redirect(url_for("income.index"))
    except (ValueError, TypeError):
        flash("Please enter a valid numeric income amount.", "danger")
        return redirect(url_for("income.index"))

    income_date = parse_date(date_str)
    if source not in INCOME_SOURCES:
        source = "Other"

    income = Income(
        user_id=current_user.id,
        amount=round(amount, 2),
        source=source,
        date=income_date,
        description=description
    )
    db.session.add(income)
    db.session.commit()

    flash(f"Successfully recorded income of {current_user.currency_symbol}{amount:,.2f} from {source}.", "success")
    return redirect(url_for("income.index"))


@income_bp.route("/income/edit/<int:income_id>", methods=["GET", "POST"])
@login_required
def edit(income_id):
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        source = request.form.get("source", income.source).strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        try:
            amount = float(amount_str)
            if amount <= 0:
                flash("Income amount must be greater than zero.", "danger")
                return render_template("income/edit.html", income=income, sources=INCOME_SOURCES)
        except (ValueError, TypeError):
            flash("Please enter a valid numeric income amount.", "danger")
            return render_template("income/edit.html", income=income, sources=INCOME_SOURCES)

        income.amount = round(amount, 2)
        income.source = source if source in INCOME_SOURCES else "Other"
        income.date = parse_date(date_str)
        income.description = description

        db.session.commit()
        flash("Income entry updated successfully.", "success")
        return redirect(url_for("income.index"))

    return render_template("income/edit.html", income=income, sources=INCOME_SOURCES)


@income_bp.route("/income/delete/<int:income_id>", methods=["POST"])
@login_required
def delete(income_id):
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    db.session.delete(income)
    db.session.commit()
    flash("Income entry deleted successfully.", "info")
    return redirect(url_for("income.index"))
