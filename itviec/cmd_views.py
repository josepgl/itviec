import os
import time
import json
import glob

import click
from flask import Blueprint
from flask import current_app as app

from itviec import source
from itviec import cache
from itviec.helpers import to_json
from itviec.feeds import JobsFeed
from itviec.parsers import JobTagParser, JobParser, EmployerParser
from itviec.db import db
from itviec.models import Job, Employer, Tag, Address, Review

# for debugging
from pprint import pprint

cmd_bp = Blueprint('itviec_cmd', __name__, cli_group=None)
db_bp = Blueprint('itviec_cmd_db', __name__, cli_group="db")
job_bp = Blueprint('itviec_cmd_job', __name__, cli_group="job")
emp_bp = Blueprint('itviec_cmd_employer', __name__, cli_group="employer")


@db_bp.cli.command('stats')
def stats():
    jobs = Job.query.count()
    addresses = Address.query.count()
    employers = Employer.query.count()
    tags = Tag.query.count()

    print("Jobs: {}".format(jobs))
    print("Tags: {}".format(tags))
    print("Addresses: {}".format(addresses))
    print("Employers: {}".format(employers))


# Commands ###########################################
@cmd_bp.cli.command('init')
def init():
    directories = (
        app.instance_path,
        app.config["CACHE_DIR"],
        app.config["JOBS_CACHE_DIR"],
        app.config["EMPLOYERS_CACHE_DIR"],
    )

    for directory in directories:
        if not os.path.exists(directory):
            print("Creating directory {}".format(directory))
            os.mkdir(directory)

    print("Initializing database")
    db.init_db()


@cmd_bp.cli.command('update')
def update():
    '''Download employer and job summary list'''
    source.fetch_all()


@cmd_bp.cli.command('update-stats')
def update_stats():
    update_jobs_stats()


def update_jobs_stats():
    '''Show jobs stats'''
    with open(app.config["JOBS_JSON_FILE"], 'r') as jobs_file:
        jobs = json.load(jobs_file)

    emps = {}
    tags = {}
    locs = {
        "Ho Chi Minh": 0,
        "Ha Noi": 0,
        "Da Nang": 0,
        "Others": 0,
    }

    for job in jobs:
        add_job_to_employer(emps, job)
        count_job_tags(tags, job)
        count_job_locations(locs, job)

    print("Found {} jobs on {} employers.".format(len(jobs), len(emps)))
    print("Found {} tags.".format(len(tags)))
    for loc in locs:
        print("Found {} jobs in {}.".format(locs[loc], loc))

    emp_with_jobs = emps_per_job_count(emps)
    for count in sorted(emp_with_jobs):
        print("Found {} employers with {} offers.".format(emp_with_jobs[count], count))


def add_job_to_employer(emps, job):
    emp = job["employer_code"]
    if emp in emps:
        emps[emp] += 1
    else:
        emps[emp] = 1


def count_job_tags(tags, job):
    for tag in job["tags"]:
        if tag in tags:
            tags[tag] += 1
        else:
            tags[tag] = 1


def count_job_locations(locs, job):
    for location in job["address"]:
        if location in locs:
            locs[location] += 1


def emps_per_job_count(emps):
    emp_with_jobs = {}
    for emp in emps:
        count = emps[emp]
        if count in emp_with_jobs:
            emp_with_jobs[count] += 1
        else:
            emp_with_jobs[count] = 1
    return emp_with_jobs


@cmd_bp.cli.command('download')
@click.argument('type', default="all")
def download(type):
    '''Store jobs and employers related to update in json files'''
    if type == "all":
        do_jobs = True
        do_employers = True
    elif type == "jobs":
        do_jobs = True
        do_employers = False
    elif type == "employers":
        do_jobs = False
        do_employers = True
    else:
        print("Error: Invalid download option.")
        print("Download command accepts: all, jobs, employers. (all)")
        exit(1)

    if do_jobs:
        job_codes = source.get_job_codes()
        job_total = len(job_codes)
        job_count = 0
        for job_code in job_codes:
            job_count += 1
            print("Fetching job {}/{}: {}".format(job_count, job_total, job_code))
            cache.fetch_job(job_code)
            time.sleep(1)

    if do_employers:
        employer_codes = source.get_employers_with_jobs()
        emp_total = len(employer_codes)
        emp_count = 0
        for employer_code in employer_codes:
            emp_count += 1
            print("Fetching employer {}/{}: {}".format(emp_count, emp_total, employer_code))
            cache.fetch_employer(employer_code)
            time.sleep(1)

    if do_jobs:
        print("{} jobs".format(job_total))
    if do_employers:
        print("{} employers".format(emp_total))


