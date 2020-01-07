import os


# def print_json(to_json):
#     import json
#     json = json.dumps(to_json, indent=4, sort_keys=True, default=str)
#     print(json)


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

    CONFIG_FILENAME = "config.py"

    # ItViec urls
    BASE_URL = "https://itviec.com"
    URL = "https://itviec.com/it-jobs"
    EMPLOYERS_JSON_URL = "https://itviec.com/api/v1/employers.json"
    TEMPLATE_EMPLOYER_URL = "https://itviec.com/companies/{}"
    TEMPLATE_EMPLOYER_REVIEW_URL = "https://itviec.com/companies/{}/review"

    # Database / SQLAlchemy
    # DATABASE_FILENAME = "ItViec.sqlite"
    DATABASE_FILENAME = "sqlalchemy.sqlite"
    DATABASE = os.path.join(INSTANCE_DIR, DATABASE_FILENAME)
    # SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///' + os.path.join(INSTANCE_DIR, DATABASE_FILENAME)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True

    # Bootstrap
    BOOTSTRAP_SERVE_LOCAL = True

    # ItViec json header
    HTTP_HEADER_X_REQUESTED_WITH = "XMLHttpRequest"
    # HTTP_HEADER_COOKIE = "_ITViec_session=..."


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(Config.INSTANCE_DIR, 'sqlalchemy.sqlite')
    # SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class TestingConfig(Config):
    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = dict(
    development=DevelopmentConfig,
    test=TestingConfig,
    production=ProductionConfig
)

req_http_headers = dict()


# Uses flask.Config (app.config)
def load_config(config, test_config=None):
    global req_http_headers

    # load the instance config, if it exists, when not testing
    config_name = os.getenv("FLASK_ENV", "production")
    print("Loading {} configuration profile.".format(config_name))

    # load default config
    config.from_object(config_by_name[config_name]())

    if test_config is None:
        try:
            # load customized config
            print("Loading custom configuration.")
            config.from_pyfile("config.py")
            # app.config.from_pyfile('config.py', silent=True)
        except FileNotFoundError:
            print("Custom config.py file missing in instance folder.")
            pass
    else:
        # load the test config if passed in
        config.from_mapping(test_config)

    req_http_headers = collect_http_headers(config)

    # Debugging
    # print_json(config)


def collect_http_headers(conf):
    for k, v in conf.get_namespace('HTTP_HEADER_').items():
        req_http_headers[k.replace("_", "-").capitalize()] = v
    return req_http_headers


# req_http_headers = collect_http_headers(conf)
