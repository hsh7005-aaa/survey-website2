import json
import os
from collections import Counter
from http.server import BaseHTTPRequestHandler

import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials

from auth import get_admin_from_cookie


def get_sheet_with_token(access_token):
    creds = OAuthCredentials(token=access_token)
    client = gspread.authorize(creds)
    return client.open_by_key(os.environ["SPREADSHEET_ID"]).sheet1


def get_access_token_from_cookie(headers):
    cookie_header = headers.get("Cookie", "")
    cookies = {}
    for part in cookie_header.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies.get("access_token", "")


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        admin = get_admin_from_cookie(self.headers)
        if not admin:
            self.send_response(401)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "unauthorized", "login_url": "/api/auth/login"}).encode())
            return

        try:
            access_token = get_access_token_from_cookie(self.headers)
            sheet = get_sheet_with_token(access_token)
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
