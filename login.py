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
    return redirect(client.prepare_request_uri(
        google_provider_cfg["authorization_endpoint"],
        redirect_uri = request.base_url + "/callback",
        scope = ["openid", "email", "profile"],
    ))


@app.route("/login/callback")
def callback():
    code = request.values.get("code")
    token_url, headers, body = client.prepare_token_request(
        google_provider_cfg["token_endpoint"],
        authorization_response = request.url,
        redirect_url = request.base_url,
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
    return redirect(session.pop("raymondz_next", url_for("index")))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
