import os
import uuid
import urllib.parse
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Check if the uploaded file has an allowed image extension."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp', 'gif'})

def save_uploaded_image(file_storage, folder_name='uploads'):
    """
    Safely save an uploaded image to the static/uploads directory.
    Returns the relative URL path for database storage (e.g. /static/uploads/filename.jpg).
    """
    if not file_storage or file_storage.filename == '':
        return None
    
    if not allowed_file(file_storage.filename):
        return None
        
    filename = secure_filename(file_storage.filename)
    # Prefix with a random unique identifier to prevent overwriting
    unique_prefix = uuid.uuid4().hex[:8]
    saved_filename = f"{unique_prefix}_{filename}"
    
    target_dir = Path(current_app.config['UPLOAD_FOLDER'])
    target_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = target_dir / saved_filename
    file_storage.save(file_path)
    
    return f"/static/uploads/{saved_filename}"

def clean_phone_number(phone_str, default="917483737517"):
    """
    Cleans any raw phone string into a standard numeric WhatsApp / international dialing string.
    Handles '+91 74837 37517', '07483737517', '7483737517', '917483737517', etc.
    """
    if not phone_str:
        return default
    digits = "".join(filter(str.isdigit, str(phone_str)))
    if not digits:
        return default
    # If 10 digits (e.g. 7483737517), prepend India country code 91
    if len(digits) == 10:
        return f"91{digits}"
    # If 11 digits starting with 0 (e.g. 07483737517)
    if len(digits) == 11 and digits.startswith('0'):
        return f"91{digits[1:]}"
    return digits

def build_whatsapp_booking_url(whatsapp_number, customer_name, service_name, appointment_date, appointment_time, notes=""):
    """
    Generates a pre-filled WhatsApp click-to-chat URL for quick booking.
    """
    clean_number = clean_phone_number(whatsapp_number)
    
    lines = [
        "👋 Hello Nature Unisex Salon,",
        "I would like to book an appointment:",
        f"👤 *Name:* {customer_name}",
        f"✂️ *Service:* {service_name}",
        f"📅 *Date:* {appointment_date}",
        f"⏰ *Time:* {appointment_time}"
    ]
    if notes:
        lines.append(f"💬 *Note:* {notes}")
    lines.append("\nPlease confirm my slot. Thank you!")
    
    message_text = "\n".join(lines)
    encoded_message = urllib.parse.quote(message_text)
    
    return f"https://api.whatsapp.com/send?phone={clean_number}&text={encoded_message}"

def build_whatsapp_general_url(whatsapp_number, message="Hello Nature Unisex Salon, I'd like to enquire about your salon services."):
    """Generates standard WhatsApp quick chat link."""
    clean_number = clean_phone_number(whatsapp_number)
    encoded_message = urllib.parse.quote(message)
    return f"https://api.whatsapp.com/send?phone={clean_number}&text={encoded_message}"

