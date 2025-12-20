from flask import g, jsonify, redirect, render_template, request, session, url_for

from app import app, authenticate_leadership
from db import mysql
from md_utils import render_markdown_plain, render_markdown_safe

class Meeting:
    def __init__(self, club_id, title, description, start_time = None, end_time = None, date = None, location = None, is_meeting = True, is_leader = False, meeting_id = None, post_time = None):
        self.id = meeting_id
        self.club_id = club_id
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.date = date
        self.location = location
        self.is_meeting = bool(is_meeting)
        self.is_leader = bool(is_leader)
        self.post_time = post_time

    def description_safe(self):
        return render_markdown_safe(self.description)

    def description_plain(self):
        return render_markdown_plain(self.description)

    def create(self):
        cursor = mysql.connection.cursor()
        if self.is_meeting:
            cursor.execute("""
                INSERT INTO 
                    raymondz_meetings
                    (club_id, title, description, start_time, end_time, date, location, is_meeting)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, 1)
            """, (self.club_id, self.title, self.description, self.start_time, self.end_time, self.date, self.location))
        else:
            cursor.execute("""
                INSERT INTO 
                    raymondz_meetings
                    (club_id, title, description, is_meeting)
                VALUES 
                    (%s, %s, %s, 0)
            """, (self.club_id, self.title, self.description))
        mysql.connection.commit()
        self.id = cursor.lastrowid
        created = Meeting.get(self.id)
        if created:
            created.is_leader = self.is_leader
            return created
        return self

    @staticmethod
    def delete(meeting_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            DELETE FROM 
                raymondz_meetings
            WHERE 
                id = %s
        """, (meeting_id,))
        mysql.connection.commit()

    @staticmethod
    def get(meeting_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM raymondz_meetings WHERE id = %s
        """, (meeting_id,))
        meeting = cursor.fetchone()
        if not meeting:
            return None
        return Meeting.from_dict(meeting)

    @staticmethod
    def from_dict(meeting):
        return Meeting(
            meeting_id = meeting.get("id"),
            club_id = meeting.get("club_id"),
            title = meeting.get("title"),
            description = meeting.get("description"),
            start_time = meeting.get("start_time"),
            end_time = meeting.get("end_time"),
            date = meeting.get("date"),
            location = meeting.get("location"),
            is_meeting = meeting.get("is_meeting"),
            post_time = meeting.get("post_time")
        )

@app.route("/meetings", methods = ["GET"])
def meetings():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT 
            m.*,
            c.name AS club_name,
            cm.user_id IS NOT NULL AS is_member
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
    club_id = request.values.get("club_id")
    title = request.values.get("title")
    description = request.values.get("description")
    start_time = request.values.get("start-time")
    end_time = request.values.get("end-time")
    date = request.values.get("date")
    location = request.values.get("location")
    is_meeting = request.values.get("is_meeting", "1") != "0"

    if not title or not description:
        return "Missing required fields", 400
    if is_meeting:
        if not start_time or not end_time or not date or not location:
            return "Missing required fields", 400
        if end_time < start_time:
            return "Invalid times", 400

    meeting = Meeting.from_dict({
        "club_id": club_id,
        "title": title,
        "description": description,
        "start_time": start_time,
        "end_time": end_time,
        "date": date,
        "location": location,
        "is_meeting": is_meeting,
        "is_leader": True
    }).create()

    macros = app.jinja_env.get_template("macros.html.j2").make_module({"g": g})
    rendered_meeting = macros.render_meeting_card(meeting, meeting.is_leader, meeting.is_meeting, True)

    return jsonify({"html": rendered_meeting, "is_meeting": meeting.is_meeting})

@app.route("/deleteMeeting", methods = ["POST"])
@authenticate_leadership
def deleteMeeting():
    Meeting.delete(request.values.get("id"))
    return "Success!", 200
