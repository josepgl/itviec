import os

# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
CONFIG_FILENAME = "config.py"
DATABASE_FILENAME = "ItViec.sqlite"

EMPLOYERS_JSON_URL = "https://itviec.com/api/v1/employers.json"
TEMPLATE_EMPLOYER_URL = "https://itviec.com/companies/{}"
TEMPLATE_EMPLOYER_REVIEW_URL = "https://itviec.com/companies/{}/review"

SQLALCHEMY_DATABASE_URI = "sqlite:////home/jose/projects/itviec/instance/sqlalchemy.sqlite"


class Config:
    DEBUG = True

    BASE_URL = "https://itviec.com"
    URL = "https://itviec.com/it-jobs"

    DATABASE = os.path.join(INSTANCE_DIR, DATABASE_FILENAME)
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE_DIR, DATABASE_FILENAME)
    # SQLALCHEMY_DATABASE_URI = "sqlite:////home/jose/projects/itviec/instance/sqlalchemy.sqlite")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True

    BOOTSTRAP_SERVE_LOCAL = True

    HTTP_HEADER_X_REQUESTED_WITH = "XMLHttpRequest"


class DevelopmentConfig(Config):
    DEBUG = True
    # DATABASE = ":memory:"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE_DIR, 'sqlalchemy.sqlite')


class TestingConfig(Config):
    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = dict(
    dev=DevelopmentConfig, test=TestingConfig, prod=ProductionConfig
)

req_http_headers = dict()


def set_app_config(config, test_config=None):
    global req_http_headers
    if test_config is None:
        # load the instance config, if it exists, when not testing
        config_name = os.getenv("FLASK_CONFIGURATION", "default")
        # app.config.from_object(config_by_name[config_name])
        config.from_object(config_by_name["dev"])
        try:
            # load default config
            config.from_pyfile("config.py")
            # load customized config
            config.from_pyfile("instance/config.py")
            # app.config.from_pyfile('config.py', silent=True)
        except:
            pass
    else:
        # load the test config if passed in
        config.from_mapping(test_config)

    req_http_headers = collect_http_headers(config)

    # Debugging
    # import json
    # conf_json = json.dumps(app.config, indent=4, sort_keys=True, default=str)
    # print(conf_json)

def collect_http_headers(conf):
    for k, v in conf.get_namespace('HTTP_HEADER_').items():
        req_http_headers[k.replace("_", "-").capitalize()] = v
    return req_http_headers


# req_http_headers = collect_http_headers(conf)
