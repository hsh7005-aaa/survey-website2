import os
import json
import requests
import hashlib
import hmac
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse

CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
BASE_URL = os.environ["BASE_URL"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
REDIRECT_URI = f"{BASE_URL}/api/auth/callback"
SECRET = os.environ["FLASK_SECRET_KEY"]


def make_token(email):
    ts = str(int(time.time()))
    sig = hmac.new(SECRET.encode(), f"{email}:{ts}".encode(), hashlib.sha256).hexdigest()
    return f"{email}:{ts}:{sig}"


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


def get_admin_from_cookie(headers):
    cookie_header = headers.get("Cookie", "")
    cookies = {}
    for part in cookie_header.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    token = cookies.get("admin_token", "")
    return verify_token(token)


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path

        # /api/auth/login → Google OAuth 시작
        if path == "/api/auth/login":
            params = {
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "online",
                "prompt": "select_account"
            }
            url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
            self.send_response(302)
            self.send_header("Location", url)
            self.end_headers()

        # /api/auth/callback → 코드 교환 후 쿠키 발급
        elif path == "/api/auth/callback":
            qs = parse_qs(urlparse(self.path).query)
            code = qs.get("code", [None])[0]
            if not code:
                self._respond(400, {"error": "no code"})
                return

            # 토큰 교환
            token_res = requests.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code"
            })
            token_data = token_res.json()
            access_token = token_data.get("access_token")
            if not access_token:
                self._respond(401, {"error": "token exchange failed"})
                return

            # 이메일 확인
            user_res = requests.get("https://www.googleapis.com/oauth2/v2/userinfo",
                                    headers={"Authorization": f"Bearer {access_token}"})
            user_info = user_res.json()
            email = user_info.get("email", "")

            if email != ADMIN_EMAIL:
                self.send_response(302)
                self.send_header("Location", "/?error=unauthorized")
                self.end_headers()
                return

            # 쿠키 발급 후 결과 페이지로
            token = make_token(email)
            self.send_response(302)
            self.send_header("Set-Cookie", f"admin_token={token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=86400")
            self.send_header("Location", "/results")
            self.end_headers()

        # /api/auth/logout
        elif path == "/api/auth/logout":
            self.send_response(302)
            self.send_header("Set-Cookie", "admin_token=; Path=/; Max-Age=0")
            self.send_header("Location", "/")
            self.end_headers()

        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())
