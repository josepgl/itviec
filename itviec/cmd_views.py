import os
import time
import json

import click
from flask import Blueprint
from flask import current_app as app

from itviec import source
from itviec import cache
from itviec.db import db
from itviec.composers import compose_employer


# for debugging
from pprint import pprint

cmd_bp = Blueprint('itviec_cmd', __name__, cli_group=None)


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
@click.argument('selected_type', default="all")
def download(selected_type):
    '''Store jobs and employers related to update in json files'''
    if selected_type == "all":
        do_jobs = True
        do_employers = True
    elif selected_type == "jobs":
        do_jobs = True
        do_employers = False
    elif selected_type == "employers":
        do_jobs = False
        do_employers = True
    else:
        print("Error: Invalid download option.")
        print("Download command accepts: all, jobs, employers. (all)")
        exit(1)

    if do_jobs:
        batch_download("job")

    if do_employers:
        batch_download("employer")


def batch_download(name):
    batches = {
        "job": {
            "collection_func": source.get_job_codes,
            "fetch_func": cache.fetch_job,
        },
        "employer": {
            "collection_func": source.get_employers_with_jobs,
            "fetch_func": cache.fetch_employer,
        },
    }

    if name not in batches:
        raise KeyError("Download batch not found.")

    codes = batches[name]["collection_func"]()
    total = len(codes)
    count = 0
    for code in codes:
        count += 1
        print("Fetching {} {}/{}: {}".format(name, count, total, code))
        batches[name]["fetch_func"](code)
        time.sleep(0.7)


@cmd_bp.cli.command('load')
def load():
    '''Will load employers from newest jobs to oldest'''
    for emp_code in source.get_employers_with_jobs():
        print("# Employer: {}".format(emp_code))

        emp_d = cache.get_employer(emp_code)
        employer = compose_employer(emp_d)

        db.session.add(employer)
        db.session.commit()


@cmd_bp.cli.command('install')
@click.argument('employer_code')
def install(employer_code):
    print("Installing employer '{}'...".format(employer_code))
    cache.fetch_employer(employer_code)
    emp_d = cache.get_employer(employer_code)

    # pprint(emp_d)

    for job_code in emp_d["jobs"]:
        cache.fetch_job(job_code)

    employer = compose_employer(emp_d)
    pprint(employer.__dict__)
