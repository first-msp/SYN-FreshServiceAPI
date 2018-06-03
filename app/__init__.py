from __future__ import absolute_import, unicode_literals
import os
from flask import Flask, Blueprint, request, jsonify
from celery import Celery
import time
import logging
from logging.handlers import RotatingFileHandler
handler=RotatingFileHandler('C:\\inetpub\\logs\\SYN-FreshServiceAPI\\log.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)

AUTHENTICATION_KEY = "disovnvecpic"

_basedir = os.path.abspath(os.path.dirname(__file__))
celeryapp = Celery('__init__', backend='rpc://', broker='pyamqp://')


@celeryapp.task()
def add_user_to_file_share(file_share, email, ticket_id):
    import subprocess, sys
    subprocess.call(["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe", "C:\\inetpub\\wwwroot\\SYN-FreshServiceAPI\\deploy\\file_shares.ps1 -Email {} -FileShare {}".format(email, file_share)])


api_v1_blueprint = Blueprint('api_v1_blueprint', __name__)


@api_v1_blueprint.route('/service_requests/file_shares', methods=['POST'])
def post_file_shares():
    """
    Title:              File Shares
    Description:        Executes celery task to add user to appropriate group for
                        file share access.
                        
                        File share group is determined by adding the name of the file
                        share into a template for the group e.g.
                        
                        RBAC-SERVER-01-Department-AccessLevel
                        becomes
                        RBAC-FILE-02-TechnicalConservatories-Read

                        spaces are removed from the string sent to the API (file_share).
                        
                        After task completion, user will be notified by setting the
                        the ticket to resolved and leaving a note to log off and back
                        on.

                        The email parameter is need to ensure Sheerframe users will be
                        added correctly. The Powershell script will need to connect to
                        Sheerframe DC. And to identify the user.
    URL:                /service_requests/file_shares
    METHOD:             POST
    DATA PARAMS:
                { 'request': {
                            'ticket_id': [STRING],
                            'file_share': [STRING],
                            'email': [STRING]
                            }
                }

    SUCCESS RESPONSE:
                CODE:       200
                CONTENT:    { "ticket_id": [STRING] }

    ERROR RESPONSE:
                CODE:       401 UNAUTHORISED
                CONTENT:    { "Error": "Request not authenticated." }

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { "Error": "File share is missing from the request." }

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { "Error": "Ticket ID is missing from the request." }

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { "Error": "Email is missing from the request." }

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { "Error": "Ticket ID is not a string." }

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { "Error": "File Share is not a string." }

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { "Error": "Email is not a string." }

    NOTES:
                Runs a celery task, which in turn runs a powershell script
                which add the user to the specified group. The celery task will
                also connect to Freshservice API and set the service request as
                resolved, with a note explaining to log off and back on.
                The authentication for connecting to the domain is stored within
                the powershell scripts.
    """
    if request.method == 'POST':
        result = request.get_json(force=True)
        print(result)
        """ validation on the request """
        if not 'file_share' in result:
            return jsonify({ "Error": "File share is missing from request."} ), 422
        if not 'ticket_id' in result:
            return jsonify({ "Error": "Ticket ID is missing from request."} ), 422
        if not 'email' in result:
            return jsonify({ "Error": "Email is missing from the request." }), 422

        if not isinstance(result['file_share'], str):
            return jsonify({ "Error": "File Share is not a string." }), 422
        if not isinstance(result['ticket_id'], str):
            return jsonify({ "Error": "Ticket ID is not a string." }), 422
        if not isinstance(result['email'], str):
            return jsonify({ "Error": "Email is not a string." }), 422
        application.logger.info(result['file_share'])
        
        add_user_to_file_share.delay(result['file_share'], result['email'], result['ticket_id'])
        return jsonify({'ticket_id': result['ticket_id']})


application = Flask(__name__)
application.logger.addHandler(handler)
application.register_blueprint(api_v1_blueprint, url_prefix='/')


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)
