from datetime import datetime, time, date as date_cls

from db import mysql
from md_utils import render_markdown_plain, render_markdown_safe


class Meeting:
    def __init__(self, club_id, title, description, start_time = None, end_time = None, date = None, location = None, is_meeting = True, is_leader = False, meeting_id = None, post_time = None):
        self.id = meeting_id
        self.club_id = club_id
        self.title = title
        self.description = description
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)
        self.date = self._parse_date(date)
        self.location = location
        self.is_meeting = bool(is_meeting)
        self.is_leader = bool(is_leader)
        self.post_time = self._parse_datetime(post_time)

    @staticmethod
    def _parse_time(value):
        if value is None or isinstance(value, time):
            return value
        if isinstance(value, str) and value:
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(value, fmt).time()
                except ValueError:
                    continue
        return None

    @staticmethod
    def _parse_date(value):
        if value is None or isinstance(value, date_cls):
            return value
        if isinstance(value, str) and value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_datetime(value):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    def description_safe(self):
        return render_markdown_safe(self.description or "")

    def description_plain(self):
        return render_markdown_plain(self.description or "")

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
        return cursor.rowcount

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
            is_leader = meeting.get("is_leader", False),
            post_time = meeting.get("post_time")
        )
