import json
from datetime import datetime

from flask import g, redirect, render_template, request, session, url_for

from app import app, authenticate_leadership
from db import mysql
from md_utils import render_markdown_plain, render_markdown_safe

@app.route("/meetings", methods = ["GET"])
def meetings():
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
            (m.is_meeting = 1 AND m.date >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 DAY))
        OR
            (m.is_meeting = 0 AND m.post_time >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 MONTH))
        ORDER BY
            m.is_meeting DESC,
            CASE WHEN m.is_meeting = 1 THEN m.date END ASC,
            CASE WHEN m.is_meeting = 1 THEN m.start_time END ASC,
            CASE WHEN m.is_meeting = 0 THEN m.post_time END DESC
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
    is_meeting = request.values.get("is_meeting", "1") != "0"

    cursor = mysql.connection.cursor()
    if not title or not description:
        return "Missing required fields", 400
    if is_meeting:
        if not start_time or not end_time or not date or not location:
            return "Missing required fields", 400
        if end_time < start_time:
            return "Invalid times", 400

    if is_meeting:
        cursor.execute("""
            INSERT INTO 
                raymondz_meetings
                (club_id, title, description, start_time, end_time, date, location, is_meeting)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s, 1)
        """, (club_id, title, description, start_time, end_time, date, location))
    else:
        cursor.execute("""
            INSERT INTO 
                raymondz_meetings
                (club_id, title, description, is_meeting)
            VALUES 
                (%s, %s, %s, 0)
        """, (club_id, title, description))
    mysql.connection.commit()
    meeting_id = cursor.lastrowid

    description_html = render_markdown_safe(description)
    description_plain = render_markdown_plain(description)

    if is_meeting:
        meeting_data = {
            "id": meeting_id,
            "club_id": club_id,
            "title": title,
            "description": description_html,
            "description_plain": description_plain,
            "date": datetime.strptime(date, "%Y-%m-%d").date().strftime("%A, %b %-d"),
            "time_range": f"{start_time} - {end_time}",
            "location": location,
            "is_meeting": 1
        }
    else:
        meeting_data = {
            "id": meeting_id,
            "club_id": club_id,
            "title": title,
            "description": description_html,
            "description_plain": description_plain,
            "post_time": datetime.now().strftime("%A, %b %-d %I:%M %p"),
            "is_meeting": 0
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
