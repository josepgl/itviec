from itviec import cache
from itviec.db import db
from itviec.helpers import to_json
from itviec.models import Employer, Job, Tag, Address, Review
from pprint import pprint


def compose_employer(employer_dict):
    compose_employer_reviews(employer_dict)
    jobcodes_to_jobs(employer_dict)
    str_to_address(employer_dict)
    str_to_tag(employer_dict)
    employer_dict["why"] = to_json(employer_dict["why"], indent=None)

    employer = Employer(**employer_dict)
    return employer


def compose_employer_reviews(employer):
    reviews = []
    for rev_d in employer["reviews"]:
        rev_d["employer_code"] = employer["code"]
        review = Review(**rev_d)
        reviews.append(review)
        db.session.add(review)
    employer["reviews"] = reviews


def jobcodes_to_jobs(employer):
    jobs = []
    for job_code in employer["jobs"]:
        print("    \\- Job: {}".format(job_code))
        job = db.session.query(Job).filter_by(code=job_code).first()
        if job:
            print("<*> FOUND Job in database by CODE '{}': {}".format(job_code, job))

        if job is None:
            try:
                job_d = cache.get_job(job_code)
            except FileNotFoundError:
                cache.fetch_job(job_code)
                job_d = cache.get_job(job_code)
            job_id = int(job_d["id"])
            job = db.session.query(Job).filter_by(id=job_id).first()
            if job:
                print("<*> FOUND Job in database by ID '{}': {}".format(job_id, job))

        if job is None:
            str_to_tag(job_d)
            str_to_address(job_d)

            job = Job(**job_d)
            db.session.add(job)

        jobs.append(job)
        db.session.commit()

    employer["jobs"] = jobs


def str_to_tag(item):
    tag_list = []
    for tag_name in item["tags"]:
        tag = db.session.query(Tag).filter_by(name=tag_name).first()
        if tag is None:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        tag_list.append(tag)
    item["tags"] = tag_list


def str_to_address(item):
    addr_list = []
    for full_addr in item["addresses"]:
        if full_addr == '':
            continue
        addr = db.session.query(Address).filter_by(full_address=full_addr).first()
        if addr is None:
            try:
                addr_list = full_addr.split(", ")[-2:]
                city = addr_list.pop()
                if len(addr_list):
                    district = addr_list.pop()
                    addr = Address(full_address=full_addr, city=city, district=district)
                else:
                    addr = Address(full_address=full_addr, city=city)
            except ValueError:
                print("Address: '{}'".format(full_addr))
                raise
            db.session.add(addr)
        addr_list.append(addr)
    item["addresses"] = addr_list


def jobtags_to_jobcodes(employer):
    job_codes = []
    for jt in employer["jobs"]:
        job_codes.append(jt["code"])
    employer["jobs"] = job_codes
