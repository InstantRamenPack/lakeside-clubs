import json, requests, re
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, g, session
import markdown, bleach
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
    cursor.execute("""
        SELECT
            c.*,
            MAX(CASE WHEN cm.user_id = %s THEN cm.membership_type END) AS membership_type,
            JSON_ARRAYAGG(
                CASE
                    WHEN cm.membership_type = 1 THEN JSON_OBJECT('id', u.id, 'name', u.name, 'email', u.email)
                END
            ) AS leaders,
            JSON_ARRAYAGG(
                CASE
                    WHEN cm.membership_type = 0 THEN JSON_OBJECT('id', u.id, 'name', u.name, 'email', u.email)
                END
            ) AS members
        FROM
            raymondz_clubs c
        LEFT JOIN
            raymondz_club_members cm ON cm.club_id = c.id
        LEFT JOIN
            raymondz_users u ON u.id = cm.user_id
        WHERE
            c.id = %s
        GROUP BY
            c.id
    """, (g.user.user_id, club_id))
    club = cursor.fetchone()
    if not club:
        return "Unknown club", 404
    if club["leaders"]:
        club["leaders"] = [leader for leader in json.loads(club["leaders"]) if leader]
    else:
        club["leaders"] = []
    if club["members"]:
        club["members"] = [member for member in json.loads(club["members"]) if member]
    else:
        club["members"] = []

    cursor.execute("""
        SELECT 
            m.*,
            JSON_ARRAYAGG(
                CASE 
                    WHEN u.id IS NOT NULL THEN JSON_OBJECT('id', u.id, 'name', u.name, 'email', u.email)
                END
            ) AS members,
            MAX(u.id = %s) AS is_member
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
    """, (g.user.user_id, club_id))
    meetings = cursor.fetchall()
    for meeting in meetings:
        if meeting["members"]:
            meeting["members"] = json.loads(meeting["members"])
        else:
            meeting["members"] = []
        meeting["description"] = render_markdown_safe(meeting["description"])

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
    club_id = request.values.get("id")

    # authorization
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT club_id FROM raymondz_club_members 
        WHERE user_id = %s AND club_id = %s AND membership_type = 1
    """, (g.user.user_id, club_id))
    club = cursor.fetchone()
    if not club:
        return "Forbidden", 403

    data = request.values.get("data") or ""

    # only @lakesideschool.org emails
    emails = re.findall(r"[A-Za-z0-9._%+-]+@lakesideschool\.org", data)
    emails = [e.lower() for e in emails]
    emails = list(dict.fromkeys(emails)) # deduplicate
    if not emails:
            return json.dumps(())
    
    # add users in case they don't exist
    # use of placeholders in batch INSERT by ChatGPT
    cursor.execute(f"""
        INSERT IGNORE INTO 
            raymondz_users (email)
        VALUES 
            {", ".join(["(%s)"] * len(emails))}
    """, emails)
    mysql.connection.commit()

    # select new members
    cursor.execute(f"""
        SELECT 
            *
        FROM 
            raymondz_users u
        LEFT JOIN 
            raymondz_club_members cm
        ON 
            cm.user_id = u.id AND cm.club_id = %s
        WHERE 
            u.email IN ({", ".join(["%s"] * len(emails))}) AND cm.user_id IS NULL
    """, (club_id, *emails))
    new_members = cursor.fetchall()

    # insert memberships for new members
    if new_members:
        cursor.executemany("""
            INSERT INTO 
                raymondz_club_members 
                (user_id, club_id)
            VALUES 
                (%s, %s)
        """, [(member["id"], club_id) for member in new_members])
        mysql.connection.commit()

    return json.dumps(new_members)

@app.route("/copyUsers", methods = ["POST"])
def copyUsers():
    club_id = request.values.get("id")

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT club_id FROM raymondz_club_members
        WHERE user_id = %s AND club_id = %s AND membership_type = 1
    """, (g.user.user_id, club_id))
    club = cursor.fetchone()
    if not club:
        return "Forbidden", 403

    cursor.execute("""
        SELECT u.email
        FROM 
            raymondz_club_members cm
        JOIN 
            raymondz_users u ON u.id = cm.user_id
        WHERE 
            cm.club_id = %s
    """, (club_id,))
    members = cursor.fetchall()

    return json.dumps(members)

