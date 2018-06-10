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
    Title:              Printers
    Description:        Takes ticket_id from freshservice webhook from Printers service request. Connects to Fresh
                        service API to retrieve service request items and requestor details. In Freshservice all of
                        the printers are shown as checkboxes, all values are sent here in JSON format, being
                        True or False. For every value (printer) sent, the powershell script printers.ps1 is ran.
                        The ps1 script will add user the user in to the appropriate group to add the printer. Will
                        then connect to API to add a reply to the ticket letting the user know the request is completed
                        and to restart their machines.
    Powershell Script:  printers.ps1
    Parameters:         Printer:        [STRING] (Required)
                        Username:       [STRING] (Required)
                        domain:         [STRING] (Required)
                                        Used in the Powershell script to determine which domain
                                        the user comes from. Important, as wrong users could get
                                        added if they have the same name.
    Notes:              Need to work out how to get status codes from the Powershell script as basic
                        success/failure report. Idea is 0 for success, 1 for can't find username,
                        2 for other failure. This can atleast give an agent an idea of why the
                        service request didn't work.
    """
    api_key = os.environ['api_key']
    domain = "servicedesk.synseal.com"
    password = "x"
    ticket_id = ticket_id.split("-")[1]

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
            print(requested_items[0]['requested_item']['requested_item_values'][i])

            subprocess.call(["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe",
                             "C:\\inetpub\\wwwroot\\SYN-FreshServiceAPI\\deploy\\printers.ps1 "
                             "-Printer {} -Username {} -Domain {}".format(i, username, domain)])
            print(i, username, domain)

    # script completes, update ticket to let user know to reboot
    domain = "synsealitservicedesk.freshservice.com"
    password = "x"

    headers = {'Content-Type': 'application/json'}

    note = {
        "body": "Printers have been added to your user account. Please reboot your PC for these change to take "
                "affect."
    }

    r = requests.post("https://" + domain + "/api/v2/tickets/" + ticket_id + "/reply", auth=(api_key, password),
                      headers=headers, data=json.dumps(note))


api_v1_blueprint = Blueprint('api_v1_blueprint', __name__)


@api_v1_blueprint.route('/service_requests/printers', methods=['POST'])
def post_printers():
    """
    Title:              Post Printers
    Description:        Add users to groups for file share access from Service Requests

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


application = Flask(__name__)
application.logger.addHandler(handler)
application.register_blueprint(api_v1_blueprint, url_prefix='/')

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)
