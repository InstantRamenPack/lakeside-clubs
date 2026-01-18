from flask import g, jsonify, render_template, request

from app import app, authenticate_leadership
from db import mysql
from meeting import Meeting

@app.route("/meetings", methods = ["GET"])
def meetings():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT 
            m.*,
            c.name AS club_name,
            cm.user_id IS NOT NULL AS is_member
        FROM 
            meetings m
        JOIN
            clubs c ON c.club_id = m.club_id
        LEFT JOIN
            club_members cm ON cm.club_id = c.club_id AND cm.user_id = %s
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
    meeting_rows = cursor.fetchall()

    meeting_objects = []
    for meeting in meeting_rows:
        m = Meeting.from_dict(meeting)
        m.club_name = meeting.get("club_name")
        m.is_member = bool(meeting.get("is_member"))
        meeting_objects.append(m)

    return render_template("meetings.html.j2", meetings = meeting_objects)

@app.route("/createMeeting", methods = ["POST"])
@authenticate_leadership
def createMeeting():
    meeting = {
        "club_id": request.values.get("club_id"),
        "title":request.values.get("title"),
        "description": request.values.get("description"),
        "start_time": request.values.get("start-time"),
        "end_time": request.values.get("end-time"),
        "date": request.values.get("date"),
        "location": request.values.get("location"),
        "is_meeting": request.values.get("is_meeting", "1") != "0",
        "is_leader": True
    }

    if not meeting["title"] or not meeting["description"]:
        return "Missing required fields", 400
    if meeting["is_meeting"]:
        if not meeting["start_time"] or not meeting["end_time"] or not meeting["date"] or not meeting["location"]:
            return "Missing required fields", 400
        if meeting["end_time"] < meeting["start_time"]:
            return "Invalid times", 400

    meeting = Meeting.from_dict(meeting).create()
    macros = app.jinja_env.get_template("macros.html.j2").make_module({"g": g})
    rendered_meeting = macros.render_meeting_card(meeting, meeting.is_leader, meeting.is_meeting, True)
    meeting.as_vector_store()

    return jsonify({"html": rendered_meeting, "is_meeting": meeting.is_meeting})

@app.route("/deleteMeeting", methods = ["POST"])
@authenticate_leadership
def deleteMeeting():
    meeting_id = request.values.get("meeting_id")
    meeting = Meeting.get(meeting_id)
    if not meeting:
        return "Not found", 404
    Meeting.delete(meeting_id)
    return "Success!", 200