@cmd_bp.cli.command('load')
def load():
    '''Will load employers from newest jobs to oldest'''
    for emp_code in source.get_employers_with_jobs():
        print("# Employer: {}".format(emp_code))

        emp_d = cache.get_employer(emp_code)
        compose_employer_reviews(emp_d)
        jobtags_to_jobcodes(emp_d)
        jobcodes_to_jobs(emp_d)
        str_to_address(emp_d)
        str_to_tag(emp_d)
        emp_d["why"] = to_json(emp_d["why"], indent=None)

        emp = Employer(**emp_d)
        db.session.add(emp)
        db.session.commit()


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


@cmd_bp.cli.command('tags-count')
def tags_count():
    tags = db.session.query(Tag).all()
    jobs_count = Job.query.count()

    result = []
    for tag in tags:
        count = len(tag.jobs.all())
        if not count:
            continue
        perc = (count / jobs_count) * 100
        result.append((tag.name, count, round(perc, 2)))
    result.sort(key=lambda j: j[1], reverse=True)

    pprint(result)


@cmd_bp.cli.command('employers-jobs-count')
def employers_jobs_count():
    from sqlalchemy import func, desc

    query = db.session.query(Job.employer_code, func.count(Job.employer_code).label('count'))
    query = query.group_by(Job.employer_code).order_by(desc("count")).limit(100)
    print(query)
    for row in query:
        print(row)


@job_bp.cli.command('show')
@click.argument('jid')
def job_show(jid):
    pprint(Job.query.filter(Job.id == jid).first().__dict__)


@job_bp.cli.command('parse')
@click.argument('code')
def parse_job(code):
    job_p = JobParser(code)
    job_p.fetch_and_parse()
    job_d = job_p.digest()

    pprint(job_d)


@job_bp.cli.command('instance')
@click.argument('code')
def instantiate_job(code):
    job_p = JobParser(code)
    job_p.fetch_and_parse()
    job = Job.from_dict(job_p.get_dict())

    pprint(job)


# employer ############################################################
@emp_bp.cli.command('parse')
@click.argument('code')
def parse_employer(code):
    employer_p = EmployerParser(code)
    employer_p.fetch_and_parse()
    employer_p.fetch_and_parse_reviews()

    pprint(employer_p.__dict__)


@emp_bp.cli.command('feed2json')
@click.argument('max_count', default=10_000)
def employer_feed2json(max_count=None):
    if max_count is None:
        max_count = 100_000
    max_count = int(max_count)

    feed = EmployerFeed()
    print("Employers: {}".format(len(feed)))
    loop_count = 0

    employer_l = []
    for (emp_code, _) in feed:
        employer_l.append(emp_code)
    employer_l.sort()

    exceptions = ("commgate-vn", "proview", "saigon-casa", "skybloom", "wav")  # 404
    start_with = ""
    skip = True

    for emp_code in employer_l:
        loop_count = loop_count + 1
        if start_with == emp_code:
            skip = False
        if skip:
            continue
        if emp_code in exceptions:
            continue

        print("#{} {}".format(loop_count, emp_code))

        p = EmployerParser(emp_code)
        p.fetch_and_parse()
        p.save_json()

        if loop_count == max_count:
            break

        time.sleep(1)


@emp_bp.cli.command('prio2json')
@click.argument('max_count', default=None)
def employer_prio2json(max_count):
    if max_count is None:
        max_count = 100_000
    max_count = int(max_count)

    # To be modified/populated as necessary ###############
    prio_list = []
    start_with = ""
    ####################################

    print("Employers: {}".format(len(prio_list)))
    exceptions = ("commgate-vn", "proview", "saigon-casa", "skybloom", "wav")  # 404
    loop_count = 0
    skip = True

    for emp_code in prio_list:
        loop_count = loop_count + 1
        if start_with <= emp_code:
            skip = False
        if skip:
            continue
        if emp_code in exceptions:
            continue

        print("#{} {}".format(loop_count, emp_code))

        p = EmployerParser(emp_code)
        p.fetch_and_parse()
        p.save_json()

        if loop_count == max_count:
            break

        time.sleep(1)


@emp_bp.cli.command('with-job')
def employer_with_job():
    query = db.session.query(Job.employer_code).group_by(Job.employer_code).all()
    emp_w_job = []
    for row in query:
        emp_w_job.append(row[0])
    print(emp_w_job)
