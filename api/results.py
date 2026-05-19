from flask import Flask, jsonify
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from collections import Counter

app = Flask(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_dict = json.loads(creds_json)

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    sheet = client.open_by_key(spreadsheet_id).sheet1
    return sheet

@app.route("/api/results", methods=["GET", "OPTIONS"])
def results():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_records()  # 헤더 제외 딕셔너리 리스트

        total = len(all_rows)

        # 집계
        age_groups = Counter(row["연령대"] for row in all_rows)
        satisfactions = Counter(row["만족도"] for row in all_rows)
        frequencies = Counter(row["이용빈도"] for row in all_rows)
        recommends = Counter(row["추천여부"] for row in all_rows)

        response = jsonify({
            "total": total,
            "age_group": dict(age_groups),
            "satisfaction": dict(satisfactions),
            "frequency": dict(frequencies),
            "recommend": dict(recommends)
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


def handler(request, context=None):
    return app(request.environ, lambda *args: None)
