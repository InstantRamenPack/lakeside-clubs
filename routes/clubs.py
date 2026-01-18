import json, re

from flask import g, redirect, render_template, render_template_string, request, session, url_for

from app import app, authenticate_leadership
from club import Club

@app.route("/club", methods = ["GET"])
def club():
    club_id = request.values.get("club_id")
    club = Club(club_id)
    if not club.load_details():
        return "Unknown club", 404
    if not club.tags:
        club.tags = []

    meetings = []
    macros = app.jinja_env.get_template("macros.html.j2").make_module({"g": g})
    for meeting in club.meetings:
        meeting.is_leader = bool(club.is_leader)
        meeting.rendered_card = macros.render_meeting_card(
            meeting,
            meeting.is_leader,
            meeting.is_meeting,
            True
        )
        meetings.append(meeting)

    return render_template("club.html.j2", club = club, meetings = meetings)   

@app.route("/joinClub", methods = ["GET", "POST"])
def joinClub():
    if not g.user.authenticated:
        session["next"] = request.url
        return redirect(url_for("login"))
    
    club = Club(request.values.get("club_id"))
    club.add_member(g.user.user_id)
    return redirect(url_for("club", club_id = request.values.get("club_id"))) 

@app.route("/leaveClub", methods = ["POST"])
def leaveClub():
    club = Club(request.values.get("club_id"))
    club.remove_member(g.user.user_id)
    return "Success!", 200

@app.route("/fetchMembers", methods = ["POST"])
@authenticate_leadership
def fetchMembers():
    club_id = request.values.get("club_id")
    club = Club(club_id)
    leaders = club.leaders()
    members = club.members()
    payload = (
        [{"email": user.get("email"), "is_leader": 1} for user in leaders] +
        [{"email": user.get("email"), "is_leader": 0} for user in members]
    )
    return json.dumps(payload)

@app.route("/importUsers", methods = ["POST"])
@authenticate_leadership
def importUsers():
    club_id = request.values.get("club_id")
    data = request.values.get("data") or ""

    # only @lakesideschool.org emails
    emails = re.findall(r"[A-Za-z0-9._%+-]+@lakesideschool\.org", data)
    emails = [e.lower() for e in emails]
    emails = list(dict.fromkeys(emails)) # deduplicate
    if not emails:
        return json.dumps({"new_members": [], "rendered_members": []})
    
    club = Club(club_id)
    new_members = club.import_emails(emails)
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

    club = Club(club_id)
    club.remove_member(user_id)
    return "Success!", 200

@app.route("/addLeader", methods = ["POST"])
@authenticate_leadership
def addLeader():
    club_id = request.values.get("club_id")
    user_id = request.values.get("user_id")

    club = Club(club_id)
    club.add_leader(user_id, True)
    return "Success!", 200

@app.route("/demoteLeader", methods = ["POST"])
@authenticate_leadership
def demoteLeader():
    club_id = request.values.get("club_id")
    user_id = request.values.get("user_id")

    if str(user_id) == str(g.user.user_id):
        return "Cannot remove yourself", 400

    club = Club(club_id)
    club.demote_leader(user_id, False)
    return "Success!", 200

@app.route("/createTag", methods = ["POST"])
@authenticate_leadership
def createTag():
    club_id = request.values.get("club_id")
    tag_name = (request.values.get("tag_name") or "").strip().lower()[:16]

    if not tag_name:
        return "Missing tag name", 400

    tag = Club.create_tag(tag_name)
    club = Club(club_id)
    club.add_tag(tag["tag_id"])
    return json.dumps(tag)

@app.route("/deleteTag", methods = ["POST"])
@authenticate_leadership
def deleteTag():
    club_id = request.values.get("club_id")
    tag_id = request.values.get("tag_id")

    club = Club(club_id)
    club.remove_tag(tag_id)
    return "Success!", 200
