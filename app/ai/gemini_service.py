import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DISCLAIMER = "AI-generated financial guidance is for informational purposes and is not professional financial advice."


class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()

    def _call_gemini(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """Calls Gemini API using google-genai or direct Google REST API, with error handling."""
        if not self.api_key:
            return None

        # 1. Attempt using google-genai SDK
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            model_name = "gemini-2.5-flash"
            
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\nUser Question/Data:\n{prompt}"

            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"google-genai SDK call failed: {e}. Attempting REST fallback...")

        # 2. Attempt direct Google REST API fallback
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_instruction}\n\n{prompt}" if system_instruction else prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1000
                }
            }
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
            else:
                logger.warning(f"Gemini REST API returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Gemini REST API request failed: {e}")

        return None

    def analyze_spending(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes spending patterns, category distribution, and trends."""
        currency = data.get("currency_symbol", "$")
        income = data.get("total_income", 0.0)
        expense = data.get("total_expense", 0.0)
        categories = data.get("categories_breakdown", [])
        savings_rate = data.get("savings_rate", 0.0)
        highest = data.get("highest_category", {})

        system_prompt = (
            "You are an expert, empathetic Personal Finance Advisor. "
            "Analyze the provided structured financial numbers strictly based on real data. "
            "Do NOT invent fictional numbers or transactions. "
            "Provide: 1) Executive Summary, 2) Spending Distribution & High Burn Areas, "
            "3) Practical Optimization Recommendations, and 4) Actionable Next Steps. "
            f"Always include the disclaimer: '{DISCLAIMER}'"
        )
        user_prompt = (
            f"Currency: {currency}\n"
            f"Monthly Income: {currency}{income:,.2f}\n"
            f"Monthly Expenses: {currency}{expense:,.2f}\n"
            f"Savings Rate: {savings_rate}%\n"
            f"Highest Spending Category: {highest.get('name', 'None')} ({currency}{highest.get('amount', 0):,.2f}, {highest.get('percentage', 0)}% of total)\n"
            f"Category Breakdown:\n" + "\n".join(
                [f"- {c['category_name']} ({c['category_type']}): {currency}{c['amount']:,.2f} ({c['percentage']}%)" for c in categories]
            )
        )

        ai_response = self._call_gemini(user_prompt, system_instruction=system_prompt)
        if ai_response:
            return {
                "source": "Gemini AI",
                "analysis": ai_response,
                "disclaimer": DISCLAIMER
            }

        # Heuristic Rule-Based Fallback
        return self._heuristic_spending_analysis(data)

    def _heuristic_spending_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based financial spending analysis when AI key is unavailable."""
        currency = data.get("currency_symbol", "$")
        income = data.get("total_income", 0.0)
        expense = data.get("total_expense", 0.0)
        categories = data.get("categories_breakdown", [])
        savings_rate = data.get("savings_rate", 0.0)
        highest = data.get("highest_category", {})
        highest_name = highest.get("name", "Expenses")
        highest_amt = highest.get("amount", 0.0)
        highest_pct = highest.get("percentage", 0.0)

        insights = []
        if highest_pct > 35:
            insights.append(f"**High Concentration Alert**: {highest_name} consumes {highest_pct}% of your total expenditure ({currency}{highest_amt:,.2f}). Consolidating or negotiating this category could unlock meaningful savings.")
        else:
            insights.append(f"**Balanced Outlays**: Your largest category is {highest_name} at {highest_pct}% ({currency}{highest_amt:,.2f}), representing a reasonably diversified spending spread.")

        if savings_rate >= 20:
            insights.append(f"**Target Savings Rate Achieved**: Your current savings rate is {savings_rate}%, outperforming the standard 20% benchmark recommended in the 50/30/20 rule.")
        elif savings_rate > 0:
            insights.append(f"**Savings Rate**: You are currently saving {savings_rate}% of your income. Boosting this by 3-5% over the next quarter will significantly accelerate your financial safety cushion.")
        else:
            insights.append(f"**Zero Net Savings Warning**: No positive savings have been registered for this period. Directing 5-10% into automated deposits on income day is strongly recommended.")

        discretionary_total = sum(c["amount"] for c in categories if c.get("category_type") == "Discretionary")
        if discretionary_total > 0 and expense > 0:
            disc_pct = round((discretionary_total / expense) * 100, 1)
            insights.append(f"**Discretionary Spending**: Lifestyle & non-essential categories total {currency}{discretionary_total:,.2f} ({disc_pct}% of total spending). Trimming recurring subscriptions and takeout can generate immediate monthly relief.")

        text = (
            f"### Spending & Cashflow Overview\n\n"
            f"- **Total Monthly Outflow**: {currency}{expense:,.2f}\n"
            f"- **Retained Savings Rate**: {savings_rate}%\n"
            f"- **Top Outlay**: {highest_name} ({currency}{highest_amt:,.2f})\n\n"
            f"### Key Diagnostic Findings\n" + "\n".join([f"- {i}" for i in insights]) + "\n\n"
            f"### Actionable Recommendations\n"
            f"1. **Enforce Category Caps**: Set strict budget limits on discretionary lines like Entertainment and Dining.\n"
            f"2. **Audit Subscriptions**: Review recurring payments to ensure you actively use each service.\n"
            f"3. **Automate Transfers**: Schedule savings transfers on the day income arrives before discretionary expenses begin.\n\n"
            f"*{DISCLAIMER}*"
        )
        return {
            "source": "Smart Heuristic Engine",
            "analysis": text,
            "disclaimer": DISCLAIMER
        }

    def generate_budget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a personalized budget recommendation based on the 50/30/20 framework & actual spending."""
        currency = data.get("currency_symbol", "$")
        income = data.get("total_income", 0.0) or data.get("monthly_income", 0.0)
        categories = data.get("categories_breakdown", [])

        system_prompt = (
            "You are a budgeting specialist. Recommend realistic monthly category limits "
            "based on the 50% Needs, 30% Wants, 20% Savings framework. "
            "Base recommendations strictly on the user's provided income and categories. "
            f"Include the disclaimer: '{DISCLAIMER}'"
        )
        user_prompt = (
            f"Income: {currency}{income:,.2f}\n"
            f"Categories and current spending:\n" +
            "\n".join([f"- {c['category_name']}: {currency}{c['amount']:,.2f}" for c in categories])
        )

        ai_response = self._call_gemini(user_prompt, system_instruction=system_prompt)
        if ai_response:
            return {
                "source": "Gemini AI",
                "budget_advice": ai_response,
                "disclaimer": DISCLAIMER
            }

        # Heuristic 50/30/20 budget recommendation
        needs_cap = round(income * 0.50, 2)
        wants_cap = round(income * 0.30, 2)
        savings_cap = round(income * 0.20, 2)

        content = (
            f"### Recommended 50/30/20 Budget Blueprint\n\n"
            f"For your monthly baseline income of **{currency}{income:,.2f}**, the recommended allocation is:\n\n"
            f"1. **Needs & Essentials (50%)**: **{currency}{needs_cap:,.2f}**\n"
            f"   - Covers Rent/Mortgage, Groceries, Utilities, Healthcare, and Transportation.\n"
            f"2. **Wants & Discretionary (30%)**: **{currency}{wants_cap:,.2f}**\n"
            f"   - Covers Dining out, Entertainment, Shopping, and Subscriptions.\n"
            f"3. **Savings & Debt Optimization (20%)**: **{currency}{savings_cap:,.2f}**\n"
            f"   - Emergency fund build-up, retirement accounts, and financial goals.\n\n"
            f"### Action Plan\n"
            f"- Set a cap of {currency}{wants_cap:,.2f} across all non-essential category budgets.\n"
            f"- Prioritize your {currency}{savings_cap:,.2f} monthly savings target into a dedicated high-yield account.\n\n"
            f"*{DISCLAIMER}*"
        )
        return {
            "source": "Smart Heuristic Engine",
            "budget_advice": content,
            "disclaimer": DISCLAIMER
        }

    def generate_savings_recommendations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Provides tailored savings and cost-optimization recommendations."""
        currency = data.get("currency_symbol", "$")
        income = data.get("total_income", 0.0)
        expense = data.get("total_expense", 0.0)
        savings = data.get("total_savings", 0.0)
        emergency_status = data.get("emergency_status", {})
        goals = data.get("goals", [])

        user_prompt = (
            f"Income: {currency}{income:,.2f}, Expenses: {currency}{expense:,.2f}, Current Month Savings: {currency}{savings:,.2f}\n"
            f"Emergency Fund: {currency}{emergency_status.get('current_savings', 0):,.2f} of {currency}{emergency_status.get('target', 0):,.2f} "
            f"({emergency_status.get('runway_months', 0)} months runway)\n"
            f"Goals: " + ", ".join([f"{g['name']} (Saved: {currency}{g['current_amount']:,.2f} / {currency}{g['target_amount']:,.2f})" for g in goals])
        )

        ai_response = self._call_gemini(
            user_prompt,
            system_instruction=f"Provide 4 highly specific, actionable savings tactics. {DISCLAIMER}"
        )
        if ai_response:
            return {
                "source": "Gemini AI",
                "recommendations": ai_response,
                "disclaimer": DISCLAIMER
            }

        # Rule-based fallback
        runway = emergency_status.get("runway_months", 0.0)
        recs = []
        if runway < 3.0:
            recs.append(f"**Emergency Runway Priority**: You currently have {runway} months of living reserves. Build this to at least 3 months ({currency}{emergency_status.get('avg_monthly_expense', 0) * 3:,.2f}) before aggressive non-essential goal allocations.")
        else:
            recs.append(f"**Emergency Fund Solid**: With {runway} months of reserves, you can comfortably funnel surplus savings directly into your long-term wealth goals.")

        recs.append("**The 48-Hour Purchase Filter**: Apply a mandatory 48-hour waiting period on all non-essential purchases exceeding $50 to prevent impulsive buying.")
        recs.append("**Automated Micro-Savings**: Configure an automatic transfer to savings the day after pay arrives so that you 'pay yourself first'.")
        recs.append("**Subscription Pruning**: Review active recurring streaming and SaaS memberships quarterly. Canceling just two unused services typically saves $25–$50/month.")

        content = (
            f"### High-Impact Savings Strategies\n\n" +
            "\n\n".join([f"- {r}" for r in recs]) +
            f"\n\n*{DISCLAIMER}*"
        )
        return {
            "source": "Smart Heuristic Engine",
            "recommendations": content,
            "disclaimer": DISCLAIMER
        }

    def chat_with_financial_advisor(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]],
        financial_context: Dict[str, Any]
    ) -> str:
        """Interactive conversational advisor grounded in the user's real financial figures."""
        currency = financial_context.get("currency_symbol", "$")
        income = financial_context.get("total_income", 0.0)
        expense = financial_context.get("total_expense", 0.0)
        savings = financial_context.get("total_savings", 0.0)
        savings_rate = financial_context.get("savings_rate", 0.0)
        highest_cat = financial_context.get("highest_category", {})
        emergency_months = financial_context.get("emergency_months", 0.0)

        system_instruction = (
            "You are 'Personal Finance Advisor Bot', a supportive, pragmatic, and knowledgeable AI financial assistant. "
            "You have access to the user's authentic monthly financial summary:\n"
            f"- Preferred Currency: {currency}\n"
            f"- Total Monthly Income: {currency}{income:,.2f}\n"
            f"- Total Monthly Expenses: {currency}{expense:,.2f}\n"
            f"- Total Monthly Savings: {currency}{savings:,.2f} (Savings Rate: {savings_rate}%)\n"
            f"- Highest Expense Category: {highest_cat.get('name', 'N/A')} ({currency}{highest_cat.get('amount', 0):,.2f})\n"
            f"- Emergency Fund Runway: {emergency_months} months\n\n"
            "Guidelines:\n"
            "1. Reference their actual data when answering their questions.\n"
            "2. Never promise guaranteed investment returns. Provide educational guidance and prudent risk awareness.\n"
            "3. Keep answers concise, clear, and well-structured using markdown.\n"
            f"4. Conclude with or include the disclaimer: '{DISCLAIMER}'"
        )

        history_context = ""
        if chat_history:
            recent_msgs = chat_history[-6:]
            history_context = "Recent conversation:\n" + "\n".join(
                [f"{m['role'].capitalize()}: {m['content']}" for m in recent_msgs]
            ) + "\n\n"

        prompt = f"{history_context}User: {user_message}\nAdvisor:"

        ai_response = self._call_gemini(prompt, system_instruction=system_instruction)
        if ai_response:
            return ai_response

        # Heuristic conversational fallback
        return self._heuristic_chat_response(user_message, financial_context)

    def _heuristic_chat_response(self, message: str, context: Dict[str, Any]) -> str:
        """Intelligent contextual fallback for chat questions when API key is offline."""
        msg = message.lower()
        currency = context.get("currency_symbol", "$")
        income = context.get("total_income", 0.0)
        expense = context.get("total_expense", 0.0)
        savings = context.get("total_savings", 0.0)
        savings_rate = context.get("savings_rate", 0.0)
        highest_cat = context.get("highest_category", {})
        highest_name = highest_cat.get("name", "living costs")
        highest_amt = highest_cat.get("amount", 0.0)
        emergency_months = context.get("emergency_months", 0.0)

        if "reduce" in msg or "cut" in msg or "lower" in msg or "less" in msg:
            reply = (
                f"Based on your current numbers, your highest expenditure is in **{highest_name}** ({currency}{highest_amt:,.2f}), "
                f"accounting for a significant portion of your total monthly outflow ({currency}{expense:,.2f}).\n\n"
                f"**3 Concrete Ways to Cut Back:**\n"
                f"1. **Discretionary Capping**: Audit dining out, delivery apps, and entertainment subscriptions.\n"
                f"2. **Meal Prep & Batch Shopping**: Groceries are frequently 40–60% cheaper than takeout.\n"
                f"3. **Utility & Plan Optimization**: Call service providers (mobile, internet) annually to request competitive tier matching.\n\n"
                f"*{DISCLAIMER}*"
            )
        elif "overspend" in msg or "where" in msg or "spending" in msg:
            reply = (
                f"Looking at your records, your total spending this month is **{currency}{expense:,.2f}**.\n\n"
                f"- **Top Spending Area**: {highest_name} at **{currency}{highest_amt:,.2f}**.\n"
                f"- **Current Savings Rate**: {savings_rate}%.\n\n"
                f"Check your **Budget Planning** page to see if {highest_name} or Entertainment have breached their defined category caps.\n\n"
                f"*{DISCLAIMER}*"
            )
        elif "save" in msg or "how much" in msg or "target" in msg:
            recommended_savings = round(income * 0.20, 2) if income > 0 else 500.0
            reply = (
                f"Following the 50/30/20 guideline, a healthy monthly savings target for your income of {currency}{income:,.2f} is **{currency}{recommended_savings:,.2f}** (20%).\n\n"
                f"Currently, you have saved **{currency}{savings:,.2f}** this month ({savings_rate}%).\n"
                f"You currently have approximately **{emergency_months} months** of emergency runway covered.\n\n"
                f"*{DISCLAIMER}*"
            )
        elif "emergency" in msg or "buffer" in msg:
            reply = (
                f"Your emergency cushion currently stands at **{emergency_months} months** of living expenses.\n\n"
                f"- **Recommended standard**: 3 to 6 months of essential living expenses kept in an FDIC/government-insured high-yield savings account.\n"
                f"- **Next milestone**: If you are under 3 months, prioritize building liquidity before investing in volatile assets.\n\n"
                f"*{DISCLAIMER}*"
            )
        elif "invest" in msg or "stock" in msg or "crypto" in msg:
            reply = (
                f"When considering investments, the standard prudent sequencing is:\n\n"
                f"1. **High-interest debt elimination** (credit cards > 10% APR).\n"
                f"2. **Emergency Fund** (3–6 months essential living expenses).\n"
                f"3. **Broad-market index funds / tax-advantaged retirement accounts** for steady long-term compounding.\n\n"
                f"⚠️ *Important Reminder: Markets fluctuate and past performance is no guarantee of future returns. Avoid high-risk speculative instruments with emergency capital.*\n\n"
                f"*{DISCLAIMER}*"
            )
        else:
            reply = (
                f"Hello! I am your AI Financial Advisor. Here is a snapshot of your finances this month:\n\n"
                f"- **Monthly Income**: {currency}{income:,.2f}\n"
                f"- **Total Expenses**: {currency}{expense:,.2f}\n"
                f"- **Monthly Savings**: {currency}{savings:,.2f} ({savings_rate}% rate)\n"
                f"- **Emergency Runway**: {emergency_months} months\n\n"
                f"You can ask me questions like:\n"
                f"- *'How can I reduce my expenses?'*\n"
                f"- *'Where am I overspending?'*\n"
                f"- *'How much should I save this month?'*\n"
                f"- *'How is my emergency fund looking?'*\n\n"
                f"*{DISCLAIMER}*"
            )
        return reply
