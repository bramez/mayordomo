import logging

from flask import Flask, make_response, request

from allow_decorator import crossdomain
from mayordomo_service import MayordomoService

app = Flask(__name__)
mayordomo = MayordomoService()

logger = logging.getLogger("mayordomo")
hdlr = logging.FileHandler("/var/log/mayordomo.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)


@app.route('/devices', methods=['GET'])
@crossdomain(origin='*')
def get_devices():
    list_of_devices = mayordomo.get_serialized_devices()
    return list_of_devices


@app.route("/devices", methods=["POST"])
@crossdomain(origin='*')
def post_devices():
    mayordomo.switch_on_all_devices()
    return make_response("Good morning!", 201)


@app.route("/devices", methods=["DELETE"])
@crossdomain(origin='*')
def delete_devices():
    mayordomo.switch_off_all_devices()
    return make_response("Good night!", 200)


@app.route("/devices/<name>/rele", methods=["OPTIONS"])
@crossdomain(origin='*')
def options(name):
    return make_response("", 200)


@app.route("/devices/<name>/rele", methods=["PUT"])
@crossdomain(origin='*')
def update_rele(name):
    name = name.lower()

    rele = request.json
    if 'soft_status' not in rele:
        return make_response("please set the status property to true or false", 400)

    if rele['soft_status']:
        mayordomo.switch_on_rele(name)
    else:
        mayordomo.switch_off_rele(name)
    formatted_message = "Good morning '{}'!".format(name)
    return make_response(formatted_message, 201)


if __name__ == "__main__":
    mayordomo.start()
    app.run(host="192.168.0.18", port=8080)
