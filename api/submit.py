import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    creds_dict = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(os.environ.get("SPREADSHEET_ID")).sheet1


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            sheet = get_sheet()

            # 헤더 없으면 추가
            existing = sheet.get_all_values()
            if not existing or existing[0][0] != "타임스탬프":
                sheet.insert_row(
                    ["타임스탬프","이름","연령대","만족도","이용빈도","추천여부","의견"],
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
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())

        except Exception as e:
            self.send_response(500)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
