from sqlalchemy import Column, Table, ForeignKey, UniqueConstraint
from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.orm import relationship, backref

import config
from itviec.db import db
from itviec.helpers import fetch_url
from itviec.parsers import JobSummaryParser, parse_employer, parse_employer_review
from pprint import pprint

job_address = Table('job_address', db.base.metadata,
                    Column('job_id', Integer, ForeignKey('job.id')),
                    Column('address_id', Integer, ForeignKey('address.id'))
                    )


class Employer(db.base):
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

    # Description fields
    description = Column(Text(), nullable=False, unique=True)  # Large text
    panel = Column(Text(), nullable=False, unique=True)
    # header = Column(String(), nullable=False, unique=True)

    # jobs = relationship('Job', lazy=True)
    # tags = Column(String(128), ForeignKey('tag.name'), nullable=False)
    # reviews = relationship('Review', backref='employer', lazy=True)

    def __repr__(self):
        return '<Employer {}: {}>'.format(self.code, self.name)

    def url(self):
        return config.Config.TEMPLATE_EMPLOYER_URL.format(self.code)

    @classmethod
    def request_employer(self, code):
        employer_url = config.Config.TEMPLATE_EMPLOYER_URL.format(code)
        # print(employer_url)
        employer_response = fetch_url(employer_url)
        employer_dict = parse_employer(employer_response.text, code)
        employer_dict['panel'] = "<div>"
        # print(employer_dict)

        # print("#### Review ##################")
        review_url = config.Config.TEMPLATE_EMPLOYER_REVIEW_URL.format(code)
        review_response = fetch_url(review_url)
        review_dict = parse_employer_review(review_response.text)
        pprint(review_dict['reviews'][0])
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


class Job(db.base):
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True, nullable=False)
    last_update = Column(String(128), nullable=False)
    title = Column(String(128), nullable=False)
    url = Column(String(128), nullable=False)
    salary = Column(String(128), nullable=False)
    description = Column(String(128), nullable=False)

    address = relationship("Address",
                           secondary="job_address",
                           backref="job",
                           # backref=backref("jobs", lazy='dynamic'),
                           )

    # tags = relationship("Tag",
    #                     secondary="job_tag",
    #                     backref="job",
    #                     backref=backref("jobs", lazy='dynamic'),
    #                     back_populates="jobs",
    #                     )

    # employer_code = Column(String(128), nullable=False)
    employer_code = Column(String(128), ForeignKey('employer.code'), nullable=False)
    employer = relationship("Employer", backref=backref("jobs", order_by=id))
    # employer = relationship("Employer",
    #                         secondary="employer_job",
    #                         backref="jobs",
    #                         )

    def __repr__(self):
        return '<Job {}: {}>'.format(self.id, self.title)

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def from_tag(self, tag):
        job_p = JobSummaryParser(tag)
        job_dict = job_p.get_dict()
        return self.from_dict(job_dict)

    @classmethod
    def from_dict(self, job_dict):
        # has_job = db.session.query(Job).filter_by(id=job_dict["id"]).first()
        # if has_job:
        #     return has_job

        # Child objects
        addresses = []
        for job_address in job_dict["address"]:
            # print("job_address: " + job_address)
            has_addr = db.session.query(Address).filter_by(name=job_address).first()
            if has_addr is not None:
                addresses.append(has_addr)
            else:
                addresses.append(Address(name=job_address))
                db.session.add(addresses[-1])
            # pprint(addresses[-1].__dict__)

        tags = []
        for job_tag in job_dict["tags"]:
            # print("job_tag: " + job_tag)
            has_tag = db.session.query(Tag).filter_by(name=job_tag).first()
            if has_tag is not None:
                tags.append(has_tag)
            else:
                tags.append(Tag(name=job_tag))
                db.session.add(tags[-1])
            # pprint(tags[-1].__dict__)

        db.session.commit()
        job_dict["address"] = []
        job_dict["tags"] = []
        job = Job(**job_dict)
        job.address.extend(addresses)
        for tag in tags:
            job.link_tag(tag)

        return job

    def link_tag(self, tag):
        has_link = db.session.query(JobTag).filter_by(job_id=self.id, tag_id=tag.id).first()

        if has_link:
            print("{} already exists".format(has_link))
            return None

        job_tag_link = JobTag(job_id=self.id, tag_id=tag.id)
        print("Created: {}".format(job_tag_link))
        db.session.add(job_tag_link)

        return job_tag_link


class JobTag(db.base):
    __tablename__ = 'job_tag'

    job_tag_id = Column(Integer(), primary_key=True)
    job_id = Column(Integer(), ForeignKey('job.id'))
    tag_id = Column(Integer(), ForeignKey('tag.id'))

    job = relationship("Job", backref=backref("tags"))
    tag = relationship("Tag", uselist=False)

    __table_args__ = (UniqueConstraint('job_id', 'tag_id'),)

    def __repr__(self):
        return '<JobTag job={} tag={}>'.format(self.job_id, self.tag_id)


class Tag(db.base):
    __tablename__ = 'tag'

    id = Column(Integer(), primary_key=True)
    name = Column(String(128), unique=True, nullable=False)

    # jobs = relationship("Job",
    #                     secondary="job_tag",
    #                     # backref="job",
    #                     # backref=backref("jobs", lazy='dynamic'),
    #                     back_populates="tags",
    #                     )
    # jobs = relationship("JobTag")
    # jobs = relationship("JobTag", secondary="job_tag")
    # employers = relationship("Employer", secondary="employer_tag")

    def __repr__(self):
        return '<Tag {}>'.format(self.name)


class Address(db.base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(128), unique=True, nullable=False)

    def __repr__(self):
        return '<Address {}>'.format(self.name)


class Review(db.base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    title = Column(String(128), unique=True)
    date = Column(String(128), unique=True)
    employer_code = Column(String(128), ForeignKey('employer.code'), nullable=False)
    last_update = Column(String(128))
    liked = Column(Text())
    hated = Column(Text())
    recommend = Column(Boolean(), nullable=False)
    stars_total = Column(Integer(), nullable=False)
    stars_salary = Column(Integer(), nullable=False)
    stars_training = Column(Integer(), nullable=False)
    stars_management = Column(Integer(), nullable=False)
    stars_culture = Column(Integer(), nullable=False)
    stars_workspace = Column(Integer(), nullable=False)

    def __repr__(self):
        return '<Review {}>'.format(self.title)
