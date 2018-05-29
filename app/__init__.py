import os
from flask import Flask

import logging
from logging.handlers import RotatingFileHandler
handler=RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)


_basedir = os.path.abspath(os.path.dirname(__file__))

application = Flask(__name__)
application.logger.addHandler(handler)
from app.modules.mod_api_v1.views import api_v1_blueprint
application.register_blueprint(api_v1_blueprint, url_prefix='/')