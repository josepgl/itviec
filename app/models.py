from . import db
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, PickleType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# class Employer(db.Model):
class Employer(Base):
    __tablename__ = 'employer'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(128), nullable=False, unique=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    url = db.Column(db.String(128), nullable=False, unique=True)
    logo = db.Column(db.String(128), nullable=False, unique=True)
    location = db.Column(db.String(128), nullable=False, unique=True)
    industry = db.Column(db.String(128), nullable=False, unique=True)
    employees = db.Column(db.String(128), nullable=False, unique=True)
    country = db.Column(db.String(128), nullable=False, unique=True)
    working_days = db.Column(db.String(128), nullable=False, unique=True)
    overtime = db.Column(db.String(128))
    website = db.Column(db.String(128))

    description = db.Column(db.String(128), nullable=False, unique=True)
    tags = db.Column(db.String(128), db.ForeignKey('tag.name'), nullable=False)

    jobs = db.relationship('Job', backref='employer', lazy=True)

    def __repr__(self):
        return '<Employer {}>'.format(self.code)


# class Job(db.Model):
class Job(Base):
    __tablename__ = 'job'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    last_update = db.Column(db.String(128), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(128), nullable=False)
    salary = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(128), nullable=False)
    address_1 = db.Column(db.String(128), nullable=False)
    address_2 = db.Column(db.String(128), nullable=False)

    employer_code = db.Column(db.String(128), db.ForeignKey('employer.code'), nullable=False)
    tags = db.Column(db.String(128), db.ForeignKey('tag.name'), nullable=False)

    def __repr__(self):
        return '<Job {}>'.format(self.id)


# class Tag(db.Model):
class Tag(Base):
    __tablename__ = 'tag'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), unique=True)

    def __repr__(self):
        return '<Tag {}>'.format(self.name)
