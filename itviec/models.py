from sqlalchemy import Column, Table, ForeignKey, UniqueConstraint
from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.orm import relationship, backref

import config
from itviec.db import db
from itviec.parsers import JobTagParser, EmployerParser

from pprint import pprint

job_address = Table('job_address', db.base.metadata,
                    Column('job_id', Integer, ForeignKey('job.id')),
                    Column('address_id', Integer, ForeignKey('address.id'))
                    )

employer_address = Table('employer_address', db.base.metadata,
                         Column('employer_id', Integer, ForeignKey('employer.id')),
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
    overview = Column(Text(), nullable=False, unique=True)  # Large text
    why = Column(Text(), nullable=False, unique=True)  # Large text

    addresses = relationship("Address",
                             secondary="employer_address",
                             backref="employers",
                             # backref=backref("jobs", lazy='dynamic'),
                             )
    # jobs = relationship('Job', lazy=True)
    # tags = Column(String(128), ForeignKey('tag.name'), nullable=False)
    # reviews = relationship('Review', backref='employer', lazy=True)

    def __repr__(self):
        return '<Employer {}: {}>'.format(self.code, self.name)

    def url(self):
        return config.Config.TEMPLATE_EMPLOYER_URL.format(self.code)


class Job(db.base):
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True, nullable=False)
    code = Column(String(128), nullable=False)
    last_update = Column(String(128), nullable=False)
    title = Column(String(128), nullable=False)
    salary = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    skills_experience = Column(Text, nullable=False)
    reasons = Column(Text, nullable=False)
    why = Column(Text, nullable=False)

    # address = Column(String(128), nullable=False)
    full_address = Column(String(128), ForeignKey('address.name'))
    address = relationship("Address",
                           # secondary="job_address",
                           backref="jobs",
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
    def from_dict(self, job_dict):

        pprint(job_dict)

        # Child objects
        has_addr = db.session.query(Address).filter_by(name=job_dict["full_address"]).first()
        if has_addr is not None:
            job_dict["full_address"] = has_addr
        else:
            job_dict["full_address"] = Address(name=job_dict["full_address"])
            db.session.add(job_dict["full_address"])

        tags = []
        for job_tag in job_dict["tags"]:
            has_tag = db.session.query(Tag).filter_by(name=job_tag).first()
            if has_tag is not None:
                tags.append(has_tag)
            else:
                tags.append(Tag(name=job_tag))
                db.session.add(tags[-1])

        # db.session.commit()
        job_dict["tags"] = []
        job = Job(**job_dict)
        job.link_tags(tags)

        return job

    def link_tag(self, tag):
        has_link = db.session.query(JobTag).filter_by(job_id=self.id, tag_id=tag.id).first()

        if has_link:
            print("{} already exists".format(has_link))
            return None

        job_tag_link = JobTag(job_id=self.id, tag_id=tag.id)
        print("Created: {}".format(job_tag_link))
        db.session.add(job_tag_link)
        # db.session.commit()

        return job_tag_link

    def link_tags(self, tags):
        for tag in tags:
            self.link_tag(tag)


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

    def __repr__(self):
        return '<Tag {}>'.format(self.name)


class Address(db.base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)

    def __repr__(self):
        return '<Address {}>'.format(self.name)


class Review(db.base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True, autoincrement=True)
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
