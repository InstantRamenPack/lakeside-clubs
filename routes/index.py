from flask import g, render_template

import algorithm
from app import app
from club import Club


@app.route("/")
def index():
    club_rows = Club.all_details()
    club_rows.sort(key = lambda club: club.size or 0, reverse = True)
    clubs = {}
    lead_order = []
    joined_order = []
    other_order = []

    for club in club_rows:
        club_id = club.club_id
        clubs[club_id] = club

        if club.is_leader:
            lead_order.append(club_id)
        elif club.is_member:
            joined_order.append(club_id)
        else:
            other_order.append(club_id)

    if g.user.authenticated:
        other_order = [
            club_id for club_id in algorithm.recommend_club_ids(g.user.user_id)
            if club_id in other_order
        ]

    return render_template(
        "index.html.j2", 
        clubs = clubs, 
        lead_order = lead_order, 
        joined_order = joined_order, 
        other_order = other_order
    )
