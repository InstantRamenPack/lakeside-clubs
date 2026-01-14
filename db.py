import os
from flask import current_app, g
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

class _DictCursorConnection:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        if not args and "cursorclass" not in kwargs and "cursor" not in kwargs:
            return self._conn.cursor(pymysql.cursors.DictCursor)
        return self._conn.cursor(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)

class MySQL:
    def __init__(self, app=None):
        self.engine = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.engine = self._create_engine(app)
        app.teardown_appcontext(self.teardown)

    def _create_engine(self, app):
        url = URL.create(
            "mysql+pymysql",
            username = app.config["MYSQL_USER"],
            password = app.config["MYSQL_PASSWORD"],
            host = app.config["MYSQL_HOST"],
            port = int(app.config["MYSQL_PORT"]),
            database = app.config["MYSQL_DB"],
        )
        ssl_ca = os.path.join(os.path.dirname(__file__), "tidb-ca.pem")
        return create_engine(
            url,
            pool_pre_ping = True,
            connect_args = {
                "ssl": {"ca": ssl_ca},
                "autocommit": True,
            },
        )

    @property
    def connection(self):
        if 'db_conn' not in g:
            if self.engine is None:
                self.engine = self._create_engine(current_app)
            g.db_conn = _DictCursorConnection(self.engine.raw_connection())
        return g.db_conn

    def teardown(self, exception):
        db = g.pop('db_conn', None)
        if db is not None:
            db.close()

mysql = MySQL()

def init(app):
    mysql.init_app(app)
