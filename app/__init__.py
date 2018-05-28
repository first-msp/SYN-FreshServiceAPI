import os
from flask import Flask

_basedir = os.path.abspath(os.path.dirname(__file__))

application = Flask(__name__)
application.config.from_object('app.settings.local')

from app.database import init_db
init_db()

from app.modules.mod_api_v1.views import main_blueprint
application.register_blueprint(main_blueprint, url_prefix='/user')
