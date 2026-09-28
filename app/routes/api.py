from datetime import date
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import extract, or_
from app.extensions import db
from app.models.financial import (
    Income,
    Expense,
    ExpenseCategory,
    Budget,
    Savings,
    FinancialGoal,
    FinancialAlert,
    MonthlyReport,
    ChatMessage
)
from app.services.finance_service import FinanceService
from app.services.alert_service import AlertService
from app.ai.gemini_service import GeminiService
from app.utils.helpers import parse_date

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------
# Dashboard & Overview API
# ---------------------------------------------------------
@api_bp.route("/dashboard", methods=["GET"])
@login_required
def get_dashboard_data():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    summary = FinanceService.get_monthly_summary(current_user.id, year, month)
    budget = FinanceService.get_budget_status(current_user.id, year, month)
    emergency = FinanceService.get_emergency_fund_status(current_user)
    health = FinanceService.evaluate_financial_health_score(current_user, year, month)
    trends = FinanceService.get_spending_trends(current_user.id, months_count=6)

    return jsonify({
        "status": "success",
        "user": current_user.to_dict(),
        "summary": summary,
        "budget": budget,
        "emergency": emergency,
        "health": health,
        "trends": trends
    }), 200


# ---------------------------------------------------------
# Income REST API
# ---------------------------------------------------------
@api_bp.route("/income", methods=["GET", "POST"])
@login_required
def income_collection():
    if request.method == "GET":
        incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
        return jsonify({
            "status": "success",
            "count": len(incomes),
            "data": [i.to_dict() for i in incomes]
        }), 200

    data = request.get_json() or {}
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return jsonify({"status": "error", "message": "Amount must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid amount provided."}), 400

    source = data.get("source", "Other").strip()
    income_date = parse_date(data.get("date"))
    description = data.get("description", "").strip()

    income = Income(
        user_id=current_user.id,
        amount=round(amount, 2),
        source=source,
        date=income_date,
        description=description
    )
    db.session.add(income)
    db.session.commit()

    return jsonify({"status": "success", "message": "Income created", "data": income.to_dict()}), 201


