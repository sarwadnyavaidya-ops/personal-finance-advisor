from app.ai.gemini_service import GeminiService, DISCLAIMER


def test_ai_spending_analysis_fallback():
    """Test intelligent heuristic fallback when GEMINI_API_KEY is unset."""
    ai = GeminiService(api_key="")  # Empty key ensures fallback path

    data = {
        "currency_symbol": "$",
        "total_income": 5000.0,
        "total_expense": 3200.0,
        "savings_rate": 22.0,
        "highest_category": {"name": "Rent", "amount": 1500.0, "percentage": 46.9},
        "categories_breakdown": [
            {"category_name": "Rent", "category_type": "Essential", "amount": 1500.0, "percentage": 46.9},
            {"category_name": "Food", "category_type": "Essential", "amount": 600.0, "percentage": 18.8},
            {"category_name": "Entertainment", "category_type": "Discretionary", "amount": 400.0, "percentage": 12.5}
        ]
    }

    result = ai.analyze_spending(data)
    assert result is not None
    assert "analysis" in result
    assert DISCLAIMER in result["disclaimer"]
    assert "Rent" in result["analysis"]
    assert "$3,200.00" in result["analysis"]


def test_ai_budget_generation():
    """Test 50/30/20 budget recommendation blueprint."""
    ai = GeminiService(api_key="")
    data = {
        "currency_symbol": "$",
        "total_income": 6000.0,
        "categories_breakdown": []
    }
    result = ai.generate_budget(data)
    assert result is not None
    assert "50/30/20 Budget Blueprint" in result["budget_advice"]
    # 50% of 6000 is 3000, 30% is 1800, 20% is 1200
    assert "$3,000.00" in result["budget_advice"]
    assert "$1,800.00" in result["budget_advice"]
    assert "$1,200.00" in result["budget_advice"]


def test_ai_chat_advisor_context():
    """Test AI conversational advisor responding to specific queries."""
    ai = GeminiService(api_key="")
    context = {
        "currency_symbol": "$",
        "total_income": 4000.0,
        "total_expense": 2500.0,
        "total_savings": 800.0,
        "savings_rate": 20.0,
        "highest_category": {"name": "Dining", "amount": 650.0},
        "emergency_months": 4.2
    }

    # Query 1: Expense reduction
    reply1 = ai.chat_with_financial_advisor("How can I reduce expenses?", [], context)
    assert "Dining" in reply1
    assert DISCLAIMER in reply1

    # Query 2: Savings inquiry
    reply2 = ai.chat_with_financial_advisor("How much should I save this month?", [], context)
    assert "$800.00" in reply2
    assert "50/30/20" in reply2
