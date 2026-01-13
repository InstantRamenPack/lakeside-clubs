import json

import config
from app import client
from db import mysql

def recommend_club_ids(user_id, user_weight_factor = 4, tag_weight_factor = 1, limit = None):
    """
    Rank clubs by relevancy.

    - Let target user be U
    - Let user_weight w(U') be sum of 1/|C| for clubs C that U' and U share
    - Let club_user_weight of club C be sum w(U') for U' in C, divided by |C|
    - Similarly calculate club_tag_weight
    - Final weight is scaled on club_user_weight and club_tag_weight
    - Sort by weight, then club size, then id
    """

    cursor = mysql.connection.cursor()

    # collect members and tags per club
    cursor.execute("""
        SELECT 
            c.id AS club_id,
            JSON_ARRAYAGG(cm.user_id) AS members,
            JSON_ARRAYAGG(ct.tag_id) AS tags
        FROM 
            raymondz_clubs c
        LEFT JOIN 
            raymondz_club_members cm ON cm.club_id = c.id
        LEFT JOIN 
            raymondz_club_tags ct ON ct.club_id = c.id
        GROUP BY 
            c.id
    """)

    club_ids = []
    club_members = {}
    club_tags = {}
    user_clubs = []

    for row in cursor.fetchall():
        cid = row["club_id"]
        club_ids.append(cid)

        members = [m for m in json.loads(row["members"] or "[]") if m is not None]
        tags = [t for t in json.loads(row["tags"] or "[]") if t is not None]
        members = list(set(members))
        tags = list(set(tags))

        club_members[cid] = members
        club_tags[cid] = tags
        if user_id in members:
            user_clubs.append(cid)

    if not user_clubs:
        return []

    # user_weights
    user_weights = {}
    for club_id in user_clubs:
        for member in club_members.get(club_id, []):
            user_weights[member] = user_weights.get(member, 0.0) + (1.0 / len(club_members.get(club_id, [])))

    # tag_weights
    tag_weights = {}
    for club_id in user_clubs:
        for tag_id in club_tags.get(club_id, []):
            tag_weights[tag_id] = tag_weights.get(tag_id, 0.0) + (1.0 / len(club_tags.get(club_id, [])))

    # total weights
    weights = []
    for club_id in club_ids:
        if club_id in user_clubs:
            continue

        club_size = len(club_members.get(club_id, []))
        club_user_weight = 0.0
        for member in club_members.get(club_id, []):
            club_user_weight += user_weights.get(member, 0.0) / len(club_members.get(club_id, []))

        club_tag_weight = 0.0
        for tag_id in club_tags.get(club_id, []):
            club_tag_weight += tag_weights.get(tag_id, 0.0) / len(club_tags.get(club_id, []))

        weights.append((user_weight_factor * club_user_weight + tag_weight_factor * club_tag_weight, club_size, club_id))

    # sort
    weights.sort(key = lambda item: (-item[0], -item[1], item[2]))
    if limit is not None:
        weights = weights[:limit]

    return [club_id for _, _, club_id in weights]

def search_clubs(query, n):
    results = client.vector_stores.search(
        vector_store_id = config.OPENAI_VECTOR_STORE_ID,
        query = query,
        max_num_results = 10
    )

    club_scores = {}
    for item in results.data:
        attributes = item.attributes
        club_id = attributes.get("club_id")
        club_scores[club_id] = club_scores.get(club_id, 0.0) + float(item.score)

    ranked = sorted(
        club_scores.items(),
        key = lambda pair: (-pair[1], str(pair[0]))
    )
    
    return [club_id for club_id, _ in ranked[:n]]
