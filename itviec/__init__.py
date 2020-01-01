import os

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from config import set_app_config
from itviec.db import db_session

bootstrap = Bootstrap()


def page_not_found(e):
    return render_template("404.html"), 404


def create_app(test_config=None):

    print("Starting app instance...")

    app = Flask(__name__, instance_relative_config=True, static_url_path='')

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # App config, handlers and setup
    set_app_config(app.config)
    bootstrap.init_app(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    app.register_error_handler(404, page_not_found)

    # Blueprints
    import itviec.views
    app.register_blueprint(itviec.views.bp)
    app.add_url_rule('/', endpoint='index')

    if app.config['ENV'] != 'production':
        from . import dev
        app.register_blueprint(dev.bp)

    return app
