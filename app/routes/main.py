from datetime import date
from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from app.services.finance_service import FinanceService
from app.services.alert_service import AlertService
from app.models.financial import Expense, Income, FinancialGoal, FinancialAlert, AIRecommendation

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("dashboard/landing.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    # Refresh alerts for this period
    AlertService.generate_alerts_for_user(current_user, year, month)

    summary = FinanceService.get_monthly_summary(current_user.id, year, month)
    budget_status = FinanceService.get_budget_status(current_user.id, year, month)
    emergency_status = FinanceService.get_emergency_fund_status(current_user)
    health_evaluation = FinanceService.evaluate_financial_health_score(current_user, year, month)
    trends = FinanceService.get_spending_trends(current_user.id, months_count=6)

    # Recent Transactions (Last 5 expenses and 5 incomes)
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc(), Expense.id.desc()).limit(5).all()
    recent_incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc(), Income.id.desc()).limit(5).all()

    # Goals and Alerts
    active_goals = FinancialGoal.query.filter_by(user_id=current_user.id).order_by(FinancialGoal.target_date.asc()).all()
    unread_alerts = FinancialAlert.query.filter_by(user_id=current_user.id, is_read=False).order_by(FinancialAlert.created_at.desc()).limit(4).all()
    latest_recommendations = AIRecommendation.query.filter_by(user_id=current_user.id).order_by(AIRecommendation.created_at.desc()).limit(3).all()

    return render_template(
        "dashboard/index.html",
        summary=summary,
        budget_status=budget_status,
        emergency_status=emergency_status,
        health_evaluation=health_evaluation,
        trends=trends,
        recent_expenses=recent_expenses,
        recent_incomes=recent_incomes,
        active_goals=active_goals,
        unread_alerts=unread_alerts,
        latest_recommendations=latest_recommendations,
        selected_year=year,
        selected_month=month
    )


@main_bp.route("/health")
def health_check():
    return jsonify({"status": "healthy", "service": "Personal Finance Advisor Bot"}), 200
