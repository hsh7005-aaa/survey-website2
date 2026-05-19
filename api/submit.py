from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime

app = Flask(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    # 환경변수에서 서비스 계정 JSON 읽기
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_dict = json.loads(creds_json)

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    sheet = client.open_by_key(spreadsheet_id).sheet1
    return sheet

@app.route("/api/submit", methods=["POST", "OPTIONS"])
def submit():
    # CORS 처리
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    try:
        data = request.get_json()

        name = data.get("name", "익명")
        age_group = data.get("age_group", "")
        satisfaction = data.get("satisfaction", "")
        frequency = data.get("frequency", "")
        recommend = data.get("recommend", "")
        comment = data.get("comment", "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sheet = get_sheet()

        # 헤더가 없으면 추가
        if sheet.row_count == 0 or sheet.cell(1, 1).value != "타임스탬프":
            sheet.insert_row(
                ["타임스탬프", "이름", "연령대", "만족도", "이용빈도", "추천여부", "의견"],
                index=1
            )

        sheet.append_row([timestamp, name, age_group, satisfaction, frequency, recommend, comment])

        response = jsonify({"success": True, "message": "설문이 제출되었습니다."})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        response = jsonify({"success": False, "error": str(e)})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500


# Vercel handler
def handler(request, context=None):
    return app(request.environ, lambda *args: None)
