import os

from flask import Flask, render_template


def create_app(test_config=None):
    print("Starting app")
    app = Flask(__name__, instance_relative_config=True, static_url_path='')
    app.config.from_mapping(
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

    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        return render_template("404.html"), 404

    @app.route("/about")
    def about():
        return render_template("about.html")

    from . import db
    db.init_app(app)

    from . import routes
    app.register_blueprint(routes.bp)
    app.add_url_rule('/', endpoint='index')

    from flask_bootstrap import Bootstrap
    bootstrap = Bootstrap(app)

    return app
