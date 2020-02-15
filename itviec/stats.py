import json

from flask import current_app as app

from itviec.db import db
from itviec.models import Job
from itviec.helpers import str_to_datetime


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


def to_be_updated():
    with open(app.config["JOBS_JSON_FILE"], 'r') as jobs_file:
        jobs = json.load(jobs_file)

    jobs_to_update = []
    deltas = []
    for job in jobs:
        has_job = db.session.query(Job).filter_by(code=job["code"]).first()
        if has_job:
            delta = get_delta(job["last_post"], has_job.last_post)
            deltas.append(delta)

            if has_job and has_job.last_post == job["last_post"]:
                continue

        jobs_to_update.append(job)

    result = {
        "jobs": len(jobs_to_update),
        "employers": len(get_employers_from_job_tags(jobs_to_update))
    }

    print("To be updated: {} jobs from {} employers.".format(result["jobs"], result["employers"]))
    print_delta_distribution(deltas)


def get_employers_from_job_tags(job_tags):
    employers = {j["employer_code"]: None for j in job_tags}
    return list(employers.keys())


def get_delta(new, old):
    new_dt = str_to_datetime(new)
    old_dt = str_to_datetime(old)
    return new_dt - old_dt


def print_delta_distribution(deltas):
    total_deltas = len(deltas)
    for hours in range(1, 24):
        count = 0
        for d in deltas:
            hours_in_seconds = hours * 60 * 60
            if d > hours_in_seconds:
                count += 1
        percent = round(count * 100 / total_deltas, 2)
        print("{} % of deltas differ more than {} hours".format(percent, hours))
