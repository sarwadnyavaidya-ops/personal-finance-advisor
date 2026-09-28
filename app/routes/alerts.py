from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.financial import FinancialAlert

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/alerts")
@login_required
def index():
    severity_filter = request.args.get("severity", "").strip()
    query = FinancialAlert.query.filter_by(user_id=current_user.id)

    if severity_filter in ["info", "warning", "danger"]:
        query = query.filter_by(severity=severity_filter)

    alerts = query.order_by(FinancialAlert.created_at.desc()).all()
    unread_count = FinancialAlert.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template(
        "alerts/index.html",
        alerts=alerts,
        unread_count=unread_count,
        selected_severity=severity_filter
    )


@alerts_bp.route("/alerts/read/<int:alert_id>", methods=["POST"])
@login_required
def mark_read(alert_id):
    alert = FinancialAlert.query.filter_by(id=alert_id, user_id=current_user.id).first_or_404()
    alert.is_read = True
    db.session.commit()
    flash("Alert marked as read.", "info")
    return redirect(url_for("alerts.index"))


@alerts_bp.route("/alerts/read-all", methods=["POST"])
@login_required
def mark_all_read():
    FinancialAlert.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("All alerts marked as read.", "success")
    return redirect(url_for("alerts.index"))


@alerts_bp.route("/alerts/delete/<int:alert_id>", methods=["POST"])
@login_required
def delete(alert_id):
    alert = FinancialAlert.query.filter_by(id=alert_id, user_id=current_user.id).first_or_404()
    db.session.delete(alert)
    db.session.commit()
    flash("Alert deleted.", "info")
    return redirect(url_for("alerts.index"))
