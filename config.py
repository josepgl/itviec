import os

# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
CONFIG_FILENAME = "config.py"
DATABASE_FILENAME = "ItViec.sqlite"

EMPLOYERS_JSON_URL = "https://itviec.com/api/v1/employers.json"
TEMPLATE_EMPLOYER_URL = "https://itviec.com/companies/{}"
TEMPLATE_EMPLOYER_REVIEW_URL = "https://itviec.com/companies/{}/review"


class Config:
    DEBUG = True

    BASE_URL = "https://itviec.com"
    URL = "https://itviec.com/it-jobs"

    DATABASE = os.path.join(INSTANCE_DIR, DATABASE_FILENAME)
    # DATABASE_URI = "sqlite://" + os.path.join(INSTANCE_DIR, DATABASE_FILENAME)

    BOOTSTRAP_SERVE_LOCAL = True

    HTTP_HEADER_X_REQUESTED_WITH = "XMLHttpRequest"


class DevelopmentConfig(Config):
    DEBUG = True
    # DATABASE = ":memory:"


class TestingConfig(Config):
    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = dict(
    dev=DevelopmentConfig, test=TestingConfig, prod=ProductionConfig
)


def set_app_config(config, test_config=None):
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

    # Debugging
    # import json
    # conf_json = json.dumps(app.config, indent=4, sort_keys=True, default=str)
    # print(conf_json)
