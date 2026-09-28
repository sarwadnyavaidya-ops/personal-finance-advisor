from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from app.extensions import db
from app.models.financial import Savings
from app.services.finance_service import FinanceService
from app.utils.helpers import parse_date

savings_bp = Blueprint("savings", __name__)

SAVINGS_SOURCES = [
    "Savings Deposit",
    "High-Yield Savings",
    "Investment",
    "Emergency Fund",
    "Cash Savings",
    "Other"
]


@savings_bp.route("/savings", methods=["GET"])
@login_required
def index():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)

    # All savings records for this user
    savings_records = Savings.query.filter_by(user_id=current_user.id).order_by(Savings.date.desc(), Savings.id.desc()).all()

    # Cumulative total
    cumulative_savings = sum(s.amount for s in savings_records)

    # Monthly total
    monthly_saved = sum(s.amount for s in savings_records if s.date.year == selected_year and s.date.month == selected_month)

    # Emergency fund overview
    emergency_status = FinanceService.get_emergency_fund_status(current_user)

    # Savings growth timeline data (by month)
    monthly_timeline = db.session.query(
        extract("year", Savings.date).label("year"),
        extract("month", Savings.date).label("month"),
        func.sum(Savings.amount).label("total")
    ).filter(
        Savings.user_id == current_user.id
    ).group_by(
        extract("year", Savings.date),
        extract("month", Savings.date)
    ).order_by(
        extract("year", Savings.date).asc(),
        extract("month", Savings.date).asc()
    ).all()

    growth_labels = []
    growth_data = []
    running_sum = 0.0

    for yr, mo, tot in monthly_timeline:
        running_sum += float(tot)
        growth_labels.append(f"{int(mo)}/{int(yr)}")
        growth_data.append(round(running_sum, 2))

    return render_template(
        "savings/index.html",
        savings_records=savings_records,
        cumulative_savings=cumulative_savings,
        monthly_saved=monthly_saved,
        emergency_status=emergency_status,
        sources=SAVINGS_SOURCES,
        growth_labels=growth_labels,
        growth_data=growth_data,
        selected_year=selected_year,
        selected_month=selected_month,
        today=today
    )


@savings_bp.route("/savings/add", methods=["POST"])
@login_required
def add():
    amount_str = request.form.get("amount", "").strip()
    source = request.form.get("source", "Savings Deposit").strip()
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("Savings deposit amount must be greater than zero.", "danger")
            return redirect(url_for("savings.index"))
    except (ValueError, TypeError):
        flash("Please enter a valid numeric savings amount.", "danger")
        return redirect(url_for("savings.index"))

    sav_date = parse_date(date_str)
    if source not in SAVINGS_SOURCES:
        source = "Other"

    record = Savings(
        user_id=current_user.id,
        amount=round(amount, 2),
        source=source,
        date=sav_date,
        description=description
    )
    db.session.add(record)
    db.session.commit()

    flash(f"Successfully recorded savings deposit of {current_user.currency_symbol}{amount:,.2f}.", "success")
    return redirect(url_for("savings.index"))


@savings_bp.route("/savings/edit/<int:savings_id>", methods=["GET", "POST"])
@login_required
def edit(savings_id):
    savings_item = Savings.query.filter_by(id=savings_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        source = request.form.get("source", savings_item.source).strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        try:
            amount = float(amount_str)
            if amount <= 0:
                flash("Savings amount must be greater than zero.", "danger")
                return render_template("savings/edit.html", savings=savings_item, sources=SAVINGS_SOURCES)
        except (ValueError, TypeError):
            flash("Please enter a valid numeric savings amount.", "danger")
            return render_template("savings/edit.html", savings=savings_item, sources=SAVINGS_SOURCES)

        savings_item.amount = round(amount, 2)
        savings_item.source = source if source in SAVINGS_SOURCES else "Other"
        savings_item.date = parse_date(date_str)
        savings_item.description = description

        db.session.commit()
        flash("Savings record updated successfully.", "success")
        return redirect(url_for("savings.index"))

    return render_template("savings/edit.html", savings=savings_item, sources=SAVINGS_SOURCES)


@savings_bp.route("/savings/delete/<int:savings_id>", methods=["POST"])
@login_required
def delete(savings_id):
    savings_item = Savings.query.filter_by(id=savings_id, user_id=current_user.id).first_or_404()
    db.session.delete(savings_item)
    db.session.commit()
    flash("Savings record deleted successfully.", "info")
    return redirect(url_for("savings.index"))
