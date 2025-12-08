from flask_pymysql import MySQL

mysql = MySQL()

def init_db(app):
    mysql.init_app(app)
