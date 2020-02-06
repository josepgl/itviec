import requests
import json
from datetime import datetime

from flask import current_app as app

import config

VIETNAMESE_CHARACTERS = "ăắằẳẵặâấầẩẫậĐđêếềểễệôốồổỗộơớờởỡợưứừửữự"


def first_line(string):
    return str(string).splitlines()[0]


def class_name(instance):
    return instance.__class__.__name__


def log(string, *args):
    print("ItViec " + string.format(*args))


def log_msg(string, *args):
    string = "{}:{}() " + string
    print(string.format(*args))


def msg(string):
    if config.DEBUG:
        print(string)


def fetch_url(url, headers=config.req_http_headers):
    # print('Fetching url {}'.format(url)) # DEBUG
    error_msg = "Error {0} fetching url: {1}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        exit(1)

    # Check response code
    if response.status_code != 200:
        raise StopIteration(error_msg.format(response.status_code, url))

    return response


def to_json(to_json, indent=2):
    return json.dumps(to_json, sort_keys=True, indent=indent, ensure_ascii=False)


def to_json_file(to_json, filename):
    with open(filename, 'wb') as json_file:
        s = json.dumps(to_json, sort_keys=True, indent=2, ensure_ascii=False)
        json_file.write(s.encode('utf8'))


def str_to_datetime(date_string):
    return datetime.strptime(date_string, app.config["DATETIME_FORMAT"])


def datetime_to_str(datetime_type):
    return datetime_type.strftime(app.config["DATETIME_FORMAT"])


def time_since(datetime_type):
    now = datetime.now()
    return now - datetime_type
