from __future__ import annotations

import smtplib
import ssl
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from typing import Any

from ..core.config import get_settings


def _to_decimal(amount: Any) -> Decimal:
    if amount is None:
        raise ValueError("amount is required")
    if isinstance(amount, Decimal):
        return amount
    if isinstance(amount, (int, float)):
        return Decimal(str(amount))
    if isinstance(amount, str):
        v = amount.strip()
        if not v:
            raise ValueError("amount is required")
        try:
            return Decimal(v)
        except InvalidOperation as e:
            raise ValueError(f"Invalid amount: {amount!r}") from e
    raise TypeError(f"Unsupported amount type: {type(amount).__name__}")


def _format_money(currency: str, amount: Any) -> str:
    cur = (currency or "").strip().upper() or "INR"
    dec = _to_decimal(amount)
    if dec == dec.to_integral_value():
        return f"{cur} {int(dec)}"
    try:
        return f"{cur} {dec.quantize(Decimal('0.01'))}"
    except Exception:
        return f"{cur} {dec}"


def send_price_drop_email(
    to_email: str,
    origin: str,
    destination: str,
    departure_date: str,
    old_price: Any,
    new_price: Any,
    *,
    currency: str = "INR",
) -> None:
    settings = get_settings()

    host = settings.email_host
    port = settings.email_port
    user = settings.email_user
    password = settings.email_password
    from_name = settings.email_from_name

    if not host or not port or not user or not password:
        raise RuntimeError(
            "Email SMTP is not configured. Set EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD in backend/.env"
        )

    to_email_n = (to_email or "").strip()
    if not to_email_n:
        raise ValueError("to_email is required")

    origin_u = (origin or "").strip().upper()
    dest_u = (destination or "").strip().upper()

    subject = f"Price dropped for {origin_u} → {dest_u} 🎉"

    body = (
        "Good news.\n\n"
        f"The price for {origin_u} → {dest_u} on {departure_date} dropped:\n\n"
        f"Old price: {_format_money(currency, old_price)}\n"
        f"New price: {_format_money(currency, new_price)}\n\n"
        "Check FareAround now.\n"
    )

    msg = EmailMessage()
    msg["To"] = to_email_n
    msg["From"] = f"{from_name} <{user}>" if from_name else user
    msg["Subject"] = subject
    msg.set_content(body)

    timeout_s = 20

    # Gmail typically uses 587 + STARTTLS or 465 implicit SSL.
    if int(port) == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, int(port), context=context, timeout=timeout_s) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        return

    with smtplib.SMTP(host, int(port), timeout=timeout_s) as smtp:
        smtp.ehlo()
        context = ssl.create_default_context()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(user, password)
        smtp.send_message(msg)
