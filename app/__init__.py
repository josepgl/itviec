import os

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from config import set_app_config


bootstrap = Bootstrap()


def create_app(test_config=None):
    print("Starting app")
    app = Flask(__name__, instance_relative_config=True, static_url_path='')

    set_app_config(app.config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Basic routes
    @app.route("/hello")
    def hello():
        return "Hello, World!"

    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        return render_template("404.html"), 404

    @app.route("/about")
    def about():
        return render_template("about.html")

    # App modules
    bootstrap.init_app(app)

    from . import routes
    app.register_blueprint(routes.bp)
    app.add_url_rule('/', endpoint='index')

    if app.config['ENV'] != 'production':
        from . import dev
        app.register_blueprint(dev.bp)

    return app
