import json
import requests

from flask import redirect, request, session, url_for
from oauthlib.oauth2 import WebApplicationClient

from app import app
from user import User

client = WebApplicationClient(app.config["GOOGLE_CLIENT_ID"])
google_provider_cfg = requests.get(app.config["GOOGLE_DISCOVERY_URL"]).json()

@app.route("/login")
def login():
    if "next" not in session:
        referrer = request.referrer
        if referrer and referrer.startswith(request.host_url):
            session["next"] = referrer
    return redirect(client.prepare_request_uri(
        google_provider_cfg["authorization_endpoint"],
        redirect_uri = url_for("callback", _external = True, _scheme = "https"),
        scope = ["openid", "email", "profile"],
    ))

@app.route("/login/callback")
def callback():
    code = request.values.get("code")
    authorization_response = request.url
    if authorization_response.startswith("http://"):
        authorization_response = "https://" + authorization_response[len("http://"):]
    token_url, headers, body = client.prepare_token_request(
        google_provider_cfg["token_endpoint"],
        authorization_response = authorization_response,
        redirect_url = url_for("callback", _external = True, _scheme = "https"),
        code = code
    )
    token_response = requests.post(
        token_url,
        headers = headers,
        data = body,
        auth = (app.config["GOOGLE_CLIENT_ID"], app.config["GOOGLE_CLIENT_SECRET"]),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))
    uri, headers, body = client.add_token(google_provider_cfg["userinfo_endpoint"])

    userinfo_response = requests.get(uri, headers = headers, data = body)
    if not userinfo_response.json()["email_verified"]:
        return "User email not available or not verified by Google.", 400
    user = User(
        google_id = userinfo_response.json()["sub"], 
        first_name = userinfo_response.json()["given_name"], 
        last_name = userinfo_response.json()["family_name"], 
        name = userinfo_response.json()["name"], 
        email = userinfo_response.json()["email"], 
        picture = userinfo_response.json()["picture"]
    )
    user.init()
    return redirect(session.pop("next", url_for("index")))

@app.route("/logout")
def logout():
    redirect_url = url_for("index")
    referrer = request.referrer
    if referrer and referrer.startswith(request.host_url):
        redirect_url = referrer
    session.clear()
    return redirect(redirect_url)
