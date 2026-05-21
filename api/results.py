import json
import os
import hashlib
import hmac
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler

import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials

SECRET = os.environ["FLASK_SECRET_KEY"]


def verify_token(token):
    try:
        email, ts, sig = token.split(":")
        if int(time.time()) - int(ts) > 86400:
            return None
        expected = hmac.new(SECRET.encode(), f"{email}:{ts}".encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected):
            return email
    except:
        pass
    return None


def get_cookie(headers, key):
    cookies = {}
    for part in headers.get("Cookie", "").split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies.get(key, "")


def get_sheet(access_token):
    creds = OAuthCredentials(token=access_token)
    client = gspread.authorize(creds)
    return client.open_by_key(os.environ["SPREADSHEET_ID"]).sheet1


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        admin = verify_token(get_cookie(self.headers, "admin_token"))
        if not admin:
            self.send_response(401)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "unauthorized", "login_url": "/api/auth/login"}).encode())
            return

        try:
            access_token = get_cookie(self.headers, "access_token")
            sheet = get_sheet(access_token)
            all_rows = sheet.get_all_records()

            result = {
                "total": len(all_rows),
                "age_group": dict(Counter(r["연령대"] for r in all_rows)),
                "satisfaction": dict(Counter(r["만족도"] for r in all_rows)),
                "frequency": dict(Counter(r["이용빈도"] for r in all_rows)),
                "recommend": dict(Counter(r["추천여부"] for r in all_rows))
            }

            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