@app.route("/addLeader", methods = ["POST"])
def addLeader():
    club_id = request.values.get("club_id")
    user_id = request.values.get("user_id")

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT club_id FROM raymondz_club_members 
        WHERE user_id = %s AND club_id = %s AND membership_type = 1
    """, (g.user.user_id, club_id))
    club = cursor.fetchone()
    if not club:
        return "Forbidden", 403
    
    cursor.execute("""
        UPDATE 
            raymondz_club_members
        SET 
            membership_type = 1
        WHERE
            user_id = %s AND club_id = %s
    """, (user_id, club_id))
    mysql.connection.commit()
    return "Success!", 200    

@app.route("/kickMember", methods = ["POST"])
def kickMember():
    club_id = request.values.get("club_id")
    user_id = request.values.get("user_id")

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT club_id FROM raymondz_club_members 
        WHERE user_id = %s AND club_id = %s AND membership_type = 1
    """, (g.user.user_id, club_id))
    club = cursor.fetchone()
    if not club:
        return "Forbidden", 403
    
    cursor.execute("""
        DELETE FROM 
            raymondz_club_members
        WHERE
            user_id = %s AND club_id = %s
    """, (user_id, club_id))
    mysql.connection.commit()
    return "Success!", 200    

@app.route("/joinMeeting", methods = ["POST"])
def joinMeeting():    
    cursor = mysql.connection.cursor()
    cursor.execute("""                 
        INSERT IGNORE INTO 
            raymondz_meeting_members
            (user_id, meeting_id)
        VALUES
            (%s, %s)
    """, (g.user.user_id, request.values.get("id")))
    mysql.connection.commit()
    return "Success!", 200

@app.route("/leaveMeeting", methods = ["POST"])
def leaveMeeting():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        DELETE FROM 
            raymondz_meeting_members
        WHERE 
            user_id = %s AND meeting_id = %s
    """, (g.user.user_id, request.values.get("id")))
    mysql.connection.commit()
    return "Success!", 200

@app.route("/createMeeting", methods = ["POST"])
def createMeeting():
    club_id = request.values.get("club_id")
    title = request.values.get("title")
    description = request.values.get("description")
    start_time_value = request.values.get("start-time")
    end_time_value = request.values.get("end-time")
    location = request.values.get("location")

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT club_id FROM raymondz_club_members 
        WHERE user_id = %s AND club_id = %s AND membership_type = 1
    """, (g.user.user_id, club_id))
    club = cursor.fetchone()
    if not club:
        return "Forbidden", 403

    if not title or not description or not start_time_value or not end_time_value or not location:
        return "Missing required fields.", 400

    try:
        start_time = datetime.fromisoformat(start_time_value)
        end_time = datetime.fromisoformat(end_time_value)
    except (TypeError, ValueError):
        return "Invalid time values.", 400

    if end_time <= start_time:
        return "Invalid time values.", 400

    cursor.execute("""
        INSERT INTO 
            raymondz_meetings
            (club_id, title, description, start_time, end_time, location)
        VALUES 
            (%s, %s, %s, %s, %s, %s)
    """, (club_id, title, description, start_time, end_time, location))
    mysql.connection.commit()
    meeting_id = cursor.lastrowid

    meeting_data = {
        "id": meeting_id,
        "title": title,
        "description": render_markdown_safe(description),
        "date": start_time.strftime("%A, %b %-d"),
        "time_range": f"{start_time.strftime('%-I:%M')} - {end_time.strftime('%-I:%M')}",
        "location": location
    }

    return json.dumps(meeting_data)

@app.route("/meetings")
def meetings():
    if not g.user.authenticated:
        session["raymondz_next"] = request.url
        return redirect(url_for("login"))
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT 
            m.*,
            c.name AS club_name,
            CASE
                WHEN mm.user_id IS NOT NULL THEN 2
                WHEN cm.user_id IS NOT NULL THEN 1
                ELSE 0
            END AS member_status
        FROM 
            raymondz_meetings m
        JOIN
            raymondz_clubs c ON c.id = m.club_id
        LEFT JOIN
            raymondz_meeting_members mm ON mm.meeting_id = m.id AND mm.user_id = %s
        LEFT JOIN
            raymondz_club_members cm ON cm.club_id = c.id AND cm.user_id = %s
        ORDER BY
            m.start_time ASC
    """, (g.user.user_id, g.user.user_id))
    meetings = cursor.fetchall()

    for meeting in meetings:
        meeting["description"] = render_markdown_safe(meeting["description"])

    return render_template("meetings.html.j2", meetings = meetings)   

# login flow is from https://realpython.com/flask-google-login/
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

# ChatGPT generated
def render_markdown_safe(markdown_text):
    html = markdown.markdown(markdown_text, extensions = app.config["MD_EXTENSIONS"], output_format = "html5")
    clean = bleach.clean(
        html,
        tags = app.config["ALLOWED_TAGS"],
        attributes = app.config["ALLOWED_ATTRS"],
        protocols = app.config["ALLOWED_PROTOCOLS"],
        strip = True,
        strip_comments = True,
    )
    clean = bleach.linkify(clean, skip_tags = ["code", "pre"])
    return clean
