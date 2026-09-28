from datetime import date
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.financial import ChatMessage, AIRecommendation
from app.services.finance_service import FinanceService
from app.ai.gemini_service import GeminiService

advisor_bp = Blueprint("advisor", __name__)


@advisor_bp.route("/advisor")
@login_required
def index():
    today = date.today()
    summary = FinanceService.get_monthly_summary(current_user.id, today.year, today.month)
    emergency_status = FinanceService.get_emergency_fund_status(current_user)

    # Conversation history
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at.asc()).all()

    # Pre-generated advice recommendations
    ai_service = GeminiService(api_key=current_app.config.get("GEMINI_API_KEY"))
    budget_rec = ai_service.generate_budget({
        "currency_symbol": current_user.currency_symbol,
        "total_income": summary["total_income"] or current_user.monthly_income,
        "categories_breakdown": summary["categories_breakdown"]
    })

    return render_template(
        "advisor/chat.html",
        messages=messages,
        summary=summary,
        emergency_status=emergency_status,
        budget_rec=budget_rec,
        today=today
    )


@advisor_bp.route("/advisor/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    # Save user message
    user_msg_record = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=user_message
    )
    db.session.add(user_msg_record)
    db.session.commit()

    # Build context from current user finances
    today = date.today()
    summary = FinanceService.get_monthly_summary(current_user.id, today.year, today.month)
    emergency_status = FinanceService.get_emergency_fund_status(current_user)

    financial_context = {
        "currency_symbol": current_user.currency_symbol,
        "total_income": summary["total_income"] or current_user.monthly_income,
        "total_expense": summary["total_expense"],
        "total_savings": summary["total_savings"],
        "savings_rate": summary["savings_rate"],
        "highest_category": summary["highest_category"],
        "emergency_months": emergency_status["runway_months"]
    }

    # Fetch last 8 messages for context
    history = [
        {"role": m.role, "content": m.content}
        for m in ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at.desc()).limit(8).all()
    ]
    history.reverse()

    ai_service = GeminiService(api_key=current_app.config.get("GEMINI_API_KEY"))
    reply_text = ai_service.chat_with_financial_advisor(user_message, history, financial_context)

    # Save assistant message
    asst_msg_record = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=reply_text
    )
    db.session.add(asst_msg_record)
    db.session.commit()

    return jsonify({
        "reply": reply_text,
        "role": "assistant",
        "created_at": asst_msg_record.created_at.strftime("%I:%M %p")
    })


@advisor_bp.route("/advisor/clear", methods=["POST"])
@login_required
def clear_history():
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("Conversation history cleared.", "info")
    return redirect(url_for("advisor.index"))
