from datetime import datetime, date
from typing import Optional, Dict, Any


CURRENCY_SYMBOLS = {
    "USD": "$",
    "INR": "₹",
    "EUR": "€",
    "GBP": "£",
    "CAD": "CA$",
    "AUD": "A$",
    "JPY": "¥",
    "SGD": "S$"
}


def format_currency(amount: float, currency_code: str = "USD") -> str:
    """Format a numeric amount with the appropriate currency symbol."""
    if amount is None:
        amount = 0.0
    symbol = CURRENCY_SYMBOLS.get(currency_code.upper(), "$")
    return f"{symbol}{amount:,.2f}"


def parse_date(date_str: Optional[str]) -> date:
    """Parse date from ISO string (YYYY-MM-DD) or return today."""
    if not date_str:
        return date.today()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return date.today()


DEFAULT_CATEGORIES = [
    {"name": "Housing", "type": "Essential", "description": "Mortgage, home repairs, and maintenance"},
    {"name": "Rent", "type": "Essential", "description": "Monthly apartment or residential rent"},
    {"name": "Food", "type": "Essential", "description": "Dining out, cafeteria, snacks, and delivery"},
    {"name": "Groceries", "type": "Essential", "description": "Supermarket, produce, and household staples"},
    {"name": "Transportation", "type": "Essential", "description": "Fuel, public transit, rideshare, and parking"},
    {"name": "Education", "type": "Essential", "description": "Tuition, textbooks, courses, and supplies"},
    {"name": "Healthcare", "type": "Essential", "description": "Doctor visits, medications, and insurance copays"},
    {"name": "Entertainment", "type": "Discretionary", "description": "Movies, concerts, video games, outings"},
    {"name": "Shopping", "type": "Discretionary", "description": "Clothing, electronics, personal accessories"},
    {"name": "Utilities", "type": "Essential", "description": "Electricity, water, gas, and garbage"},
    {"name": "Bills", "type": "Essential", "description": "Internet, mobile phone bill, council tax"},
    {"name": "Subscriptions", "type": "Discretionary", "description": "Streaming, SaaS, magazines, gym memberships"},
    {"name": "Travel", "type": "Discretionary", "description": "Flights, hotels, vacation experiences"},
    {"name": "Personal Care", "type": "Discretionary", "description": "Salon, grooming, wellness, and fitness"},
    {"name": "Other", "type": "Discretionary", "description": "Miscellaneous or unclassified expenses"}
]


def seed_default_categories(db_session):
    """Seed the standard set of default categories if they do not exist."""
    from app.models.financial import ExpenseCategory

    for cat_data in DEFAULT_CATEGORIES:
        existing = db_session.query(ExpenseCategory).filter_by(name=cat_data["name"], is_default=True).first()
        if not existing:
            category = ExpenseCategory(
                name=cat_data["name"],
                type=cat_data["type"],
                description=cat_data["description"],
                is_default=True,
                user_id=None
            )
            db_session.add(category)
    db_session.commit()
