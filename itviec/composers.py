from itviec import cache
from itviec.db import db
from itviec.helpers import to_json
from itviec.models import Employer, Job, Tag, Address, Review


def install_employer(employer_code):
    print("Installing employer '{}'...".format(employer_code))
    emp_d = cache.employer_cache_or_fetch(employer_code)

    for job_tag in emp_d["jobs"]:
        if not cache.is_job_cached(job_tag["code"]):
            cache.fetch_job_with_stamp(job_tag["code"], job_tag["last_post"])

    employer = compose_employer(employer_code)
    db.session.add(employer)
    db.session.commit()


def compose_employer(employer_code):
    employer_dict = cache.get_employer(employer_code)
    compose_employer_reviews(employer_dict)
    job_tags_to_jobs(employer_dict)
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


def job_tags_to_jobs(employer):
    jobs = []
    for job_tag in employer["jobs"]:
        print("    \\- Job: {}".format(job_tag["code"]))

        job = Job.query.filter(Job.code == job_tag["code"]).first()
        if job is None:
            job = compose_job(job_tag)
            db.session.add(job)

        jobs.append(job)
        db.session.commit()

    employer["jobs"] = jobs


def compose_job(job_tag):
    try:
        job_d = cache.get_job(job_tag["code"])
    except OSError:
        cache.fetch_job_with_stamp(job_tag["code"], job_tag["last_post"])
        job_d = cache.get_job(job_tag["code"])

    str_to_tag(job_d)
    str_to_address(job_d)

    if "distance" in job_d:
        del job_d["distance"]

    job = Job(**job_d)

    return job


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
