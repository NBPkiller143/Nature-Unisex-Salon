import os
import uuid
import urllib.parse
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app

import re
import html

def sanitize_text(text, max_length=2000):
    """
    Sanitize raw user string inputs:
    - Strips dangerous HTML / script tags
    - Escapes HTML entities
    - Caps excessive length to prevent memory exhaustion DoS
    - Normalizes whitespace
    """
    if text is None:
        return ""
    # Convert to string and truncate
    text_str = str(text)[:max_length]
    # Remove null bytes and control chars
    text_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text_str)
    # Strip script/style tags and contents
    text_str = re.sub(r'<(script|style).*?>.*?</\1>', '', text_str, flags=re.DOTALL | re.IGNORECASE)
    # Strip all remaining HTML tags
    text_str = re.sub(r'<[^>]+>', '', text_str)
    # Strip leading/trailing whitespace
    return text_str.strip()

def sanitize_email(email_str):
    """Sanitize and validate email address format."""
    if not email_str:
        return ""
    clean = sanitize_text(email_str, max_length=120)
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(email_pattern, clean):
        return clean.lower()
    return ""

def is_valid_image_header(file_storage):
    """
    Validates file header magic bytes to prevent uploading executables
    disguised with image extensions.
    """
    header = file_storage.read(16)
    file_storage.seek(0) # Reset stream position
    
    if len(header) < 8:
        return False
        
    # JPEG: starts with FF D8 FF
    if header.startswith(b'\xff\xd8\xff'):
        return True
    # PNG: starts with 89 50 4E 47 0D 0A 1A 0A
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        return True
    # GIF: starts with GIF87a or GIF89a
    if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        return True
    # WEBP: starts with RIFF....WEBP
    if header.startswith(b'RIFF') and b'WEBP' in header[:16]:
        return True
        
    return False

def allowed_file(filename):
    """Check if the uploaded file has an allowed image extension."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp', 'gif'})

def save_uploaded_image(file_storage, folder_name='uploads'):
    """
    Safely save an uploaded image to the static/uploads directory.
    Validates extension, file headers, generates random UUID filename,
    and prevents directory traversal.
    """
    if not file_storage or file_storage.filename == '':
        return None
    
    if not allowed_file(file_storage.filename):
        return None
        
    # Validate magic bytes
    if not is_valid_image_header(file_storage):
        return None
        
    original_filename = secure_filename(file_storage.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    
    # Use clean random hex string + extension (prevents directory traversal or name collision)
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    target_dir = Path(current_app.config['UPLOAD_FOLDER']).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = (target_dir / unique_filename).resolve()
    # Verify path is inside target_dir
    if not str(file_path).startswith(str(target_dir)):
        return None
        
    file_storage.save(file_path)
    
    return f"/static/uploads/{unique_filename}"


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

def build_whatsapp_enquiry_url(whatsapp_number, name, phone, subject="General Salon Inquiry", message=""):
    """
    Generates a pre-filled WhatsApp click-to-chat URL for customer enquiries.
    """
    clean_number = clean_phone_number(whatsapp_number)
    
    lines = [
        "👋 Hello Nature Unisex Salon,",
        "I would like to submit an enquiry:",
        f"👤 *Name:* {name}",
        f"📞 *Phone:* {phone}",
        f"📌 *Subject:* {subject}",
        f"💬 *Message:* {message}"
    ]
    lines.append("\nPlease let me know your recommendations. Thank you!")
    
    message_text = "\n".join(lines)
    encoded_message = urllib.parse.quote(message_text)
    
    return f"https://api.whatsapp.com/send?phone={clean_number}&text={encoded_message}"


