import requests

import config


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


def fetch_url(url):
    # Fetch page
    # print('Fetching url {}'.format(url)) # DEBUG

    response = requests.get(url, headers=config.req_http_headers)

    # Check response code
    if response.status_code != 200:
        raise StopIteration(
            "Error {0} fetching url: {1}".format(response.status_code, url)
        )

    return response
