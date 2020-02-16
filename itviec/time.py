from datetime import datetime

from flask import current_app as app


def str_to_datetime(date_string):
    return datetime.strptime(date_string, app.config["DATETIME_FORMAT"])


def datetime_to_str(datetime_type):
    return datetime_type.strftime(app.config["DATETIME_FORMAT"])


def time_since(datetime_type):
    now = datetime.now()
    return now - datetime_type


def get_time_distance(time_distance):
    time = {}
    (count, unit, _) = time_distance.split(" ")
    if unit.startswith("minute"):
        time["minutes"] = int(count)
    elif unit.startswith("hour"):
        time["hours"] = int(count)
    elif unit.startswith("day"):
        time["days"] = int(count)
    return time
