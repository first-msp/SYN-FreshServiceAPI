#
from __future__ import absolute_import, unicode_literals
import os
from flask import Flask, Blueprint, request, jsonify
from celery import Celery
import time
import logging
from logging.handlers import RotatingFileHandler
import requests
import json
import os
logging.basicConfig()
handler = RotatingFileHandler('C:\\inetpub\\logs\\SYN-FreshServiceAPI\\log.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)

_basedir = os.path.abspath(os.path.dirname(__file__))
celeryapp = Celery('__init__', backend='rpc://', broker='pyamqp://')


@celeryapp.task()
def add_printer_to_user(ticket_id):
    """

    0:param ticket_id:
    :return:
    """
    api_key = os.environ['api_key']
    domain = "servicedesk.synseal.com"
    password = "x"
    ticket_id = ticket_id

    ticket_info_url = "http://{}/helpdesk/tickets/{}.json".format(domain, ticket_id)
    requested_items_url = "http://{}/helpdesk/tickets/{}/requested_items.json".format(domain, ticket_id)
    requestor_info = "http://servicedesk.synseal.com/itil/requesters/7000356305.json"

    # make api requests
    ticket_info_response = requests.get(ticket_info_url, auth=(api_key, password))
    requested_items_response = requests.get(requested_items_url, auth=(api_key, password))
    ticket_info = json.loads(ticket_info_response.content)
    requested_items = json.loads(requested_items_response.content)

    requestor_info_url = "http://{}/itil/requesters/{}.json".format(domain,
                                                                    ticket_info['helpdesk_ticket']['requester_id'])
    requestor_info_response = requests.get(requestor_info_url, auth=(api_key, password))
    requestor_info = json.loads(requestor_info_response.content)

    print("Requested by: {}".format(ticket_info['helpdesk_ticket']['requester_name']))
    print("Requestor Email: {}".format(requestor_info['user']['email']))
    print("Request: {}".format(requested_items[0]['requested_item']['requested_item_values']))

    username, domain = requestor_info['user']['email'].split("@")

    import subprocess, sys
    for i in requested_items[0]['requested_item']['requested_item_values'].keys():
        # running the powershell script below
        if requested_items[0]['requested_item']['requested_item_values'][i]:
            print requested_items[0]['requested_item']['requested_item_values'][i]
            subprocess.call(["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe",
                             "C:\\inetpub\\wwwroot\\SYN-FreshServiceAPI\\deploy\\printers.ps1 "
                             "-FileShare {} -Username {} -Domain {}".
                            format(requested_items[0]['requested_item']['requested_item_values'][i],
                                   username, domain)])


@celeryapp.task()
def add_user_to_file_share(ticket_id):
    """
    Title:              add_user_to_file_share
    Description:        Runs powershell script with required parameters to add a user into a
                        group. There are Group Policies built into the domain which will then
                        add the file share dependent on the group membership.
    Powershell Script:  file_shares.ps1
    Parameters:         file_share:     [STRING] (Required)
                                        Using this and a template provided, the file share group
                                        name can be created.
                        username:       [STRING] (Required)
                                        Passed to Powershell to add the right user into the group.
                        ticket_id:      [STRING] (Required)
                                        Used to update the ticket details and set the ticket as
                                        resolved.
                        domain:         [STRING] (Required)
                                        Used in the Powershell script to determine which domain
                                        the user comes from. Important, as wrong users could get
                                        added if they have the same name.
    Notes:              Need to work out how to get status codes from the Powershell script as basic
                        success/failure report. Idea is 0 for success, 1 for can't find username,
                        2 for other failure. This can atleast give an agent an idea of why the
                        service request didn't work.
    """
    # connect to freshservice api and pull down service request information to use
    # information needed
    # person who needs it their email, values of chosen printer

    """
    import subprocess, sys
    # running the powershell script below
    subprocess.call(["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe",
                     "C:\\inetpub\\wwwroot\\SYN-FreshServiceAPI\\deploy\\file_shares.ps1 "
                     "-FileShare {} -Username {} -Domain {}".format(file_share, username, domain)])
    # will have freshservice api interaction here to set ticket as resolved and leave note
    print("{}".format(ticket_id))"""


api_v1_blueprint = Blueprint('api_v1_blueprint', __name__)


@api_v1_blueprint.route('/service_requests/printers', methods=['POST'])
def post_printers():
    """

    :return:
    """
    if request.method == 'POST':  # only accept POST requests
        result = request.get_json(force=True)  # get all json data from request
        print(result)
        # validate all required parameters are present
        if 'ticket_id' not in result:
            return jsonify({"Error": "Ticket ID is missing from request."}), 422

        # validate parameters are correct type
        if not isinstance(result['ticket_id'], str):
            return jsonify({"Error": "Ticket ID is not a string."}), 422

        # validate length of parameters
        if not len(result["ticket_id"]) > 1:
            return jsonify({"Error": "Ticket ID needs to be longer than 1."}), 422

        # creates new celery task to add user to a file share group and update the ticket after
        try:
            add_printer_to_user.delay(result['ticket_id'])
        except Exception as e:
            application.logger.error("{}".format(result['ticket_id']))

        return jsonify({'ticket_id': result['ticket_id']})  # returns ticket ID on successful start


@api_v1_blueprint.route('/service_requests/file_shares', methods=['POST'])
def post_file_shares():
    """
    Title:              File Shares
    Description:        Add users to groups for file share access from Service Requests
                        submitted through Freshservice.
                        This endpoint is an Observer webhook in Freshservice, which is
                        used every time an approval for a File Share Service Request is made.
                        Observer sends the relevant data to this endpoint through a POST request.
                        Using this data a Celery task is started which runs a Powershell script,
                        which actually adds the user into the group. All of the logic determining
                        which group is supplied to the Powershell script is done in this function.

                        Powershell Script requirements:
                        PSScript.ps1 -FileShare -Username -Domain

                        File share group is determined by adding the name of the file
                        share into a template for the group e.g.
                        
                        RBAC-SERVER-01-Department-AccessLevel
                        becomes
                        RBAC-FILE-02-TechnicalConservatories-Read

                        spaces are removed from the string sent to the endpoint (file_share).
                        
                        After celery task completion, user will be notified by setting the
                        the ticket to resolved and leaving a note to log off and back
                        on.

                        The email parameter is needed from Freshservice, so we can determine the
                        domain of the user. This is to ensure Sheerframe users will be added
                        correctly as they're on a different domain.
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

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { "Error": "Ticket ID needs to be longer than 1." }

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { "Error": "File Share needs to be longer than 1." }

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { "Error": "Email needs to be longer than 1." }

                CODE:       401 NOT FOUND
                CONTENT:    { "Error": "Incorrect method or URL used." }
    """
    if request.method == 'POST':  # only accept POST requests
        result = request.get_json(force=True)  # get all json data from request
        print(result)
        # validate all required parameters are present
        if 'file_share' not in result:
            return jsonify({"Error": "File share is missing from request."}), 422
        if 'ticket_id' not in result:
            return jsonify({"Error": "Ticket ID is missing from request."}), 422
        if 'email' not in result:
            return jsonify({"Error": "Email is missing from the request."}), 422

        # validate parameters are correct type
        if not isinstance(result["file_share"], str):
            return jsonify({"Error": "File Share is not a string."}), 422
        if not isinstance(result['ticket_id'], str):
            return jsonify({"Error": "Ticket ID is not a string."}), 422
        if not isinstance(result['email'], str):
            return jsonify({"Error": "Email is not a string."}), 422

        # validate length of parameters
        if not len(result["file_share"]) > 1:
            return jsonify({"Error": "File Share needs to be longer than 1."}), 422
        if not len(result["email"]) > 1:
            return jsonify({"Error": "Email needs to be longer than 1."}), 422
        if not len(result["ticket_id"]) > 1:
            return jsonify({"Error": "Ticket ID needs to be longer than 1."}), 422

        # creates new celery task to add user to a file share group and update the ticket after
        try:
            add_user_to_file_share.delay(result['file_share'], result['email'], result['ticket_id'])
        except Exception as e:
            application.logger.error("{} {} {}".format(result['file_share'], result['email'], result['ticket_id']))

        return jsonify({'ticket_id': result['ticket_id']})  # returns ticket ID on successful start


application = Flask(__name__)
application.logger.addHandler(handler)
application.register_blueprint(api_v1_blueprint, url_prefix='/')

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)
