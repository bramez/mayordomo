#!/usr/bin/env python

import json, logging

from flask import Flask, jsonify, request

from allow_decorator import crossdomain
from old_mayordomo_services import MayordomoServices

logger = logging.getLogger("mayordomo")
hdlr = logging.FileHandler("/var/log/mayordomo.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

mayordomo = MayordomoServices()

# set the project root directory as the static folder, you can set others.
app = Flask(__name__)


@crossdomain(origin='*')
@app.route('/')
def hello():
    return app.send_static_file('index.html')


@app.route('/graphs/caldera')
@crossdomain(origin='*')
def graphs_caldera():
    return app.send_static_file('graphs_acs.html')


# @app.route('/data/caldera')
# @crossdomain(origin='*')
# def data_caldera():
#     return json.dumps(mayordomo.retrieve_all_data())



@app.route('/devices', methods=['GET'])
@crossdomain(origin='*')
def get_all_devices():
    logger.info("----->> Received GET /devices")
    list_of_devices = jsonify({'devices': mayordomo.get_all_devices()})
    logger.info("----->> responding 200 OK GET /devices")
    return list_of_devices


@app.route('/device/<device_name>', methods=['GET'])
@crossdomain(origin='*', methods=['GET'])
def get_device(device_name):
    return jsonify(mayordomo.get_device(device_name))


@app.route('/device', methods=['OPTIONS'])
@crossdomain(origin='*', methods=['PUT'])
def update_device():
    return ""


@app.route('/device', methods=['PUT'])
@crossdomain(origin='*')
def update_device_put():
    device = request.get_json()
    # request.remote_addr
    logger.info("client " + str(request.remote_addr) + " asked for PUT on device" + str(device['name']))
    print (device['name'])
    return jsonify(mayordomo.update_device(device))






if __name__ == "__main__":

    mayordomo.start()
    app.run(host="0.0.0.0", port=8080)
