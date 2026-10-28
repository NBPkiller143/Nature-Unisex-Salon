import hmac
import secrets
from flask import session, request, abort, jsonify

def generate_csrf_token():
    """
    Generate or retrieve a cryptographically secure session-bound CSRF token.
    Follows OWASP synchronizer token pattern.
    """
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    """
    Safely validate a submitted CSRF token against the current session.
    Uses constant-time comparison to protect against timing attacks.
    """
    expected = session.get('csrf_token')
    if not expected or not token:
        return False
    return hmac.compare_digest(str(expected), str(token))

def get_request_csrf_token():
    """
    Extract CSRF token from common locations:
    1. HTML Form parameter: csrf_token
    2. Request headers: X-CSRF-Token or X-CSRFToken
    3. JSON payload: csrf_token
    """
    token = request.form.get('csrf_token')
    if not token and request.is_json:
        try:
            data = request.get_json(silent=True)
            if isinstance(data, dict):
                token = data.get('csrf_token')
        except Exception:
            token = None
    if not token:
        token = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken')
    return token

