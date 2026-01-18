from flask import g, jsonify, render_template, request

from app import app, authenticate_leadership
from meeting import Meeting

@app.route("/meetings", methods = ["GET"])
def meetings():
    meeting_objects = Meeting.all_meetings()
    return render_template("meetings.html.j2", meetings = meeting_objects)

@app.route("/createMeeting", methods = ["POST"])
@authenticate_leadership
def createMeeting():
    meeting = {
        "club_id": request.values.get("club_id"),
        "title": request.values.get("title"),
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
