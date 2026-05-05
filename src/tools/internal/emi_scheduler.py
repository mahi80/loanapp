from __future__ import annotations

import math
from datetime import date, timedelta

import structlog

logger = structlog.get_logger()


def generate_emi_schedule(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    start_date: str | None = None,
) -> dict:
    """Generate a full amortization (EMI) schedule.

    Parameters
    ----------
    principal:
        Loan amount.
    annual_rate:
        Annual interest rate as a percentage (e.g. 12.0 for 12 %).
    tenure_months:
        Number of monthly instalments.
    start_date:
        ISO-format date string (``YYYY-MM-DD``) for the first payment.
        Defaults to today + 30 days if *None*.

    Returns
    -------
    dict
        ``emi_amount``, ``total_interest``, ``total_payment``, and
        ``payments`` (list of per-month dicts).
    """
    if tenure_months <= 0:
        logger.error("emi_invalid_tenure", tenure_months=tenure_months)
        return {
            "emi_amount": 0.0,
            "total_interest": 0.0,
            "total_payment": 0.0,
            "payments": [],
        }

    if annual_rate == 0:
        emi = principal / tenure_months
        monthly_rate = 0.0
    else:
        monthly_rate = annual_rate / 12.0 / 100.0
        emi = (
            principal
            * monthly_rate
            * math.pow(1 + monthly_rate, tenure_months)
            / (math.pow(1 + monthly_rate, tenure_months) - 1)
        )

    emi = round(emi, 2)

    # Determine start date
    if start_date is not None:
        payment_date = date.fromisoformat(start_date)
    else:
        payment_date = date.today() + timedelta(days=30)

    balance = principal
    total_interest = 0.0
    payments: list[dict] = []

    for month_no in range(1, tenure_months + 1):
        interest_component = round(balance * monthly_rate, 2)
        principal_component = round(emi - interest_component, 2)

        # Last month: adjust for rounding residuals
        if month_no == tenure_months:
            principal_component = round(balance, 2)
            interest_component = round(emi - principal_component, 2) if emi > principal_component else 0.0
            # Recompute the final EMI so the schedule closes exactly
            final_emi = round(principal_component + interest_component, 2)
        else:
            final_emi = emi

        balance = round(balance - principal_component, 2)
        if balance < 0:
            balance = 0.0

        total_interest += interest_component

        payments.append({
            "month": month_no,
            "date": payment_date.isoformat(),
            "emi": final_emi,
            "principal": principal_component,
            "interest": interest_component,
            "balance": balance,
        })

        # Advance one month
        # Simple approach: add ~30 days; align to same day-of-month
        if payment_date.month == 12:
            payment_date = payment_date.replace(year=payment_date.year + 1, month=1)
        else:
            try:
                payment_date = payment_date.replace(month=payment_date.month + 1)
            except ValueError:
                # Handle months with fewer days (e.g. Jan 31 -> Feb 28)
                next_month = payment_date.month + 1
                year = payment_date.year
                if next_month > 12:
                    next_month = 1
                    year += 1
                # Use last day of next month
                if next_month == 12:
                    last_day = 31
                else:
                    last_day = (date(year, next_month + 1, 1) - timedelta(days=1)).day
                payment_date = date(year, next_month, min(payment_date.day, last_day))

    total_interest = round(total_interest, 2)
    total_payment = round(principal + total_interest, 2)

    logger.info(
        "emi_schedule_generated",
        principal=principal,
        annual_rate=annual_rate,
        tenure_months=tenure_months,
        emi=emi,
        total_interest=total_interest,
    )

    return {
        "emi_amount": emi,
        "total_interest": total_interest,
        "total_payment": total_payment,
        "payments": payments,
    }
