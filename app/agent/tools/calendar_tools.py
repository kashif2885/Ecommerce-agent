"""
Calendar tools – fully mocked with an in-memory store.
All availability and booking checks are timezone-aware (Asia/Riyadh).
Past dates and past time slots on today's date are always rejected.
"""
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

TIMEZONE = ZoneInfo("Asia/Riyadh")

# ---------------------------------------------------------------------------
# In-memory appointment store  {booking_id: appointment_dict}
# ---------------------------------------------------------------------------
_appointments: dict[str, dict] = {}

_ALL_SLOTS = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]


def _now_riyadh() -> datetime:
    """Return the current datetime in Asia/Riyadh timezone."""
    return datetime.now(tz=TIMEZONE)


def _future_slots(date_str: str) -> list[str]:
    """
    Return slots that are:
      1. Not already booked/confirmed
      2. In the future relative to now (Asia/Riyadh)
    """
    now = _now_riyadh()
    today_str = now.strftime("%Y-%m-%d")

    booked = {
        a["time_slot"]
        for a in _appointments.values()
        if a["date"] == date_str and a["status"] == "confirmed"
    }

    result = []
    for slot in _ALL_SLOTS:
        if slot in booked:
            continue
        # For today: only include slots whose time hasn't passed yet
        if date_str == today_str:
            slot_hour, slot_min = map(int, slot.split(":"))
            if (now.hour, now.minute) >= (slot_hour, slot_min):
                continue
        result.append(slot)
    return result


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def check_availability(date: str, service: str = "") -> dict:
    """Check which future appointment time-slots are open on a given date.

    Use this tool BEFORE booking so the user can choose from available options.
    Only future slots are returned – past dates and elapsed time slots today
    are automatically excluded.

    Args:
        date: Target date in YYYY-MM-DD format (e.g. '2026-03-20').
              Convert relative expressions ('tomorrow', 'next Monday') to a
              concrete date using the current date in the system prompt.
        service: Optional service type (e.g. 'Product Demo', 'Consultation').

    Returns:
        Dict with the date, service, list of available future time-slots,
        and total count.  Returns an error if the date is in the past.
    """
    try:
        target = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": f"Invalid date format '{date}'. Please use YYYY-MM-DD."}

    today = _now_riyadh().date()
    if target < today:
        return {
            "error": f"'{date}' is in the past. Please choose today ({today}) or a future date.",
            "today": str(today),
        }

    slots = _future_slots(date)
    if not slots:
        return {
            "date": date,
            "service": service or "General",
            "available_slots": [],
            "total_available": 0,
            "message": "No available slots on this date (all booked or all elapsed).",
        }

    return {
        "date": date,
        "service": service or "General",
        "available_slots": slots,
        "total_available": len(slots),
    }


@tool
def book_appointment(
    date: str,
    time_slot: str,
    service: str,
    customer_name: str,
    customer_email: str = "",
    notes: str = "",
) -> dict:
    """Book an appointment for a customer on a confirmed future date and time.

    Always call check_availability first.  Never book a date or time slot
    that is in the past – validate against the current date/time (Asia/Riyadh).

    Args:
        date: Appointment date in YYYY-MM-DD format.
        time_slot: Confirmed time slot in HH:MM format (e.g. '14:00').
                   Must be one returned by check_availability.
        service: Service type (e.g. 'Product Demo', 'Consultation', 'General').
        customer_name: Full name of the customer.
        customer_email: Optional email for confirmation.
        notes: Optional notes or special requirements.

    Returns:
        Booking confirmation with a unique booking_id (e.g. 'BK3A7F2C1D').
        Returns an error if the date/time is in the past or already booked.
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": f"Invalid date format '{date}'. Use YYYY-MM-DD."}

    now = _now_riyadh()
    today = now.date()

    # Reject past dates
    if target_date < today:
        return {
            "error": f"Cannot book on '{date}' – that date is in the past.",
            "today": str(today),
        }

    # Reject elapsed time slots on today
    if target_date == today:
        try:
            slot_hour, slot_min = map(int, time_slot.split(":"))
        except ValueError:
            return {"error": f"Invalid time slot format '{time_slot}'. Use HH:MM."}
        if (now.hour, now.minute) >= (slot_hour, slot_min):
            return {
                "error": f"Time slot {time_slot} has already passed today ({date}).",
                "available_slots": _future_slots(date),
            }

    # Check slot is available (not already booked)
    available = _future_slots(date)
    if time_slot not in available:
        if time_slot in _ALL_SLOTS:
            return {
                "error": f"Time slot {time_slot} is already booked on {date}.",
                "available_slots": available,
            }
        return {
            "error": f"'{time_slot}' is not a valid slot. Choose from: {_ALL_SLOTS}",
        }

    booking_id = f"BK{uuid.uuid4().hex[:8].upper()}"
    _appointments[booking_id] = {
        "booking_id": booking_id,
        "date": date,
        "time_slot": time_slot,
        "service": service,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "notes": notes,
        "status": "confirmed",
        "created_at": now.isoformat(),
    }

    return {
        "success": True,
        "booking_id": booking_id,
        "confirmation": f"Appointment confirmed for {customer_name}",
        "details": {
            "date": date,
            "time": time_slot,
            "service": service,
            "status": "confirmed",
        },
    }


@tool
def cancel_appointment(booking_id: str, reason: str = "") -> dict:
    """Cancel an existing appointment by its booking ID.

    Use this when a user wants to cancel a previously booked appointment.
    If the user doesn't know the booking ID, call list_appointments first.

    Args:
        booking_id: Unique booking identifier (e.g. 'BK3A7F2C1D').
        reason: Optional reason for cancellation.

    Returns:
        Cancellation confirmation or an error if the ID is not found.
    """
    bid = booking_id.upper()
    if bid not in _appointments:
        return {"error": f"Booking ID '{booking_id}' not found. Use list_appointments to find it."}

    appt = _appointments[bid]
    if appt["status"] == "cancelled":
        return {"error": f"Booking '{booking_id}' is already cancelled."}

    appt["status"] = "cancelled"
    appt["cancelled_at"] = _now_riyadh().isoformat()
    appt["cancellation_reason"] = reason

    return {
        "success": True,
        "booking_id": bid,
        "message": (
            f"Appointment for {appt['customer_name']} on {appt['date']} "
            f"at {appt['time_slot']} has been cancelled."
        ),
        "refund_policy": "Cancellations made 24+ hours in advance are eligible for a full refund.",
    }


@tool
def list_appointments(customer_name: str) -> dict:
    """List all appointments for a given customer name.

    Use this when a user wants to see their bookings or needs to find a
    booking ID to cancel an appointment.

    Args:
        customer_name: Full or partial name of the customer (case-insensitive).

    Returns:
        Dict with total count and sorted list of appointments.
    """
    name_lower = customer_name.lower()
    matches = [
        a for a in _appointments.values()
        if name_lower in a["customer_name"].lower()
    ]

    if not matches:
        return {
            "customer": customer_name,
            "message": f"No appointments found for '{customer_name}'.",
            "appointments": [],
        }

    return {
        "customer": customer_name,
        "total": len(matches),
        "appointments": sorted(matches, key=lambda x: (x["date"], x["time_slot"])),
    }
