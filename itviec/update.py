import itviec.cache
from itviec.composers import compose_job
from itviec.db import db
from itviec.models import Job, Employer, Address, Tag
from itviec.helpers import to_json

from pprint import pprint


def update_employer(employer_code):
    employer_dict = itviec.cache.get_employer(employer_code)

    query = db.session.query(Employer).filter_by(code=employer_code)
    employer = query.first()

    # in cache: for child, check in db
    update_employer_jobs(employer, employer_dict)
    update_employer_reviews(employer, employer_dict)
    update_employer_addresses(employer, employer_dict)
    update_employer_tags(employer, employer_dict)
    employer_dict["why"] = to_json(employer_dict["why"], indent=None)

    db.session.commit()

    del employer_dict["addresses"]
    del employer_dict["reviews"]
    del employer_dict["tags"]
    del employer_dict["jobs"]

    query = db.session.query(Employer).filter(Employer.code == employer_dict["code"])
    employer = query.first()

    query.update(employer_dict)
    db.session.commit()


def update_employer_jobs(employer, employer_dict):
    for job_tag in employer_dict["jobs"]:
        print("    \\- Job: {}".format(job_tag["code"]))

        job = Job.query.filter(Job.code == job_tag["code"]).first()
        if job is None:
            job = compose_job(job_tag)
            db.session.add(job)
            employer.jobs.append(job)
            continue

        # job already in database, update child
        update_job(job)

    # remove old jobs
    job_codes = [j["code"] for j in employer_dict["jobs"]]
    for job in employer.jobs:
        if job.code not in job_codes:
            print("Purging deprecated job {}".format(job.code))
            db.session.query(Job).filter_by(code=job.code).delete()


def update_job(job):
    job_d = itviec.cache.get_job(job.code)

    update_job_addresses(job, job_d)
    update_job_tags(job, job_d)

    del job_d["addresses"]
    del job_d["tags"]

    if "distance" in job_d:
        del job_d["distance"]

    db.session.query(Job).filter(Job.code == job_d["code"]).update(job_d)
    db.session.commit()


def update_employer_tags(employer, employer_dict):
    # add new tags
    for tag_name in employer_dict["tags"]:
        tag = db.session.query(Tag).filter_by(name=tag_name).first()
        if tag is None:
            tag = Tag(name=tag_name)
            db.session.add(tag)
            db.session.commit()

        # check if the tag is linked
        if tag not in employer.tags:
            employer.tags.append(tag)

    # delete old tags
    for addr in employer.addresses:
        if addr.full_address not in employer_dict["addresses"]:
            del addr


def update_employer_addresses(employer, employer_dict):
    # add new addresses
    for addr in employer_dict["addresses"]:
        address = db.session.query(Address).filter_by(full_address=addr).first()
        if address is None:
            print("Could not find Address: {}".format(addr))
            print("db.session.dirty")
            pprint(db.session.dirty)

            address = Address(full_address=addr)

            try:
                db.session.commit()
            except:
                print("FAILURE!! db.session.dirty")
                pprint(db.session.dirty)
                # raise

        # check if the address is linked
        if address not in employer.addresses:
            employer.addresses.append(address)

    # delete old addresses
    for address in employer.addresses:
        if address.full_address not in employer_dict["addresses"]:
            del address
            db.session.commit()


def update_job_tags(job, job_dict):
    # add new tags
    for tag_name in job_dict["tags"]:
        tag = db.session.query(Tag).filter_by(name=tag_name).first()
        if tag is None:
            tag = Tag(name=tag_name)
            db.session.add(tag)
            db.session.commit()

        # check if the tag is linked
        if tag not in job.tags:
            job.tags.append(tag)

    # delete old tags
    for addr in job.addresses:
        if addr.full_address not in job_dict["addresses"]:
            del addr


def update_job_addresses(job, job_dict):
    # add new addresses
    for addr in job_dict["addresses"]:
        address = db.session.query(Address).filter_by(full_address=addr).first()
        if address is None:
            address = Address(full_address=addr)
            db.session.add(address)
            db.session.commit()

        # check if the address is linked
        if address not in job.addresses:
            job.addresses.append(address)

    # delete old addresses
    for address in job.addresses:
        if address.full_address not in job_dict["addresses"]:
            del address


def update_employer_reviews(employer, employer_dict):
    pass
