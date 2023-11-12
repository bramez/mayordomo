from flask import Flask, make_response, request

from allow_decorator import crossdomain
from technical_service import TechnicalService

app = Flask(__name__)
technical_service = TechnicalService()


@crossdomain(origin='*')
@app.route("/devices", methods=["GET"])
def get_devices():
    list_of_devices = technical_service.get_serialized_devices()
    return list_of_devices


@crossdomain(origin='*')
@app.route("/devices", methods=["POST"])
def post_devices():
    technical_service.switch_on_all_devices()
    return make_response("Good morning!", 201)


@crossdomain(origin='*')
@app.route("/devices", methods=["DELETE"])
def delete_devices():
    technical_service.switch_off_all_devices()
    return make_response("Good night!", 200)


@crossdomain(origin='*')
@app.route("/devices/<name>/rele", methods=["PUT"])
def update_rele(name):
    name = name.lower()

    rele = request.json
    if 'rele_status' not in rele:
        return make_response("please set the status property to true or false", 400)

    if rele['rele_status']:
        technical_service.switch_on_rele(name)
    else:
        technical_service.switch_off_rele(name)
    formatted_message = "Good morning '{}'!".format(name)
    return make_response(formatted_message, 201)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=18080, debug=True)  # 0-65535 (16 bits)
