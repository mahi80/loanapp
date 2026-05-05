from __future__ import annotations

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import interrupt

from src.graph.llm import get_llm
from src.graph.state import LoanApplicationState
from src.tools.internal.eligibility_rules import check_eligibility


async def intake_collect_info(state: LoanApplicationState) -> dict:
    """Step 1: Greet the user and collect basic information via an interrupt form.

    Uses interrupt() to pause and send the collect_basic_info form to the frontend.
    On resume, saves the form data into state and transitions to intake_loan_details.
    """
    llm = get_llm()
    msgs = state.get("messages", [])

    system = SystemMessage(content=(
        "You are a friendly, professional loan officer at a leading Indian bank. "
        "Greet the customer warmly. Tell them you'll collect their basic information "
        "through a simple form. Keep it to 2-3 sentences. Be warm but concise."
    ))
    greeting = await llm.ainvoke([system] + msgs)

    # Pause — frontend renders collect_basic_info form
    form_data = interrupt({
        "__interrupt_type__": "form",
        "progress": {"step": 1, "total": 5, "label": "Basic Details"},
        "tool": "collect_basic_info",
        "text": greeting.content,
    })

    # Resumed with user's form submission
    return {
        "messages": [HumanMessage(content=json.dumps(form_data))],
        "applicant_name": form_data.get("full_name", ""),
        "pan_number": form_data.get("pan_number", ""),
        "dob": form_data.get("dob", ""),
        "employment_type": form_data.get("employment_type", "salaried"),
        "monthly_income": float(form_data.get("monthly_income", 0)),
        "city": form_data.get("city", ""),
        "email": form_data.get("email", ""),
        "mobile": form_data.get("mobile", ""),
        "employer": form_data.get("employer", ""),
        "current_phase": "intake",
    }


async def intake_loan_details(state: LoanApplicationState) -> dict:
    """Step 2: Check eligibility, collect loan details, confirm and advance.

    Calculates eligibility based on income/age. If eligible, interrupts for
    loan details form. On resume, generates confirmation and advances to doc_collection.
    """
    llm = get_llm()
    msgs = state.get("messages", [])

    # Calculate age from DOB
    age = 30
    dob = state.get("dob", "")
    if dob:
        try:
            from datetime import date
            parts = dob.split("-")
            if len(parts) == 3:
                birth_year = int(parts[0])
                age = date.today().year - birth_year
        except (ValueError, IndexError):
            pass

    income = state.get("monthly_income", 0)
    max_eligible = income * 60

    eligibility = check_eligibility(
        age=age,
        monthly_income=income,
        city=state.get("city", ""),
        loan_amount=max_eligible,
    )

    eligible = eligibility.get("eligible", False)
    name = state.get("applicant_name", "Customer")

    if eligible:
        system = SystemMessage(content=(
            f"You are a friendly loan officer. The customer {name} is eligible for a loan. "
            f"Their maximum eligible amount is ₹{max_eligible:,.0f}. "
            f"Tell them the good news in 1-2 short sentences. Do NOT create any form, table, "
            f"or list of fields — the system will show the form automatically."
        ))
    else:
        reasons = eligibility.get("reasons", ["Does not meet eligibility criteria"])
        system = SystemMessage(content=(
            f"You are a friendly loan officer. Unfortunately, {name} is not eligible. "
            f"Reasons: {', '.join(reasons)}. "
            f"Explain this politely in 2-3 sentences."
        ))

    response = await llm.ainvoke([system] + msgs[-2:])

    if not eligible:
        return {
            "messages": [response],
            "current_phase": "intake",
            "conversation_complete": True,
        }

    # Pause — frontend renders collect_loan_details form
    loan_data = interrupt({
        "__interrupt_type__": "form",
        "progress": {"step": 2, "total": 5, "label": "Loan Details"},
        "tool": "collect_loan_details",
        "tool_args": {"max_amount": max_eligible},
        "eligibility": eligibility,
        "text": response.content,
    })

    # Resumed — generate confirmation and advance to doc_collection
    amount = float(loan_data.get("loan_amount", 0))
    loan_type = loan_data.get("loan_type", "personal")
    tenure = int(loan_data.get("tenure", 36))

    confirm_system = SystemMessage(content=(
        f"You are a friendly loan officer. {name}'s application details are complete: "
        f"Loan Type: {loan_type}, Amount: {amount:,.0f}, Tenure: {tenure} months. "
        f"Confirm their details look great and say you'll now collect their documents. "
        f"Keep it to 2 sentences. Do NOT list next steps or say goodbye."
    ))
    confirm_response = await llm.ainvoke([confirm_system] + msgs[-2:])

    return {
        "messages": [HumanMessage(content=json.dumps(loan_data)), confirm_response],
        "loan_amount": amount,
        "tenure_months": tenure,
        "loan_type": loan_type,
        "current_phase": "doc_collection",
    }
