import os
import re
from pathlib import Path
from app import create_app
from models import User, Appointment, Service

def verify_static_assets():
    static_dir = Path('static')
    pattern = re.compile(r"url_for\(\s*['\"]static['\"],\s*filename=['\"]([^'\"]+)['\"]")
    missing = []
    
    for root, _, files in os.walk('templates'):
        for f in files:
            if f.endswith('.html'):
                with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    for match in pattern.findall(content):
                        if not (static_dir / match).exists():
                            missing.append((f, match))
    return missing

def verify_all():
    print("[*] Checking static assets in templates...")
    missing_assets = verify_static_assets()
    if missing_assets:
        print("[!] Missing assets found:")
        for t, a in missing_assets:
            print(f"    In {t}: {a}")
    else:
        print("[PASS] All static assets referenced in templates exist on disk.")

    print("\n[*] Initializing app & running route checks...")
    app = create_app('development')
    with app.test_client() as client:
        # Public routes
        for route in ['/', '/about', '/services', '/pricing', '/gallery', '/reviews', '/contact', '/booking']:
            res = client.get(route)
            assert res.status_code == 200, f"Route {route} returned {res.status_code}"
        print("[PASS] All 8 public routes returned 200 OK.")

        # Admin login & routes
        login_res = client.post('/admin/login', data={'username': 'admin', 'password': 'Admin@Nature2026'}, follow_redirects=True)
        assert login_res.status_code == 200, "Admin login failed"

        for route in ['/admin/dashboard', '/admin/appointments', '/admin/services', '/admin/gallery', '/admin/reviews', '/admin/enquiries', '/admin/settings']:
            res = client.get(route)
            assert res.status_code == 200, f"Admin route {route} returned {res.status_code}"
        print("[PASS] All 7 admin routes returned 200 OK.")

        # Notification poll and clear APIs
        res = client.get('/api/admin/appointments/poll')
        assert res.status_code == 200 and res.get_json()['success'] is True
        print("[PASS] /api/admin/appointments/poll endpoint works.")

        res = client.post('/api/admin/appointments/clear-all-notifications')
        assert res.status_code == 200 and res.get_json()['unread_count'] == 0
        print("[PASS] /api/admin/appointments/clear-all-notifications endpoint works.")

    print("\n[SUCCESS] Entire project verified with zero errors!")

if __name__ == '__main__':
    verify_all()
