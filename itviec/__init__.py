from flask import Flask, render_template
from flask_bootstrap import Bootstrap

import config
from itviec.db import db

bootstrap = Bootstrap()


def page_not_found(e):
    return render_template("404.html"), 404


def create_app(profile=None, test_config=None):
    print("Starting app instance")

    app = Flask(__name__, instance_relative_config=True)

    # Load configuration and modules
    config.init_app(app, profile=profile, test_config=test_config)
    bootstrap.init_app(app)
    db.init_app(app)

    app.register_error_handler(404, page_not_found)

    # Blueprints
    import itviec.views
    app.register_blueprint(itviec.views.bp)
    app.add_url_rule('/', endpoint='index')

    import itviec.cmd_views
    app.register_blueprint(itviec.cmd_views.cmd_bp)
    app.register_blueprint(itviec.cmd_views.job_bp)

    if app.config['ENV'] != 'production':
        from . import dev
        app.register_blueprint(dev.bp)

    return app