@api_bp.route("/income/<int:income_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def income_item(income_id):
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
    if not income:
        return jsonify({"status": "error", "message": "Income record not found."}), 404

    if request.method == "GET":
        return jsonify({"status": "success", "data": income.to_dict()}), 200

    if request.method == "DELETE":
        db.session.delete(income)
        db.session.commit()
        return jsonify({"status": "success", "message": "Income record deleted."}), 200

    data = request.get_json() or {}
    if "amount" in data:
        try:
            amt = float(data["amount"])
            if amt <= 0:
                return jsonify({"status": "error", "message": "Amount must be positive."}), 400
            income.amount = round(amt, 2)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid amount."}), 400

    if "source" in data:
        income.source = data["source"]
    if "date" in data:
        income.date = parse_date(data["date"])
    if "description" in data:
        income.description = data["description"]

    db.session.commit()
    return jsonify({"status": "success", "message": "Income updated", "data": income.to_dict()}), 200


# ---------------------------------------------------------
# Expense REST API
# ---------------------------------------------------------
@api_bp.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses_collection():
    if request.method == "GET":
        expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
        return jsonify({
            "status": "success",
            "count": len(expenses),
            "data": [e.to_dict() for e in expenses]
        }), 200

    data = request.get_json() or {}
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return jsonify({"status": "error", "message": "Amount must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid amount provided."}), 400

    category_id = data.get("category_id")
    category = db.session.get(ExpenseCategory, category_id) if category_id else None
    if not category:
        return jsonify({"status": "error", "message": "Valid category_id is required."}), 400

    exp_date = parse_date(data.get("date"))
    expense = Expense(
        user_id=current_user.id,
        category_id=category.id,
        amount=round(amount, 2),
        date=exp_date,
        description=data.get("description", "").strip(),
        payment_method=data.get("payment_method", "Debit Card"),
        is_recurring=bool(data.get("is_recurring", False))
    )
    db.session.add(expense)
    db.session.commit()
    AlertService.generate_alerts_for_user(current_user, exp_date.year, exp_date.month)

    return jsonify({"status": "success", "message": "Expense created", "data": expense.to_dict()}), 201


@api_bp.route("/expenses/<int:expense_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def expense_item(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
    if not expense:
        return jsonify({"status": "error", "message": "Expense record not found."}), 404

    if request.method == "GET":
        return jsonify({"status": "success", "data": expense.to_dict()}), 200

    if request.method == "DELETE":
        db.session.delete(expense)
        db.session.commit()
        return jsonify({"status": "success", "message": "Expense record deleted."}), 200

    data = request.get_json() or {}
    if "amount" in data:
        try:
            amt = float(data["amount"])
            if amt <= 0:
                return jsonify({"status": "error", "message": "Amount must be positive."}), 400
            expense.amount = round(amt, 2)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid amount."}), 400

    if "category_id" in data:
        cat = db.session.get(ExpenseCategory, data["category_id"])
        if cat:
            expense.category_id = cat.id

    if "date" in data:
        expense.date = parse_date(data["date"])
    if "description" in data:
        expense.description = data["description"]
    if "payment_method" in data:
        expense.payment_method = data["payment_method"]
    if "is_recurring" in data:
        expense.is_recurring = bool(data["is_recurring"])

    db.session.commit()
    AlertService.generate_alerts_for_user(current_user, expense.date.year, expense.date.month)
    return jsonify({"status": "success", "message": "Expense updated", "data": expense.to_dict()}), 200


# ---------------------------------------------------------
# Budget REST API
# ---------------------------------------------------------
@api_bp.route("/budget", methods=["GET", "POST"])
@login_required
def budget_collection():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    if request.method == "GET":
        status = FinanceService.get_budget_status(current_user.id, year, month)
        budgets = Budget.query.filter_by(user_id=current_user.id, year=year, month=month).all()
        return jsonify({
            "status": "success",
            "year": year,
            "month": month,
            "performance": status,
            "budgets": [b.to_dict() for b in budgets]
        }), 200

    data = request.get_json() or {}
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return jsonify({"status": "error", "message": "Budget amount must be positive."}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid amount."}), 400

    category_id = data.get("category_id")
    b_year = int(data.get("year", year))
    b_month = int(data.get("month", month))

    existing = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=category_id,
        year=b_year,
        month=b_month
    ).first()

    if existing:
        existing.amount = round(amount, 2)
        budget_obj = existing
    else:
        budget_obj = Budget(
            user_id=current_user.id,
            category_id=category_id,
            amount=round(amount, 2),
            month=b_month,
            year=b_year
        )
        db.session.add(budget_obj)

    db.session.commit()
    AlertService.generate_alerts_for_user(current_user, b_year, b_month)

    return jsonify({"status": "success", "message": "Budget set", "data": budget_obj.to_dict()}), 201


@api_bp.route("/budget/<int:budget_id>", methods=["DELETE"])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
    if not budget:
        return jsonify({"status": "error", "message": "Budget not found."}), 404
    db.session.delete(budget)
    db.session.commit()
    return jsonify({"status": "success", "message": "Budget deleted."}), 200


# ---------------------------------------------------------
# Savings REST API
# ---------------------------------------------------------
@api_bp.route("/savings", methods=["GET", "POST"])
@login_required
def savings_collection():
    if request.method == "GET":
        records = Savings.query.filter_by(user_id=current_user.id).order_by(Savings.date.desc()).all()
        emergency = FinanceService.get_emergency_fund_status(current_user)
        return jsonify({
            "status": "success",
            "emergency_status": emergency,
            "data": [s.to_dict() for s in records]
        }), 200

    data = request.get_json() or {}
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return jsonify({"status": "error", "message": "Amount must be positive."}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid amount."}), 400

    savings = Savings(
        user_id=current_user.id,
        amount=round(amount, 2),
        source=data.get("source", "Savings Deposit"),
        date=parse_date(data.get("date")),
        description=data.get("description", "")
    )
    db.session.add(savings)
    db.session.commit()
    return jsonify({"status": "success", "message": "Savings added", "data": savings.to_dict()}), 201


@api_bp.route("/savings/<int:savings_id>", methods=["DELETE"])
@login_required
def delete_savings(savings_id):
    record = Savings.query.filter_by(id=savings_id, user_id=current_user.id).first()
    if not record:
        return jsonify({"status": "error", "message": "Record not found."}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({"status": "success", "message": "Savings record deleted."}), 200


# ---------------------------------------------------------
# Goals REST API
# ---------------------------------------------------------
@api_bp.route("/goals", methods=["GET", "POST"])
@login_required
def goals_collection():
    if request.method == "GET":
        goals = FinancialGoal.query.filter_by(user_id=current_user.id).order_by(FinancialGoal.target_date.asc()).all()
        return jsonify({
            "status": "success",
            "data": [g.to_dict() for g in goals]
        }), 200

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"status": "error", "message": "Goal name required."}), 400

    try:
        target = float(data.get("target_amount", 0))
        current = float(data.get("current_amount", 0))
        if target <= 0 or current < 0:
            return jsonify({"status": "error", "message": "Target amount must be positive."}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid amounts."}), 400

    target_date = parse_date(data.get("target_date"))
    goal = FinancialGoal(
        user_id=current_user.id,
        name=name,
        target_amount=round(target, 2),
        current_amount=round(current, 2),
        target_date=target_date,
        status="Achieved" if current >= target else "In Progress"
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify({"status": "success", "message": "Goal created", "data": goal.to_dict()}), 201


@api_bp.route("/goals/<int:goal_id>", methods=["PUT", "DELETE"])
@login_required
def goal_item(goal_id):
    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify({"status": "error", "message": "Goal not found."}), 404

    if request.method == "DELETE":
        db.session.delete(goal)
        db.session.commit()
        return jsonify({"status": "success", "message": "Goal deleted."}), 200

    data = request.get_json() or {}
    if "name" in data and data["name"]:
        goal.name = data["name"].strip()
    if "target_amount" in data:
        goal.target_amount = float(data["target_amount"])
    if "current_amount" in data:
        goal.current_amount = float(data["current_amount"])
    if "target_date" in data:
        goal.target_date = parse_date(data["target_date"])
    if "status" in data:
        goal.status = data["status"]

    if goal.current_amount >= goal.target_amount:
        goal.status = "Achieved"

    db.session.commit()
    return jsonify({"status": "success", "message": "Goal updated", "data": goal.to_dict()}), 200


# ---------------------------------------------------------
# AI & Analytics API
# ---------------------------------------------------------
@api_bp.route("/ai/analyze", methods=["GET"])
@login_required
def ai_analyze_spending():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    summary = FinanceService.get_monthly_summary(current_user.id, year, month)
    emergency_status = FinanceService.get_emergency_fund_status(current_user)

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
    result = ai_service.analyze_spending(payload)
    return jsonify({"status": "success", "data": result}), 200


@api_bp.route("/ai/recommendations", methods=["GET"])
@login_required
def ai_recommendations():
    today = date.today()
    summary = FinanceService.get_monthly_summary(current_user.id, today.year, today.month)
    emergency = FinanceService.get_emergency_fund_status(current_user)
    goals = [g.to_dict() for g in current_user.financial_goals]

    ai_service = GeminiService(api_key=current_app.config.get("GEMINI_API_KEY"))
    savings_data = ai_service.generate_savings_recommendations({
        "currency_symbol": current_user.currency_symbol,
        "total_income": summary["total_income"] or current_user.monthly_income,
        "total_expense": summary["total_expense"],
        "total_savings": summary["total_savings"],
        "emergency_status": emergency,
        "goals": goals
    })
    budget_data = ai_service.generate_budget({
        "currency_symbol": current_user.currency_symbol,
        "total_income": summary["total_income"] or current_user.monthly_income,
        "categories_breakdown": summary["categories_breakdown"]
    })

    return jsonify({
        "status": "success",
        "savings_recommendations": savings_data,
        "budget_recommendations": budget_data
    }), 200


@api_bp.route("/ai/chat", methods=["POST"])
@login_required
def ai_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"status": "error", "message": "Message required."}), 400

    today = date.today()
    summary = FinanceService.get_monthly_summary(current_user.id, today.year, today.month)
    emergency = FinanceService.get_emergency_fund_status(current_user)

    context = {
        "currency_symbol": current_user.currency_symbol,
        "total_income": summary["total_income"] or current_user.monthly_income,
        "total_expense": summary["total_expense"],
        "total_savings": summary["total_savings"],
        "savings_rate": summary["savings_rate"],
        "highest_category": summary["highest_category"],
        "emergency_months": emergency["runway_months"]
    }

    history = [
        {"role": m.role, "content": m.content}
        for m in ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at.desc()).limit(8).all()
    ]
    history.reverse()

    ai_service = GeminiService(api_key=current_app.config.get("GEMINI_API_KEY"))
    reply = ai_service.chat_with_financial_advisor(message, history, context)

    # Save to chat history
    db.session.add(ChatMessage(user_id=current_user.id, role="user", content=message))
    db.session.add(ChatMessage(user_id=current_user.id, role="assistant", content=reply))
    db.session.commit()

    return jsonify({"status": "success", "reply": reply}), 200


# ---------------------------------------------------------
# Alerts REST API
# ---------------------------------------------------------
@api_bp.route("/alerts", methods=["GET"])
@login_required
def alerts_collection():
    alerts = FinancialAlert.query.filter_by(user_id=current_user.id).order_by(FinancialAlert.created_at.desc()).all()
    return jsonify({
        "status": "success",
        "count": len(alerts),
        "data": [a.to_dict() for a in alerts]
    }), 200


@api_bp.route("/alerts/<int:alert_id>/read", methods=["POST"])
@login_required
def mark_alert_read(alert_id):
    alert = FinancialAlert.query.filter_by(id=alert_id, user_id=current_user.id).first()
    if not alert:
        return jsonify({"status": "error", "message": "Alert not found."}), 404
    alert.is_read = True
    db.session.commit()
    return jsonify({"status": "success", "message": "Alert marked as read"}), 200
