import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials
import requests as req

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

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            access_token = get_access_token_from_cookie(self.headers)
            sheet = get_sheet_with_token(access_token)

            existing = sheet.get_all_values()
            if not existing or existing[0][0] != "타임스탬프":
                sheet.insert_row(
                    ["타임스탬프", "이름", "연령대", "만족도", "이용빈도", "추천여부", "의견"],
                    index=1
                )

            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data.get("name", "익명"),
                data.get("age_group", ""),
                data.get("satisfaction", ""),
                data.get("frequency", ""),
                data.get("recommend", ""),
                data.get("comment", "")
            ])

            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())

        except Exception as e:
            self.send_response(500)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
