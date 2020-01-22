import requests
from requests.exceptions import HTTPError, ConnectionError

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
    except ConnectionError as e:
        print("Can't connect to server: {}".format(e))
    except HTTPError as e:
        print(e)

    # Check response code
    if response.status_code != 200:
        raise StopIteration(error_msg.format(response.status_code, url))

    return response
