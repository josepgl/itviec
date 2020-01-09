import os

'''
- Environment config
  - Instance config or
  - Test config
'''

basedir = os.path.abspath(os.path.dirname(__file__))
DEBUG = True

req_http_headers = dict()


# Function for debugging, avoiding circular dependency with helpers module
def print_json(to_json_string):
    import json
    json = json.dumps(to_json_string, indent=4, sort_keys=True, default=str)
    print(json)


class Config:
    INSTANCE_DIR = os.path.join(basedir, "instance")

    CONFIG_FILENAME = "config.py"

    # ItViec urls
    BASE_URL = "https://itviec.com"
    URL = "https://itviec.com/it-jobs"
    EMPLOYERS_JSON_URL = "https://itviec.com/api/v1/employers.json"
    TEMPLATE_EMPLOYER_URL = "https://itviec.com/companies/{}"
    TEMPLATE_EMPLOYER_REVIEW_URL = "https://itviec.com/companies/{}/review"

    # Database / SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BOOTSTRAP_SERVE_LOCAL = True

    # ItViec request header for json
    HTTP_HEADER_X_REQUESTED_WITH = "XMLHttpRequest"
    # HTTP_HEADER_COOKIE = "_ITViec_session=..."


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, "instance", "sqlalchemy.sqlite")
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or "sqlite://"
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, "instance", "sqlalchemy.sqlite")


config = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,

    default=DevelopmentConfig,
)


# Uses flask.Config (app.config)
def init_app(app, profile=None, test_config=None):
    global req_http_headers

    # load the instance config, if it exists, when not testing
    config_name = profile or os.getenv("FLASK_ENV", "production")
    print("Loading '{}' configuration profile".format(config_name))

    # load default config
    app.config.from_object(config[config_name]())

    if test_config:
        print("Loading test configuration.")
        app.config.from_mapping(test_config)
    else:
        try:
            print("Loading instance configuration.")
            app.config.from_pyfile("config.py")
        except FileNotFoundError as error:
            print("Custom config.py file missing in instance folder: {}".format(error))

    req_http_headers = collect_http_headers(app.config)

    if app.config["DEBUG"] is True:
        print_json(app.config)


def collect_http_headers(conf):
    for k, v in conf.get_namespace('HTTP_HEADER_').items():
        req_http_headers[k.replace("_", "-").capitalize()] = v
    return req_http_headers
