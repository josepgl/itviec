from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy import Integer, Float, String, Text, Boolean
from sqlalchemy.orm import relationship, backref

import config
from itviec.db import db

from pprint import pprint

job_address = Table('job_address', db.base.metadata,
                    Column('job_id', Integer, ForeignKey('job.id')),
                    Column('address_id', Integer, ForeignKey('address.id'))
                    )

employer_address = Table('employer_address', db.base.metadata,
                         Column('employer_id', Integer, ForeignKey('employer.id')),
                         Column('address_id', Integer, ForeignKey('address.id'))
                         )

job_tag = Table('job_tag', db.base.metadata,
                Column('job_id', Integer, ForeignKey('job.id')),
                Column('tag_id', Integer, ForeignKey('tag.id'))
                )

employer_tag = Table('employer_tag', db.base.metadata,
                     Column('employer_id', Integer, ForeignKey('employer.id')),
                     Column('tag_id', Integer, ForeignKey('tag.id'))
                     )


class Employer(db.base):
    __tablename__ = 'employer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(128), nullable=False, unique=True)
    name = Column(String(128), nullable=False, unique=True)
    logo = Column(String(128), nullable=False)
    location = Column(String(128), nullable=False)
    industry = Column(String(128), nullable=False)
    employees = Column(String(128), nullable=False)
    country = Column(String(128), nullable=False)
    last_update = Column(String(128), nullable=False)
    working_days = Column(String(128))
    overtime = Column(String(128))
    website = Column(String(128))

    review_count = Column(Integer)
    review_ratings = Column(Float)
    review_recommend = Column(Integer)

    # Description fields
    overview = Column(Text(), nullable=False)
    why = Column(Text())
    our_people = Column(Text())

    addresses = relationship("Address",
                             secondary="employer_address",
                             backref="employers",
                             )
    tags = relationship("Tag",
                        secondary="employer_tag",
                        backref=backref("employers", lazy='dynamic'),
                        )
    reviews = relationship('Review', backref='employer', lazy=True)

    def __repr__(self):
        return '<Employer {}: {}>'.format(self.code, self.name)

    def url(self):
        return config.Config.TEMPLATE_EMPLOYER_URL.format(self.code)


class Job(db.base):
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True, nullable=False)
    code = Column(String(256), nullable=False)
    last_update = Column(String(128), nullable=False)
    title = Column(String(128), nullable=False)
    salary = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    skills_experience = Column(Text, nullable=False)
    reasons = Column(Text, nullable=False)
    why = Column(Text)

    addresses = relationship("Address",
                             secondary="job_address",
                             backref="jobs",
                             )

    tags = relationship("Tag",
                        secondary="job_tag",
                        backref=backref("jobs", lazy='dynamic'),
                        )

    employer_code = Column(String(128), ForeignKey('employer.code'), nullable=False)
    employer = relationship("Employer", backref=backref("jobs", order_by=id))

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


class Tag(db.base):
    __tablename__ = 'tag'

    id = Column(Integer(), primary_key=True)
    name = Column(String(128), unique=True, nullable=False)

    def __repr__(self):
        return '<Tag {}>'.format(self.name)


class Address(db.base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_address = Column(String(128), unique=True, nullable=False)
    country = Column(String(32))
    city = Column(String(32))
    district = Column(String(32))

    def __repr__(self):
        return "<Address: '{}'>".format(self.full_address)


class Review(db.base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128))
    date = Column(String(128))
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
