from flask import Blueprint, jsonify, current_app
from flask.json import JSONEncoder

from datetime import datetime, date, timedelta


class CustomJSONEncoder(JSONEncoder):
    '''JSONEncoder with date types to string conversion.

    This class allows encoding flask configuration to JSON.
    '''

    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, date):
                return obj.isoformat()
            elif isinstance(obj, timedelta):
                return str(obj)
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


bp = Blueprint('dev', __name__, url_prefix='/')


@bp.route("/config")
def config():
    app = current_app
    app.json_encoder = CustomJSONEncoder

    return jsonify(app.config)
