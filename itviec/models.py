from sqlalchemy import Column, Table, Integer, String, ForeignKey, Text, DateTime, Float, Boolean, PickleType
from sqlalchemy.orm import relationship, backref

from itviec.db import Base, db_session
from itviec.helpers import fetch_url
from itviec.parsers import parse_employer, parse_employer_review, parse_job_summary
import config as Config
# from pprint import pprint


# class Employer(db.Model):
class Employer(Base):
    __tablename__ = 'employer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(128), nullable=False, unique=True)
    name = Column(String(128), nullable=False, unique=True)
    logo = Column(String(128), nullable=False, unique=True)
    location = Column(String(128), nullable=False, unique=True)
    industry = Column(String(128), nullable=False, unique=True)
    employees = Column(String(128), nullable=False, unique=True)
    country = Column(String(128), nullable=False, unique=True)
    working_days = Column(String(128), unique=True)
    overtime = Column(String(128))
    website = Column(String(128))

    description = Column(Text(), nullable=False, unique=True)  # Large text
    tags = Column(String(128), ForeignKey('tag.name'), nullable=False)

    # Description fields
    panel = Column(Text(), nullable=False, unique=True)
    # header = Column(String(), nullable=False, unique=True)

    # job_ids = Column(Integer, ForeignKey('job.id'), nullable=False)
    # job_ids = relationship('Job.id', backref='employer', lazy=True)
    # job_ids = relationship('Job', lazy=True)
    # job_ids = relationship("Employer",
    # job_ids = relationship("employer_jobids",
    #                        secondary="employer_jobids",
    #                        backref=backref("employer", lazy='dynamic')
    #                        )
    # jobs = relationship('Job', lazy=True)

    reviews = relationship('Review', backref='employer', lazy=True)

    def __repr__(self):
        return '<Employer {}: {}>'.format(self.code, self.name)

    def url(self):
        return Config.TEMPLATE_EMPLOYER_URL.format(self.code)

    @classmethod
    def request_employer(self, code):
        employer_url = Config.TEMPLATE_EMPLOYER_URL.format(code)
        # print(employer_url)
        employer_response = fetch_url(employer_url)
        employer_dict = parse_employer(employer_response.text, code)
        employer_dict['panel'] = "<div>"
        print(employer_dict)

        # print("#### Review ##################")
        review_url = Config.TEMPLATE_EMPLOYER_REVIEW_URL.format(code)
        review_response = fetch_url(review_url)
        review_dict = parse_employer_review(review_response.text)
        # print(review_dict)

        reviews = []
        for rev in review_dict["reviews"]:
            reviews.append(Review(**rev))
        # print("reviews: " + str(reviews))
        # print("#### End of Review ###########")
        # employer_dict.last_update(review_dict)

        # jobs = []
        # for job in employer_dict["jobs"]:
        #     jobs.append(Job(id=job))

        # employer_dict['jobs'] = []
        # employer_dict['reviews'] = []
        employer_dict['panel'] = "<div>"
        # print("employer_dict:")
        # pprint(employer_dict)
        employer = Employer(**employer_dict)
        # employer.jobs = jobs
        # employer.reviews = reviews

        return employer


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

    employer_code = Column(String(128), nullable=False)
    # employer = relationship('Employer', backref='jobs', load_on_pending=True)
    # employer = relationship('Employer', backref='jobs')
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

        has_job = db_session.query(Job).filter_by(id=job_dict["id"]).first()
        if has_job:
            return has_job

        # Child objects
        addresses = []
        for job_address in job_dict["address"]:
            # print("job_address: " + job_address)

            has_addr = db_session.query(Address).filter_by(name=job_address).first()
            if has_addr is not None:
                addresses.append(has_addr)
            else:
                addresses.append(Address(name=job_address))
        job_dict["address"] = addresses

        tags = []
        for job_tag in job_dict["tags"]:
            # print("job_tag: " + job_tag)
            has_tag = db_session.query(Tag).filter_by(name=job_tag).first()
            if has_tag is not None:
                tags.append(has_tag)
            else:
                tags.append(Tag(name=job_tag))
        job_dict["tags"] = tags

        # print(job_dict)
        job = Job(**job_dict)

        db_session.add(job)
        db_session.commit()

        return job


class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)

    def __repr__(self):
        return '<Tag {}>'.format(self.name)


class Review(Base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), unique=True)
    date = Column(String(128), unique=True)
    employer_code = Column(String(128), ForeignKey('employer.code'), nullable=False)

    def __repr__(self):
        return '<Review {}>'.format(self.title)


class Address(Base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)

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


# employer_jobids = Table('employer_jobids',
#                         Base.metadata,
#                         Column('employer_id', Integer, ForeignKey('employer.id')),
#                         Column('job_id', Integer, ForeignKey('job.id')),
#                         )
