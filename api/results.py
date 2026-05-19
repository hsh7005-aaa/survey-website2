import json
import os
from collections import Counter
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

    def do_GET(self):
        self._send_cors_headers
        try:
            sheet = get_sheet()
            all_rows = sheet.get_all_records()

            result = {
                "total": len(all_rows),
                "age_group": dict(Counter(r["연령대"] for r in all_rows)),
                "satisfaction": dict(Counter(r["만족도"] for r in all_rows)),
                "frequency": dict(Counter(r["이용빈도"] for r in all_rows)),
                "recommend": dict(Counter(r["추천여부"] for r in all_rows))
            }

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
