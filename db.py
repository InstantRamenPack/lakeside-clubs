try:
    from flask_mysqldb import MySQL
except ImportError:
    import pymysql
    from flask import current_app, g

    class MySQL:
        def __init__(self, app=None):
            if app is not None:
                self.init_app(app)

        def init_app(self, app):
            app.teardown_appcontext(self.teardown)

        @property
        def connection(self):
            if 'db_conn' not in g:
                g.db_conn = pymysql.connect(
                    host=current_app.config["MYSQL_HOST"],
                    user=current_app.config["MYSQL_USER"],
                    password=current_app.config["MYSQL_PASSWORD"],
                    database=current_app.config["MYSQL_DB"],
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True,
                )
            return g.db_conn

        def teardown(self, exception):
            db = g.pop('db_conn', None)
            if db is not None:
                db.close()

mysql = MySQL()

def init_db(app):
    mysql.init_app(app)
