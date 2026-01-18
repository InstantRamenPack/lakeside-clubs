import json, re

from flask import g, redirect, render_template, render_template_string, request, session, url_for

from app import app, authenticate_leadership
from db import mysql
from meeting import Meeting

@app.route("/club", methods = ["GET"])
def club():
    club_id = request.values.get("club_id")
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT
            c.*,
            MAX(CASE WHEN cm.user_id = %s THEN cm.is_leader END) AS is_leader,
            MAX(CASE WHEN cm.user_id = %s THEN 1 END) AS is_member,
            (
                SELECT 
                    JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'tag_id', t.tag_id,
                            'name', t.name
                        )
                    )
                FROM
                    club_tags ct
                LEFT JOIN
                    tags t ON t.tag_id = ct.tag_id
                WHERE
                    ct.club_id = c.club_id
            ) AS tags,
            JSON_ARRAYAGG(
                CASE WHEN 
                    cm.is_leader = 1 
                THEN 
                    JSON_OBJECT(
                        'user_id', u.user_id, 
                        'first_name', u.first_name,
                        'last_name', u.last_name,
                        'name', u.name, 
                        'email', u.email
                    )
                END
            ) AS leaders,
            JSON_ARRAYAGG(
                CASE WHEN 
                    cm.is_leader = 0 
                THEN 
                    JSON_OBJECT(
                        'user_id', u.user_id, 
                        'first_name', u.first_name,
                        'last_name', u.last_name,
                        'name', u.name, 
                        'email', u.email
                    )
                END
            ) AS members
        FROM
            clubs c
        LEFT JOIN
            club_members cm ON cm.club_id = c.club_id
        LEFT JOIN
            users u ON u.user_id = cm.user_id
        WHERE
            c.club_id = %s
        GROUP BY
            c.club_id
    """, (g.user.user_id, g.user.user_id, club_id))
    club = cursor.fetchone()
    if not club:
        return "Unknown club", 404
    if club["tags"]:
        club["tags"] = json.loads(club["tags"])
    else:
        club["tags"] = []
    if club["leaders"]:
        club["leaders"] = [leader for leader in json.loads(club["leaders"]) if leader]
    else:
        club["leaders"] = []
    if club["members"]:
        club["members"] = [member for member in json.loads(club["members"]) if member]
    else:
        club["members"] = []

    # https://stackoverflow.com/a/1855104 on selecting after today
    cursor.execute("""
        SELECT 
            m.*
        FROM 
            meetings m 
        WHERE 
            m.club_id = %s
        AND
            (
                (m.is_meeting = 1 AND m.date >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 DAY))
                OR
                (m.is_meeting = 0 AND m.post_time >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 MONTH))
            )
        GROUP BY 
            m.meeting_id 
        ORDER BY
            m.is_meeting DESC,
            CASE WHEN m.is_meeting = 1 THEN m.date END ASC,
            CASE WHEN m.is_meeting = 1 THEN m.start_time END ASC,
            CASE WHEN m.is_meeting = 0 THEN m.post_time END DESC
    """, (club_id,))
    rows = cursor.fetchall()

    meetings = []
    macros = app.jinja_env.get_template("macros.html.j2").make_module({"g": g})
    for meeting in rows:
        m = Meeting.from_dict(meeting)
        m.is_leader = bool(club["is_leader"])
        m.rendered_card = macros.render_meeting_card(m, m.is_leader, m.is_meeting, True)
        meetings.append(m)

    return render_template("club.html.j2", club = club, meetings = meetings)   

@app.route("/joinClub", methods = ["GET", "POST"])
def joinClub():
    if not g.user.authenticated:
        session["next"] = request.url
        return redirect(url_for("login"))
    
    cursor = mysql.connection.cursor()
    cursor.execute("""                 
        INSERT IGNORE INTO 
            club_members
            (user_id, club_id)
        VALUES
            (%s, %s)
    """, (g.user.user_id, request.values.get("club_id")))
    return redirect(url_for("club", club_id = request.values.get("club_id"))) 

@app.route("/leaveClub", methods = ["POST"])
def leaveClub():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        DELETE FROM 
            club_members
        WHERE 
            user_id = %s AND club_id = %s
    """, (g.user.user_id, request.values.get("club_id")))
    return "Success!", 200

