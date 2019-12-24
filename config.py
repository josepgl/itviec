import os

# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
CONFIG_FILENAME = "config.py"


class Config:
    DEBUG = True

    BASE_URL = "https://itviec.com"
    URL = "https://itviec.com/it-jobs"

    BOOTSTRAP_SERVE_LOCAL = (True,)
    # DATABASE = os.path.join(BASE_DIR, 'instance', 'ItViec.sqlite')
    DATABASE = os.path.join(BASE_DIR, "ItViec.sqlite")

    HTTP_HEADER_X_REQUESTED_WITH = "XMLHttpRequest"

    DATABASE_URI = "sqlite://" + os.path.join(BASE_DIR, "ItViec.sqlite")


class DevelopmentConfig(Config):
    DEBUG = True


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
            config.from_pyfile("config.py")
            config.from_pyfile("instance/config.py")
        except:
            pass

        # app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        config.from_mapping(test_config)

    # Debugging
    # import json
    # conf_json = json.dumps(app.config, indent=4, sort_keys=True, default=str)
    # print(conf_json)
