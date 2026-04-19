"""
scheduler.py - Date Math Engine
Handles scheduling delays (e.g., +3 days, +7 days) for email campaigns.
Crucially, it skips weekends (Saturday and Sunday) to ensure emails are only sent on business days.
"""
import datetime
from datetime import timedelta

def calculate_next_send_date(current_date: datetime.datetime, days_to_add: int) -> str:
    """
    Calculates the next target date and pushes it forward if the resulting
    date lands on a weekend.

    Args:
        current_date (datetime.datetime): The starting date.
        days_to_add (int): Number of days ahead we want to schedule the next contact.

    Returns:
        str: Format '%Y-%m-%d' representing the next valid send date.
    """
    # 1. Start by simply adding the raw days
    target_date = current_date + timedelta(days=days_to_add)

    # 2. Check if the result lands on a weekend using a generic while loop.
    # .weekday() returns 0 for Monday, 5 for Saturday, 6 for Sunday
    while target_date.weekday() >= 5:
        # If Saturday or Sunday, add one day and check again
        target_date += timedelta(days=1)

    # 3. Format strictly as YYYY-MM-DD
    return target_date.strftime('%Y-%m-%d')
