import json

from flask import g, redirect, render_template, request, session, url_for

try:
    from app import app, authenticate_leadership
    from db import mysql
except ImportError:
    from public.RaymondZ.finalproject.app import app, authenticate_leadership  # type: ignore
    from public.RaymondZ.finalproject.db import mysql  # type: ignore

from md_utils import render_markdown_plain, render_markdown_safe

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
                WHEN cm.user_id IS NOT NULL THEN 1
                ELSE 0
            END AS member_status
        FROM 
            raymondz_meetings m
        JOIN
            raymondz_clubs c ON c.id = m.club_id
        LEFT JOIN
            raymondz_club_members cm ON cm.club_id = c.id AND cm.user_id = %s
        WHERE
            m.date >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 DAY)
        ORDER BY
            m.date ASC,
            m.start_time ASC
    """, (g.user.user_id,))
    meetings = cursor.fetchall()

    for meeting in meetings:
        meeting["description"] = render_markdown_safe(meeting["description"])

    return render_template("meetings.html.j2", meetings = meetings)

@app.route("/createMeeting", methods = ["POST"])
@authenticate_leadership
def createMeeting():
    club_id = request.values.get("club_id")
    title = request.values.get("title")
    description = request.values.get("description")
    start_time = request.values.get("start-time")
    end_time = request.values.get("end-time")
    date = request.values.get("date")
    location = request.values.get("location")

    cursor = mysql.connection.cursor()
    if not title or not description or not start_time or not end_time or not date or not location:
        return "Missing required fields", 400
    if end_time < start_time:
        return "Invalid times", 400

    cursor.execute("""
        INSERT INTO 
            raymondz_meetings
            (club_id, title, description, start_time, end_time, date, location)
        VALUES 
            (%s, %s, %s, %s, %s, %s, %s)
    """, (club_id, title, description, start_time, end_time, date, location))
    mysql.connection.commit()
    meeting_id = cursor.lastrowid

    description_html = render_markdown_safe(description)
    description_plain = render_markdown_plain(description)

    meeting_data = {
        "id": meeting_id,
        "club_id": club_id,
        "title": title,
        "description": description_html,
        "description_plain": description_plain,
        "date": date,
        "time_range": f"{start_time} - {end_time}",
        "location": location
    }

    return json.dumps(meeting_data)

@app.route("/deleteMeeting", methods = ["POST"])
@authenticate_leadership
def deleteMeeting():
    meeting_id = request.values.get("id")

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT club_id FROM raymondz_meetings WHERE id = %s
    """, (meeting_id,))
    meeting = cursor.fetchone()
    if not meeting:
        return "Not found", 404

    cursor.execute("""
        DELETE FROM 
            raymondz_meetings
        WHERE 
            id = %s
    """, (meeting_id,))
    mysql.connection.commit()
    return "Success!", 200
