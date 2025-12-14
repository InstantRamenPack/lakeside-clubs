import json, re
from functools import wraps

from flask import g, redirect, render_template, request, session, url_for

from app import app, authenticate_leadership
from db import mysql
from md_utils import render_markdown_plain, render_markdown_safe

@app.route("/club")
def club():
    club_id = request.values.get("id")
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT
            c.*,
            MAX(CASE WHEN cm.user_id = %s THEN cm.membership_type END) AS membership_type,
            (
                SELECT 
                    JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'id', t.id,
                            'name', t.name
                        )
                    )
                FROM
                    raymondz_club_tags ct
                LEFT JOIN
                    raymondz_tags t ON t.id = ct.tag_id
                WHERE
                    ct.club_id = c.id
            ) AS tags,
            JSON_ARRAYAGG(
                CASE WHEN 
                    cm.membership_type = 1 
                THEN 
                    JSON_OBJECT(
                        'id', u.id, 
                        'first_name', u.first_name,
                        'last_name', u.last_name,
                        'name', u.name, 
                        'email', u.email
                    )
                END
            ) AS leaders,
            JSON_ARRAYAGG(
                CASE WHEN 
                    cm.membership_type = 0 
                THEN 
                    JSON_OBJECT(
                        'id', u.id, 
                        'first_name', u.first_name,
                        'last_name', u.last_name,
                        'name', u.name, 
                        'email', u.email
                    )
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

    # https://stackoverflow.com/a/1855104 on selecting after today
    cursor.execute("""
        SELECT 
            m.*
        FROM 
            raymondz_meetings m 
        WHERE 
            m.club_id = %s
        AND
            m.date >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 DAY)
        GROUP BY 
            m.id 
        ORDER BY
            m.date ASC,
            m.start_time ASC
    """, (club_id,))
    meetings = cursor.fetchall()
    for meeting in meetings:
        raw_description = meeting["description"]
        meeting["description"] = render_markdown_safe(raw_description)
        meeting["description_plain"] = render_markdown_plain(raw_description)

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
    return redirect(url_for("club", id = request.values.get("id"))) 

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

@app.route("/fetchMembers", methods = ["POST"])
@authenticate_leadership
def fetchMembers():
    club_id = request.values.get("id")
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT 
            u.email,
            cm.membership_type
        FROM 
            raymondz_club_members cm
        JOIN 
            raymondz_users u ON u.id = cm.user_id
        WHERE 
            cm.club_id = %s
        ORDER BY
            cm.membership_type DESC
    """, (club_id,))
    members = cursor.fetchall()

    return json.dumps(members)

@app.route("/importUsers", methods = ["POST"])
@authenticate_leadership
def importUsers():
    club_id = request.values.get("id")
    cursor = mysql.connection.cursor()

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
            raymondz_club_members
        WHERE
            user_id = %s AND club_id = %s
    """, (user_id, club_id))
    mysql.connection.commit()
    return "Success!", 200

@app.route("/addLeader", methods = ["POST"])
@authenticate_leadership
def addLeader():
    club_id = request.values.get("club_id")
    user_id = request.values.get("user_id")

    cursor = mysql.connection.cursor()
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
            raymondz_club_members
        SET 
            membership_type = 0
        WHERE
            user_id = %s AND club_id = %s
    """, (user_id, club_id))
    mysql.connection.commit()
    return "Success!", 200
