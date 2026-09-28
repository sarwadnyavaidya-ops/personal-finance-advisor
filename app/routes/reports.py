from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.financial import MonthlyReport, FinancialGoal, AIRecommendation
from app.services.finance_service import FinanceService
from app.ai.gemini_service import GeminiService

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports")
@login_required
def index():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)

    summary = FinanceService.get_monthly_summary(current_user.id, selected_year, selected_month)
    budget_status = FinanceService.get_budget_status(current_user.id, selected_year, selected_month)
    emergency_status = FinanceService.get_emergency_fund_status(current_user)
    health = FinanceService.evaluate_financial_health_score(current_user, selected_year, selected_month)
    goals = FinancialGoal.query.filter_by(user_id=current_user.id).all()

    # Look up existing report or prepare one
    saved_report = MonthlyReport.query.filter_by(
        user_id=current_user.id,
        year=selected_year,
        month=selected_month
    ).first()

    return render_template(
        "reports/index.html",
        summary=summary,
        budget_status=budget_status,
        emergency_status=emergency_status,
        health=health,
        goals=goals,
        saved_report=saved_report,
        selected_year=selected_year,
        selected_month=selected_month,
        today=today
    )


@reports_bp.route("/reports/save", methods=["POST"])
@login_required
def save_report():
    year = request.form.get("year", date.today().year, type=int)
    month = request.form.get("month", date.today().month, type=int)

    summary = FinanceService.get_monthly_summary(current_user.id, year, month)
    report_record = MonthlyReport.query.filter_by(
        user_id=current_user.id,
        year=year,
        month=month
    ).first()

    if not report_record:
        report_record = MonthlyReport(
            user_id=current_user.id,
            year=year,
            month=month
        )
        db.session.add(report_record)

    report_record.total_income = summary["total_income"]
    report_record.total_expense = summary["total_expense"]
    report_record.total_savings = summary["total_savings"]
    report_record.report_content = f"Financial summary archived for {summary['month_name']} {year}. Cashflow: {summary['net_cashflow']}, Savings Rate: {summary['savings_rate']}%."

    db.session.commit()
    flash(f"Monthly report for {summary['month_name']} {year} archived successfully.", "success")
    return redirect(url_for("reports.index", year=year, month=month))


@reports_bp.route("/reports/print")
@login_required
def print_view():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)

    summary = FinanceService.get_monthly_summary(current_user.id, selected_year, selected_month)
    budget_status = FinanceService.get_budget_status(current_user.id, selected_year, selected_month)
    emergency_status = FinanceService.get_emergency_fund_status(current_user)
    health = FinanceService.evaluate_financial_health_score(current_user, selected_year, selected_month)
    goals = FinancialGoal.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "reports/print_view.html",
        summary=summary,
        budget_status=budget_status,
        emergency_status=emergency_status,
        health=health,
        goals=goals,
        selected_year=selected_year,
        selected_month=selected_month,
        today=today
    )
