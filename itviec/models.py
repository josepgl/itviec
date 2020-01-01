from sqlalchemy import Column, Table, Integer, String, ForeignKey, Text, DateTime, Float, Boolean, PickleType
from sqlalchemy.orm import relationship, backref

from itviec.db import Base
from itviec.helpers import fetch_url
from itviec.parsers import parse_employer, parse_employer_review, parse_job_summary
import config as Config


# class Employer(db.Model):
class Employer(Base):
    __tablename__ = 'employer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(128), nullable=False, unique=True)
    name = Column(String(128), nullable=False, unique=True)
    url = Column(String(128), nullable=False, unique=True)
    logo = Column(String(128), nullable=False, unique=True)
    location = Column(String(128), nullable=False, unique=True)
    industry = Column(String(128), nullable=False, unique=True)
    employees = Column(String(128), nullable=False, unique=True)
    country = Column(String(128), nullable=False, unique=True)
    working_days = Column(String(128), nullable=False, unique=True)
    overtime = Column(String(128))
    website = Column(String(128))

    description = Column(String(128), nullable=False, unique=True)
    tags = Column(String(128), ForeignKey('tag.name'), nullable=False)

    jobs = relationship('Job', backref='employer', lazy=True)
    # employer = relationship("Employer",
    #                         # secondary="employer_jobs",
    #                         backref=backref("jobs", lazy='dynamic')
    #                         )

    # Description fields
    panel = Column(String(), nullable=False, unique=True)
    header = Column(String(), nullable=False, unique=True)

    def __repr__(self):
        return '<Employer {}: {}>'.format(self.code, self.name)

    @classmethod
    def request_employer(self, code):
        employer_url = Config.TEMPLATE_EMPLOYER_URL.format(code)
        print(employer_url)
        employer_response = fetch_url(employer_url)
        employer_dict = parse_employer(employer_response.text, code)

        print("#### Review ##################")
        review_url = Config.TEMPLATE_EMPLOYER_REVIEW_URL.format(code)
        review_response = fetch_url(review_url)
        review_dict = parse_employer_review(review_response.text)

        print(review_dict)
        print("#### End of Review ###########")
        # employer_dict.last_update(review_dict)

        return Employer(**employer_dict)


# class Job(db.Model):
class Job(Base):
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True, nullable=False)
    last_update = Column(String(128), nullable=False)
    title = Column(String(128), nullable=False)
    url = Column(String(128), nullable=False)
    salary = Column(String(128), nullable=False)
    description = Column(String(128), nullable=False)

    address = relationship("Address",
                           secondary="job_addresses",
                           backref=backref("job", lazy='dynamic')
                           )

    tags = relationship("Tag",
                        secondary="job_tags",
                        backref=backref("job", lazy='dynamic')
                        )

    employer_code = Column(String(128), ForeignKey('employer.code'), nullable=False)
    # employer = relationship("Employer",
    #                         # secondary="employer_jobs",
    #                         backref=backref("jobs", lazy='dynamic')
    #                         )

    def __repr__(self):
        return '<Job {}: {}>'.format(self.id, self.title)

    @classmethod
    def from_tag(self, tag):
        # job_url = Config.TEMPLATE_EMPLOYER_URL.format(jid)
        # job_response = fetch_url(job_url)
        job_dict = parse_job_summary(tag)
        # print(job_dict)

        addresses = []
        for job_address in job_dict["address"]:
            # print("job_address: " + job_address)
            addresses.append(Address(name=job_address))
        job_dict["address"] = []

        tags = []
        for job_tag in job_dict["tags"]:
            # print("job_tag: " + job_tag)
            tags.append(Tag(name=job_tag))
        job_dict["tags"] = []

        # print(job_dict)
        job = Job(**job_dict)
        job.address = addresses
        job.tags = tags

        return job


class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), primary_key=True, unique=True, nullable=False)

    def __repr__(self):
        return '<Tag {}>'.format(self.name)


class Review(Base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True)

    def __repr__(self):
        return '<Review {}>'.format(self.name)


class Address(Base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), primary_key=True, unique=True, nullable=False)

    def __repr__(self):
        return '<Address {}>'.format(self.name)


job_addresses = Table('job_addresses',
                      Base.metadata,
                      Column('job_id', Integer, ForeignKey('job.id')),
                      Column('address_id', Integer, ForeignKey('address.id'))
                      )


job_tags = Table('job_tags',
                 Base.metadata,
                 Column('job_id', Integer, ForeignKey('job.id')),
                 Column('tag_id', Integer, ForeignKey('tag.id'))
                 )


employer_jobs = Table('employer_jobs',
                      Base.metadata,
                      Column('employer_id', Integer, ForeignKey('employer.id')),
                      Column('job_id', Integer, ForeignKey('job.id')),
                      )
