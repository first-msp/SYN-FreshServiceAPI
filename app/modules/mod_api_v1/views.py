from flask import render_template, Blueprint, jsonify

api_v1_blueprint = Blueprint('api_v1_blueprint', __name__)


@api_v1_blueprint.route('/', methods=['GET'])
def index():
    """
    -Title:         Main Route
    -URL:           /
    -METHOD:         GET
    -URL PARAMS
        -Required
            -ID: [STRING]
        -Optional
            -NAME:  [STRING]
    -Successful
    """
    return "Hello world."