from flask import render_template, Blueprint, jsonify, request

api_v1_blueprint = Blueprint('api_v1_blueprint', __name__)


@api_v1_blueprint.route('/service_requests/printers', methods=['POST'])
def post_printers():
    """
    Title:              Add user to printer group
    URL:                /service_requests/printers
    METHOD:             POST
    URL PARAMS:         N/A
    DATA PARAMS:
                { 'request': {
                            'ticket_id': [STRING],
                            'printer': [STRING],
                            'username': [STRING]
                            }
                }

    SUCCESS RESPONSE:
                CODE:       200
                CONTENT:    { ticket_id: [STRING] }

    ERROR RESPONSE:
                CODE:       401 UNAUTHORISED
                CONTENT:    { 'error': 'not authenticated' }

                CODE:       422 Unprocessable ENTRY
                CONTENT:    { 'error': 'printer doesn't exist' }

                CODE:       422 Unprocessable ENTRY
                CONTENT:    { 'error': 'user doesn't exist' }
    """
    return "Printers test"


@api_v1_blueprint.route('/service_requests/file_shares', methods=['POST', 'GET'])
def post_file_shares():
    """
    Title:              Add user to file share group
    URL:                /service_requests/file_shares
    METHOD:             POST
    DATA PARAMS:
                { 'request': {
                            'ticket_id': [STRING],
                            'file_share': [STRING],
                            'username': [STRING]
                            }
                }

    SUCCESS RESPONSE:
                CODE:       200
                CONTENT:    { 'ticket_id': [STRING] }

    ERROR RESPONSE:
                CODE:       401 UNAUTHORISED
                CONTENT:    { 'error': 'not authenticated' }

                CODE:       422 UNPROCESSABLE ENTRY
                CONTENT:    { 'error': 'file share doesn't exist' }

                code:       422 UNPROCESSABLE ENTRY
                CONTENT:    { 'error': 'username doesn't exist' }

    NOTES:
                Runs a powershell script dependent on the variables
                sent through from Freshservice, adding the user into
                the group.
    """
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "C:\\deploy\\{0}.ps1".format(script)]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    out, err = p.communicate()
    return "hello world"
