import os
from flask import Flask, render_template
from flask_login import current_user
from config import config_by_name
from app.extensions import db, login_manager
from app.utils.helpers import format_currency, seed_default_categories
from app.models.financial import FinancialAlert


def create_app(config_name: str = None) -> Flask:
    """Application factory for Personal Finance Advisor Bot."""
    if not config_name:
        config_name = os.getenv("FLASK_ENV", "development")

    flask_app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name["default"])
    flask_app.config.from_object(config_obj)

    # Ensure instance directory exists if using local SQLite
    try:
        os.makedirs(flask_app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(flask_app)
    login_manager.init_app(flask_app)

    # Register blueprints
    from app.routes import (
        auth_bp,
        main_bp,
        income_bp,
        expense_bp,
        budget_bp,
        savings_bp,
        goals_bp,
        analysis_bp,
        advisor_bp,
        reports_bp,
        alerts_bp,
        api_bp
    )

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(income_bp)
    flask_app.register_blueprint(expense_bp)
    flask_app.register_blueprint(budget_bp)
    flask_app.register_blueprint(savings_bp)
    flask_app.register_blueprint(goals_bp)
    flask_app.register_blueprint(analysis_bp)
    flask_app.register_blueprint(advisor_bp)
    flask_app.register_blueprint(reports_bp)
    flask_app.register_blueprint(alerts_bp)
    flask_app.register_blueprint(api_bp)

    # Register template filters and context processors
    @flask_app.template_filter("currency")
    def currency_filter(amount, currency_code="USD"):
        return format_currency(amount, currency_code)

    @flask_app.context_processor
    def inject_global_data():
        from datetime import date
        unread_count = 0
        if current_user.is_authenticated:
            try:
                unread_count = FinancialAlert.query.filter_by(
                    user_id=current_user.id,
                    is_read=False
                ).count()
            except Exception:
                unread_count = 0
        return {
            "current_year": date.today().year,
            "current_month": date.today().month,
            "today_date": date.today(),
            "unread_alerts_count": unread_count
        }

    # Error handling pages
    @flask_app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @flask_app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @flask_app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    # Auto-initialize database tables and seed default categories
    with flask_app.app_context():
        # Import models so SQLAlchemy metadata is aware of them
        from app import models  # noqa: F401
        db.create_all()
        try:
            seed_default_categories(db.session)
        except Exception as e:
            flask_app.logger.warning(f"Category seeding note: {e}")

    return flask_app