@app.route("/fetchMembers", methods = ["POST"])
@authenticate_leadership
def fetchMembers():
    club_id = request.values.get("club_id")
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT 
            u.email,
            cm.is_leader
        FROM 
            club_members cm
        JOIN 
            users u ON u.user_id = cm.user_id
        WHERE 
            cm.club_id = %s
        ORDER BY
            cm.is_leader DESC
    """, (club_id,))
    members = cursor.fetchall()

    return json.dumps(members)

@app.route("/importUsers", methods = ["POST"])
@authenticate_leadership
def importUsers():
    club_id = request.values.get("club_id")
    cursor = mysql.connection.cursor()

    data = request.values.get("data") or ""

    # only @lakesideschool.org emails
    emails = re.findall(r"[A-Za-z0-9._%+-]+@lakesideschool\.org", data)
    emails = [e.lower() for e in emails]
    emails = list(dict.fromkeys(emails)) # deduplicate
    if not emails:
        return json.dumps({"new_members": [], "rendered_members": []})
    
    # add users in case they don't exist
    # use of placeholders in batch INSERT by ChatGPT
    cursor.execute(f"""
        INSERT IGNORE INTO 
            users (email)
        VALUES 
            {", ".join(["(%s)"] * len(emails))}
    """, emails)
    # select new members
    cursor.execute(f"""
        SELECT 
            *
        FROM 
            users u
        LEFT JOIN 
            club_members cm
        ON 
            cm.user_id = u.user_id AND cm.club_id = %s
        WHERE 
            u.email IN ({", ".join(["%s"] * len(emails))}) AND cm.user_id IS NULL
    """, (club_id, *emails))
    new_members = cursor.fetchall()

    # insert memberships for new members
    if new_members:
        cursor.executemany("""
            INSERT INTO 
                club_members 
                (user_id, club_id)
            VALUES 
                (%s, %s)
        """, [(member["user_id"], club_id) for member in new_members])
    macros = app.jinja_env.get_template("macros.html.j2").make_module({"g": g})
    rendered_members = [macros.display_member(member, False) for member in new_members]

    return json.dumps({"new_members": new_members, "rendered_members": rendered_members})

@app.route("/kickMember", methods = ["POST"])
@authenticate_leadership
def kickMember():
    club_id = request.values.get("club_id")
    user_id = request.values.get("user_id")

    if str(user_id) == str(g.user.user_id):
        return "Cannot remove yourself", 400

    cursor = mysql.connection.cursor()
    cursor.execute("""
        DELETE FROM 
            club_members
        WHERE
            user_id = %s AND club_id = %s
    """, (user_id, club_id))
    return "Success!", 200

@app.route("/addLeader", methods = ["POST"])
@authenticate_leadership
def addLeader():
    club_id = request.values.get("club_id")
    user_id = request.values.get("user_id")

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE 
            club_members
        SET 
            is_leader = 1
        WHERE
            user_id = %s AND club_id = %s
    """, (user_id, club_id))
    return "Success!", 200

@app.route("/demoteLeader", methods = ["POST"])
@authenticate_leadership
def demoteLeader():
    club_id = request.values.get("club_id")
    user_id = request.values.get("user_id")

    if str(user_id) == str(g.user.user_id):
        return "Cannot remove yourself", 400

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE 
            club_members
        SET 
            is_leader = 0
        WHERE
            user_id = %s AND club_id = %s
    """, (user_id, club_id))
    return "Success!", 200

@app.route("/createTag", methods = ["POST"])
@authenticate_leadership
def createTag():
    club_id = request.values.get("club_id")
    tag_name = (request.values.get("tag_name") or "").strip().lower()[:16]

    if not tag_name:
        return "Missing tag name", 400

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO 
            tags
            (name)
        VALUES
            (%s)
        ON DUPLICATE KEY UPDATE
            tag_id = LAST_INSERT_ID(tag_id)
    """, (tag_name,))
    tag_id = cursor.lastrowid

    cursor.execute("""
        INSERT IGNORE INTO 
            club_tags
            (club_id, tag_id)
        VALUES
            (%s, %s)
    """, (club_id, tag_id))
    return json.dumps({"tag_id": tag_id, "name": tag_name})

@app.route("/deleteTag", methods = ["POST"])
@authenticate_leadership
def deleteTag():
    club_id = request.values.get("club_id")
    tag_id = request.values.get("tag_id")

    cursor = mysql.connection.cursor()
    cursor.execute("""
        DELETE FROM 
            club_tags
        WHERE
            club_id = %s AND tag_id = %s
    """, (club_id, tag_id))
    return "Success!", 200
