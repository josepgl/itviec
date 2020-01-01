import flask
import requests

import config as Config


def first_line(s):
    return str(s).splitlines()[0]


def class_name(i):
    return i.__class__.__name__


def log(s, *args):
    print("ItViec " + s.format(*args))


def log_msg(s, *args):
    s = "{}:{}() " + s
    print(s.format(*args))


def msg(s):
    if conf['DEBUG']:
        print(s)


def fetch_url(url):
    # Fetch page
    # print('Fetching url {}'.format(url)) # DEBUG

    response = requests.get(url, headers=Config.req_http_headers)

    # Check response code
    if response.status_code != 200:
        raise StopIteration(
            "Error {0} fetching url: {1}".format(response.status_code, url)
        )

    return response


def get_config():
    config = flask.Config(Config.BASE_DIR)
    Config.set_app_config(config)
    # print(config)

    return config


conf = get_config()


