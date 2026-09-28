from datetime import date
from flask import Blueprint, render_template, request, flash, current_app
from flask_login import login_required, current_user
from app.services.finance_service import FinanceService
from app.ai.gemini_service import GeminiService
from app.models.financial import Expense, AIRecommendation
from app.extensions import db

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/analysis/spending")
@login_required
def spending():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)

    summary = FinanceService.get_monthly_summary(current_user.id, selected_year, selected_month)
    budget_status = FinanceService.get_budget_status(current_user.id, selected_year, selected_month)
    emergency_status = FinanceService.get_emergency_fund_status(current_user)
    trends = FinanceService.get_spending_trends(current_user.id, months_count=6)

    # Recurring expenses
    recurring_expenses = Expense.query.filter_by(
        user_id=current_user.id,
        is_recurring=True
    ).all()
    recurring_total = sum(e.amount for e in recurring_expenses)

    # Call AI / Heuristic analysis
    ai_service = GeminiService(api_key=current_app.config.get("GEMINI_API_KEY"))
    payload = {
        "currency_symbol": current_user.currency_symbol,
        "total_income": summary["total_income"],
        "total_expense": summary["total_expense"],
        "savings_rate": summary["savings_rate"],
        "highest_category": summary["highest_category"],
        "categories_breakdown": summary["categories_breakdown"],
        "emergency_status": emergency_status
    }
    ai_analysis = ai_service.analyze_spending(payload)

    return render_template(
        "analysis/spending.html",
        summary=summary,
        budget_status=budget_status,
        emergency_status=emergency_status,
        trends=trends,
        recurring_expenses=recurring_expenses,
        recurring_total=recurring_total,
        ai_analysis=ai_analysis,
        selected_year=selected_year,
        selected_month=selected_month,
        today=today
    )


@analysis_bp.route("/analysis/health")
@login_required
def health():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)

    summary = FinanceService.get_monthly_summary(current_user.id, selected_year, selected_month)
    budget_status = FinanceService.get_budget_status(current_user.id, selected_year, selected_month)
    emergency_status = FinanceService.get_emergency_fund_status(current_user)
    health_evaluation = FinanceService.evaluate_financial_health_score(current_user, selected_year, selected_month)

    # Generate or fetch savings recommendations
    ai_service = GeminiService(api_key=current_app.config.get("GEMINI_API_KEY"))
    savings_rec_data = ai_service.generate_savings_recommendations({
        "currency_symbol": current_user.currency_symbol,
        "total_income": summary["total_income"],
        "total_expense": summary["total_expense"],
        "total_savings": summary["total_savings"],
        "emergency_status": emergency_status,
        "goals": [g.to_dict() for g in current_user.financial_goals]
    })

    return render_template(
        "analysis/health.html",
        summary=summary,
        budget_status=budget_status,
        emergency_status=emergency_status,
        health=health_evaluation,
        savings_recommendations=savings_rec_data,
        selected_year=selected_year,
        selected_month=selected_month,
        today=today
    )
