from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class Database():

    def __init__(self, uri=None):
        self.base = declarative_base()
        self.session = None

        if uri is not None:
            self.set_engine(uri)

    def set_uri(self, uri):
        self.engine = create_engine(uri)
        # print("Engine: " + str(self.engine))
        print(self.engine)
        session = self.get_session()
        self.base.query = session.query_property()

    def get_session(self):
        if self.session is None:
            self.session = scoped_session(
                sessionmaker(autocommit=False,
                             autoflush=False,
                             bind=self.engine))

        return self.session

    def init_app(self, app):
        uri = app.config["SQLALCHEMY_DATABASE_URI"]
        self.set_uri(uri)

        @app.teardown_appcontext
        def close_session(exception=None):
            db.session.remove()

        if uri is 'sqlite://':
            self.init_db()

    def init_db(self):
        print("Init database")
        # import all modules here that might define models so that
        # they will be registered properly on the metadata.  Otherwise
        # you will have to import them first before calling init_db()
        import itviec.models  # noqa
        self.base.metadata.create_all(bind=self.engine)


db = Database()
