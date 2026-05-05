from __future__ import annotations

import structlog

logger = structlog.get_logger()

# EMI-like debits are typically recurring, fixed amounts.  We flag a bank
# debit as "hidden" if it recurs 2+ times, is in a plausible EMI range, and
# is NOT already reported in the bureau EMI list.

_MIN_EMI_AMOUNT = 500.0
_MIN_RECURRENCE = 2


def scan_hidden_debts(
    bank_debits: list[dict],
    bureau_emis: list[dict],
) -> dict:
    """Identify recurring EMI-like debits that do not appear in the bureau.

    Parameters
    ----------
    bank_debits:
        List of bank debit transactions.  Each dict should contain at
        least ``"amount"`` (float) and ``"description"`` (str).
        Optionally ``"date"`` for richer output.
    bureau_emis:
        List of known EMI obligations from the credit bureau.  Each dict
        should contain at least ``"amount"`` (float) and optionally
        ``"lender"`` (str).

    Returns
    -------
    dict
        ``{"hidden_debts": list[dict], "total_hidden_monthly": float}``
        Each hidden-debt dict contains ``amount``, ``occurrences``, and
        ``description``.
    """
    # Build a set of known EMI amounts (with a small tolerance band)
    known_amounts: set[float] = set()
    for emi in bureau_emis:
        amt = emi.get("amount", 0.0)
        if amt > 0:
            known_amounts.add(round(amt, 2))

    # Count recurring debits grouped by rounded amount
    amount_groups: dict[float, list[dict]] = {}
    for debit in bank_debits:
        amt = round(debit.get("amount", 0.0), 2)
        if amt < _MIN_EMI_AMOUNT:
            continue
        amount_groups.setdefault(amt, []).append(debit)

    hidden_debts: list[dict] = []
    total_hidden_monthly = 0.0

    for amt, debits in amount_groups.items():
        if len(debits) < _MIN_RECURRENCE:
            continue

        # Check whether this amount matches any known bureau EMI
        # (allow a 2 % tolerance to accommodate minor rounding)
        is_known = any(
            abs(amt - known) / max(known, 1.0) < 0.02
            for known in known_amounts
        )
        if is_known:
            continue

        # Collect a representative description
        desc = debits[0].get("description", "Unknown recurring debit")

        hidden_debts.append({
            "amount": amt,
            "occurrences": len(debits),
            "description": desc,
        })
        total_hidden_monthly += amt

    if hidden_debts:
        logger.warning(
            "hidden_debts_found",
            count=len(hidden_debts),
            total_hidden_monthly=round(total_hidden_monthly, 2),
        )
    else:
        logger.info("no_hidden_debts")

    return {
        "hidden_debts": hidden_debts,
        "total_hidden_monthly": round(total_hidden_monthly, 2),
    }
