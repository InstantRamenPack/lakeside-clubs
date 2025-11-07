import math, json, datetime, random, os, requests, re
from os import environ

from flask import Flask, render_template, request, redirect, url_for, g, session
from oauthlib.oauth2 import WebApplicationClient

from user import User
from db import mysql, init_db

app = Flask(__name__)
app.config.from_pyfile('config.py')
init_db(app)
client = WebApplicationClient(app.config["GOOGLE_CLIENT_ID"])
google_provider_cfg = requests.get(app.config["GOOGLE_DISCOVERY_URL"]).json()

@app.before_request
def load_user():
    g.user = User.retrieve()
    if not g.user:
        g.user = User(authenticated = False)

@app.route("/")
def index():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT
            c.*, 
            m.membership_type
        FROM
            raymondz_clubs c
        LEFT JOIN
            raymondz_club_members m
        ON
            m.club_id = c.id
        AND
            m.user_id = %s
        ORDER BY
            m.membership_type DESC,
            c.id
    """, (g.user.user_id,))

    return render_template("index.html.j2", clubs = cursor.fetchall())

@app.route("/club")
def club():
    club_id = request.values.get("id")
    cursor = mysql.connection.cursor()
    # asked ChatGPT how to combine two queries into one
    cursor.execute("""
        SELECT 
            c.*,
            (
                SELECT 
                   JSON_ARRAYAGG(JSON_OBJECT('id', u.id, 'name', u.name, 'email', u.email))
                FROM 
                   raymondz_club_members m
                JOIN 
                   raymondz_users u ON u.id = m.user_id
                WHERE 
                   m.club_id = c.id AND m.membership_type = 1
            ) AS leaders,
            (
                SELECT 
                   JSON_ARRAYAGG(JSON_OBJECT('id', u.id, 'name', u.name, 'email', u.email))
                FROM 
                   raymondz_club_members m
                JOIN 
                   raymondz_users u ON u.id = m.user_id
                WHERE 
                   m.club_id = c.id AND m.membership_type = 0
            ) AS members,
            m.membership_type
        FROM 
            raymondz_clubs c
        LEFT JOIN 
            raymondz_club_members m ON m.user_id = %s AND m.club_id = %s
        WHERE 
            c.id = %s
    """, (g.user.user_id, club_id, club_id))
    club = cursor.fetchone()
    if not club:
        return "Unknown club", 404
    if club["leaders"]:
        club["leaders"] = json.loads(club["leaders"])
    else:
        club["leaders"] = []
    if club["members"]:
        club["members"] = json.loads(club["members"])
    else:
        club["members"] = []

    cursor.execute("""
        SELECT 
            m.*,
            JSON_ARRAYAGG(JSON_OBJECT('id', u.id, 'name', u.name, 'email', u.email)) AS members
        FROM 
            raymondz_meetings m 
        LEFT JOIN
            raymondz_meeting_members mm ON mm.meeting_id = m.id
        LEFT JOIN
            raymondz_users u ON u.id = mm.user_id
        WHERE 
            m.club_id = %s
        GROUP BY 
            m.id 
        ORDER BY
            m.start_time ASC
    """, (club_id,))
    meetings = cursor.fetchall()
    for meeting in meetings:
        if meeting["members"]:
            meeting["members"] = json.loads(meeting["members"])

    return render_template("club.html.j2", club = club, meetings = meetings)   

@app.route("/joinClub", methods = ["GET", "POST"])
def joinClub():
    if not g.user.authenticated:
        session["raymondz_next"] = request.url
        return redirect(url_for("login"))
    
    cursor = mysql.connection.cursor()
    cursor.execute("""                 
        INSERT IGNORE INTO 
            raymondz_club_members
            (user_id, club_id)
        VALUES
            (%s, %s)
    """, (g.user.user_id, request.values.get("id")))
    mysql.connection.commit()
    return redirect(url_for("index")) 

@app.route("/leaveClub", methods = ["POST"])
def leaveClub():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        DELETE FROM 
            raymondz_club_members
        WHERE 
            user_id = %s AND club_id = %s
    """, (g.user.user_id, request.values.get("id")))
    mysql.connection.commit()
    return "Success!", 200

@app.route("/importUsers", methods = ["POST"])
def importUsers():
    # authorization
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT club_id FROM raymondz_club_members 
        WHERE user_id = %s AND club_id = %s AND membership_type = 1
    """, (g.user.user_id, request.values.get("id")))
    clubs = cursor.fetchone()
    if not clubs:
        return "Forbidden", 403

    data = request.values.get("data")
    emails = re.findall("[A-Za-z0-9._%+-]+@lakesideschool\.org", data)
    for i in range(len(emails)):
        emails[i] = emails[i].lower()

    # add users if they don't exist
    emailQuery = []
    for email in emails:
        emailQuery.append((email,))
    cursor.executemany("""
        INSERT IGNORE INTO 
            raymondz_users
            (email)
        VALUES
            (%s)   
    """, emailQuery)
    mysql.connection.commit()

    emailQuery = []
    for email in emails:
        emailQuery.append((request.values.get("id"), email))
    cursor.executemany("""
        INSERT IGNORE INTO 
            raymondz_club_members
            (user_id, club_id)
        SELECT
            u.id, %s
        FROM 
            raymondz_users u
        WHERE
            u.email = %s
    """, emailQuery)
    mysql.connection.commit()

    return emails

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
    user.load()
    return redirect(session.pop("raymondz_next", url_for("index")))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))