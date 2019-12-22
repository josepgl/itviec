import os

from flask import Flask
from flask_bootstrap import Bootstrap


# create and configure app
app = Flask(__name__, static_url_path='')
print("Starting app")

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

bootstrap = Bootstrap(app)

from app import routes


def create_app(test_config=None):
    # create and configure app
    # app = Flask(__name__, static_url_path='')
    app = Flask(__name__, instance_relative_config=True, static_url_path='')

    print("Starting app")

    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, 'ItViec.sqlite')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    from flask_bootstrap import Bootstrap
    bootstrap = Bootstrap(app)

    # register the database commands
    # from flaskr import db

    # db.init_app(app)

    # apply the blueprints to the app
    # from flaskr import auth, blog

    # app.register_blueprint(auth.bp)
    # app.register_blueprint(blog.bp)

    # from app import routes
    # from app import views,models

    return app
