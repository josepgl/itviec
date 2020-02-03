from flask import Blueprint, jsonify, current_app
from flask.json import JSONEncoder

from datetime import datetime, date, timedelta


class CustomJSONEncoder(JSONEncoder):
    '''JSONEncoder with date types to string conversion.

    This class allows encoding flask configuration to JSON.
    '''

    def default(self, o):  # pylint: disable=E0202
        try:
            if isinstance(o, datetime):
                return o.isoformat()
            elif isinstance(o, date):
                return o.isoformat()
            elif isinstance(o, timedelta):
                return str(o)
            iterable = iter(o)
        except TypeError as e:
            print("TypeError found: {}".format(e))
            raise
        else:
            return list(iterable)
        return JSONEncoder.default(self, o)


bp = Blueprint('dev', __name__, url_prefix='/')


@bp.route("/config")
def config():
    app = current_app
    app.json_encoder = CustomJSONEncoder

    return jsonify(app.config)
