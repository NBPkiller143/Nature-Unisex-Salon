import re
from datetime import datetime, date, time, timezone, timedelta
from sqlalchemy import text
from models import db, Appointment, WebsiteSetting, Service
from utils import clean_phone_number

# India Standard Time (UTC+05:30) for salon operating hours in Bengaluru
IST = timezone(timedelta(hours=5, minutes=30))

# Valid salon appointment slot times (09:00 to 20:30)
VALID_SLOTS_24H = [
    "09:00", "09:30", "10:00", "10:30",
    "11:00", "11:30", "12:00", "12:30",
    "13:30", "14:00", "15:00", "16:00",
    "17:00", "18:00", "19:00", "20:00", "20:30"
]

# Statuses occupying a stylist/station slot
ACTIVE_SLOT_STATUSES = ['Pending', 'Confirmed']

def get_salon_current_datetime():
    """Return timezone-aware current datetime for Bengaluru salon."""
    return datetime.now(IST)

def normalize_appointment_time(time_str):
    """
    Parse and normalize varied time strings into standard ('HH:MM', 'hh:mm AM/PM') tuple.
    Handles '11:30', '11:30 AM', '14:00', '2:00 PM', '09:00', '9:30am', etc.
    """
    if not time_str:
        return None
    
    clean_str = time_str.strip().upper()
    formats_to_try = [
        '%H:%M',
        '%I:%M %p',
        '%I:%M%p',
        '%I %p',
        '%I%p'
    ]
    
    parsed_time = None
    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(clean_str, fmt)
            parsed_time = dt.time()
            break
        except ValueError:
            continue
            
    if not parsed_time:
        # Regex fallback for 'HH:MM'
        match = re.match(r'^(\d{1,2}):(\d{2})$', clean_str)
        if match:
            h, m = int(match.group(1)), int(match.group(2))
            if 0 <= h < 24 and 0 <= m < 60:
                parsed_time = time(h, m)
                
    if not parsed_time:
        return None

    standard_24h = parsed_time.strftime('%H:%M')
    display_12h = parsed_time.strftime('%I:%M %p')
    return standard_24h, display_12h

def validate_booking_datetime(app_date_str, app_time_str):
    """
    Validates appointment date and time against business rules:
    - Valid date format (YYYY-MM-DD)
    - Valid time format
    - Not in the past
    - Within salon operating hours (09:00 to 20:30)
    - Maximum 90 days in advance
    """
    if not app_date_str:
        return False, "Appointment date is required.", None, None
    if not app_time_str:
        return False, "Appointment time slot is required.", None, None

    # 1. Parse date
    try:
        booking_date = datetime.strptime(app_date_str.strip(), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return False, "Invalid appointment date format. Please use YYYY-MM-DD.", None, None

    # 2. Parse time
    time_tuple = normalize_appointment_time(app_time_str)
    if not time_tuple:
        return False, "Invalid appointment time format.", None, None
        
    std_24h, disp_12h = time_tuple
    slot_time = datetime.strptime(std_24h, '%H:%M').time()

    # 3. Check against current IST date and time
    now_ist = get_salon_current_datetime()
    today_ist = now_ist.date()
    current_time_ist = now_ist.time()

    if booking_date < today_ist:
        return False, "Appointment date cannot be in the past.", None, None

    if booking_date == today_ist and slot_time <= current_time_ist:
        return False, "Selected appointment time has already passed for today.", None, None

    # 4. Check advance booking limit (90 days)
    if (booking_date - today_ist).days > 90:
        return False, "Appointments can only be booked up to 90 days in advance.", None, None

    # 5. Operating hours check (Opening 09:00, Closing 21:00, Last slot 20:30)
    opening_time = time(9, 0)
    closing_time = time(20, 30)
    if slot_time < opening_time or slot_time > closing_time:
        return False, "Selected time is outside salon operating hours (09:00 AM to 09:00 PM).", None, None

    return True, "", booking_date, time_tuple

def check_slot_availability(app_date_str, std_24h, customer_phone=None, customer_email=None, exclude_appointment_id=None):
    """
    Checks if a slot has capacity and checks for duplicate bookings.
    Only statuses in ACTIVE_SLOT_STATUSES ('Pending', 'Confirmed') occupy a slot.
    Cancelled, Rejected, or Completed bookings do NOT block availability.
    """
    # 1. Query all active bookings on requested date
    query = Appointment.query.filter(
        Appointment.appointment_date == app_date_str,
        Appointment.status.in_(ACTIVE_SLOT_STATUSES)
    )
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
        
    day_appointments = query.all()

    # Normalize times for comparison
    active_in_slot = []
    clean_target_phone = clean_phone_number(customer_phone) if customer_phone else None
    clean_target_email = customer_email.strip().lower() if customer_email else None

    for apt in day_appointments:
        t_tuple = normalize_appointment_time(apt.appointment_time)
        if t_tuple and t_tuple[0] == std_24h:
            active_in_slot.append(apt)
            
            # Check duplicate booking for same customer
            if clean_target_phone:
                apt_phone = clean_phone_number(apt.phone)
                if apt_phone == clean_target_phone:
                    return False, "You already have an active appointment scheduled for this date and time."
                    
            if clean_target_email and apt.email:
                if apt.email.strip().lower() == clean_target_email:
                    return False, "You already have an active appointment scheduled for this date and time."

    # 2. Check salon slot capacity
    try:
        settings = WebsiteSetting.get_settings()
        max_capacity = settings.max_concurrent_bookings_per_slot or 3
    except Exception:
        max_capacity = 3

    if len(active_in_slot) >= max_capacity:
        return False, f"The selected time slot ({std_24h}) on {app_date_str} is fully booked. Please choose an alternate slot."

    return True, "Slot available"

def lock_slot_for_transaction(app_date_str, std_24h):
    """
    Acquire database transaction concurrency lock where supported:
    - In PostgreSQL: Uses pg_advisory_xact_lock on a hash of the slot key.
      Automatically released upon transaction commit or rollback.
    - In SQLite: Handled via SQLite's serialized write transactions.
    """
    try:
        if db.engine.dialect.name == 'postgresql':
            slot_key = f"salon_slot_{app_date_str}_{std_24h}"
            db.session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {'key': slot_key}
            )
    except Exception as e:
        # Non-fatal if advisory locks are restricted in specific hosted environments
        pass

