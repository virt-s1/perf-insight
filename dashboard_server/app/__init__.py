import logging

from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.commen import MyIndexView
import time
from flask import Response

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")
db = SQLA(app)
# appbuilder = AppBuilder(app, db.session)
appbuilder = AppBuilder(app, db.session, indexview=MyIndexView)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@app.route('/progress')
def progress():
    def generate():
        x = 100
        while x >= 0:
            yield "data:" + str(x) + "\n\n"
            x = x - 1
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream')


from . import models, views  # noqa
