import json
import re

from rank_bm25 import BM25Okapi

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
    - Sort by weight, then club size, then club_id
    """

    cursor = mysql.connection.cursor()

    # collect members and tags per club without cross-joining members x tags
    cursor.execute("""
        SELECT
            c.club_id AS club_id,
            m.members AS members,
            t.tags AS tags
        FROM
            clubs c
        LEFT JOIN (
            SELECT
                club_id,
                JSON_ARRAYAGG(DISTINCT user_id) AS members
            FROM
                club_members
            GROUP BY
                club_id
        ) m ON m.club_id = c.club_id
        LEFT JOIN (
            SELECT
                club_id,
                JSON_ARRAYAGG(DISTINCT tag_id) AS tags
            FROM
                club_tags
            GROUP BY
                club_id
        ) t ON t.club_id = c.club_id
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

def search_clubs(query, rrf_k = 20):
    """
    Search clubs using embeddings and BM25 keyword search. 
    """

    # embedding search
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT
            meeting_id,
            club_id,
            clean_description,
            embedding
        FROM
            meetings
    """)
    meeting_rows = cursor.fetchall()

    query_embedding = client.embeddings.create(
        model = "text-embedding-3-small",
        input = query,
        dimensions = 1536,
    ).data[0].embedding

    embedding_rank = []
    for row in meeting_rows:
        similarity = sum(x * y for x, y in zip(query_embedding, json.loads(row.get("embedding"))))
        embedding_rank.append((row.get("meeting_id"), row.get("club_id"), similarity))
    embedding_rank.sort(key = lambda item: item[2], reverse = True)

    # BM25 search
    query_tokens = re.findall(r"[a-z0-9]+", query.lower())
    meeting_tokens = []
    for row in meeting_rows:
        meeting_tokens.append(re.findall(r"[a-z0-9]+", row.get("clean_description").lower()))

    bm25_scores = BM25Okapi(meeting_tokens).get_scores(query_tokens)
    bm25_rank = []
    for row, score in zip(meeting_rows, bm25_scores):
        bm25_rank.append((row.get("meeting_id"), row.get("club_id"), score))
    bm25_rank.sort(key = lambda item: item[2], reverse = True)

    # RRF to merge embedding and BM25 ranks
    rrf_scores = {}

    for rank, row in enumerate(embedding_rank, start = 1):
        meeting_id = row[0]
        if meeting_id is None:
            continue
        rrf_scores.setdefault(meeting_id, {"club_id": row[1], "score": 0.0})
        rrf_scores[meeting_id]["score"] += 1.0 / (rrf_k + rank)

    for rank, row in enumerate(bm25_rank, start = 1):
        meeting_id = row[0]
        if meeting_id is None:
            continue
        rrf_scores.setdefault(meeting_id, {"club_id": row[1], "score": 0.0})
        rrf_scores[meeting_id]["score"] += 1.0 / (rrf_k + rank)

    club_scores = {}
    club_counts = {}
    for entry in rrf_scores.values():
        club_id = entry["club_id"]
        club_scores[club_id] = club_scores.get(club_id, 0.0) + entry["score"]
        club_counts[club_id] = club_counts.get(club_id, 0) + 1

    for club_id, score in list(club_scores.items()):
        # change aggregating algorithm as necessary
        club_scores[club_id] = score / (club_counts.get(club_id, 1))

    club_rankings = sorted(
        club_scores.items(),
        key = lambda item: (-item[1], item[0])
    )

    return [club_id for club_id, _ in club_rankings]
