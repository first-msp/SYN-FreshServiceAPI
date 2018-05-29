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
    if request.method == 'POST':
        result = request.get_json(force=True)
        if not 'username' in result:
            return jsonify({"error": "username not supplied"}), 422
        if not 'file_share' in result:
            return jsonify({"error": "file share not supplied"}), 422
        if not 'ticket_id' in result:
            return jsonify({"error": "ticket_id not supplied"}), 422

        if not isinstance(result['username'], str):
            return jsonify({"error": "username not string"}), 422
        if not isinstance(result['file_share'], str):
            return jsonify({"error": "file share not string"}), 422
        if not isinstance(result['ticket_id'], str):
            return jsonify({"error": "ticket_id not string"}), 422
        import subprocess, sys
        p = subprocess.Popen(["powershell.exe",
                              "C:\\inetpub\\wwwroot\\FS-API1\\deploy\\file_shares.ps1 -Group {} -Username {}".format(
                                  result['file_share'],
                                  result['username'])])
        p.communicate()
        return jsonify({'ticket_id': result['ticket_id']})
    return jsonify({"data": "you got, got"})


