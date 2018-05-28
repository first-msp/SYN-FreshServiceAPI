import os
from flask import Flask

_basedir = os.path.abspath(os.path.dirname(__file__))

application = Flask(__name__)

from app.modules.mod_api_v1.views import api_v1_blueprint
application.register_blueprint(api_v1_blueprint, url_prefix='/')
