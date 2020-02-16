import time
from datetime import timedelta

from flask import current_app as app

from itviec.db import db
from itviec import source
from itviec.models import Employer, Job
from itviec.time import str_to_datetime
from itviec.composers import install_employer
import itviec.source

from itviec.update import update_employer


def download():
    feed_jobs = source.get_job_tags()
    downloads = calculate_downloads(feed_jobs)

    input("Press any key to continue...")

    download_jobs(downloads["jobs"])
    download_employers(downloads["employers"])


def upgrade():
    feed_jobs = source.get_job_tags()
    upd = calculate_updates(feed_jobs)

    if not (upd["employers"]["update"] or upd["employers"]["create"] or
            upd["jobs"]["update"] or upd["jobs"]["create"]):
        exit()

    input("Press any key to continue...")

    if upd["employers"]["create"]:
        print("Creating new employers...")
        for employer_code in upd["employers"]["create"]:
            install_employer(employer_code)

    if upd["employers"]["update"]:
        print("Updating employers...")
        for employer_code in upd["employers"]["update"]:
            print("Updating employer " + employer_code)
            update_employer(employer_code)

    if upd["jobs"]["update"] or upd["jobs"]["create"]:
        print("Updating jobs...")
        for job in upd["jobs"]["update"] + upd["jobs"]["create"]:
            update_employer(job["employer_code"])

    calculate_updates(feed_jobs)


def calculate_downloads(feed_jobs):
    jobs = calculate_job_downloads(feed_jobs)
    employers = calculate_employer_downloads(feed_jobs)

    for job_tag in jobs:
        if not itviec.cache.is_employer_cache_hit(job_tag["employer_code"]):
            if job_tag["employer_code"] not in employers:
                employers.append(job_tag["employer_code"])

    print("Downloads: jobs: {} employers: {}".format(len(jobs), len(employers)))
    return {"jobs": jobs, "employers": employers}


def calculate_job_downloads(feed_jobs):
    jobs = []
    for job in feed_jobs:
        valid_cache = itviec.cache.is_job_cache_hit(job)
        if not valid_cache:
            jobs.append(job)
    return jobs


def calculate_employer_downloads(feed_jobs):
    employers = {}
    for job in feed_jobs:
        employer_code = job["employer_code"]
        if employer_code in employers:
            continue
        valid_cache = itviec.cache.is_employer_cache_hit(employer_code, job["last_post"])
        if not valid_cache:
            employers[employer_code] = None
    return list(employers)


def download_jobs(job_tags):
    j_count = 0
    j_total = len(job_tags)
    for job in job_tags:
        j_count += 1
        print("Downloading job {}/{} {}...".format(j_count, j_total, job["code"]))
        itviec.cache.fetch_job(job["code"])
        time.sleep(0.7)


def download_employers(employers):
    '''Input: employer_code list'''
    e_count = 0
    e_total = len(employers)
    for employer_code in employers:
        e_count += 1
        print("Downloading employer {}/{} {}...".format(e_count, e_total, employer_code))
        itviec.cache.fetch_employer(employer_code)
        time.sleep(0.7)


def calculate_updates(feed_jobs):
    jobs = calculate_job_upgrades(feed_jobs)

    if jobs["create"]:
        print("Refreshing cache of employers with new jobs")
        for job_tag in jobs["create"]:
            # force fetch employer for new jobs
            itviec.cache.fetch_employer(job_tag["employer_code"])

    employers = calculate_employer_upgrades(feed_jobs)

    for job_tag in jobs["create"]:
        db_emp = db.session.query(Employer).filter_by(code=job_tag["employer_code"]).first()
        if db_emp:
            if job_tag["employer_code"] not in employers["update"]:
                employers["update"].append(job_tag["employer_code"])
        else:
            if job_tag["employer_code"] not in employers["create"]:
                employers["create"].append(job_tag["employer_code"])

    if employers["update"] or employers["create"] or jobs["update"] or jobs["create"]:
        print("Total employer upgrades: updates: {}, new: {}".format(
            len(employers["update"]), len(employers["create"])))
        print("Total job upgrades: updates: {}, new: {}".format(
            len(jobs["update"]), len(jobs["create"])))
    else:
        print("Done.")

    return {"jobs": jobs, "employers": employers}


def calculate_job_upgrades(feed_jobs):
    jobs = {"create": [], "update": []}
    up_to_date_counter = 0

    for job in feed_jobs:
        has_job = Job.query.filter(Job.code == job["code"]).first()

        if has_job:
            threshold = timedelta(days=1)
            db_date = str_to_datetime(has_job.last_post).date()
            feed_date = str_to_datetime(job["last_post"]).date()
            delta = feed_date - db_date
            updated_db = delta <= threshold

            if updated_db:
                up_to_date_counter += 1
            else:
                jobs["update"].append(job)

        else:
            print("Job '{}' not found in database, needs to be created.".format(job["code"]))
            jobs["create"].append(job)

    if "VERBOSE" in app.config and app.config["VERBOSE"]:
        print("Jobs upgrades: update: {}, create: {}".format(
            len(jobs["update"]), len(jobs["create"])))

    return jobs


def calculate_employer_upgrades(feed_jobs):
    employers = {"create": [], "update": []}
    already_up_to_date = 0

    emp_dates = source.get_employers_with_feed_date()
    done = []

    for job in feed_jobs:
        employer_code = job["employer_code"]
        if employer_code in done:
            continue
        done.append(employer_code)

        query = db.session.query(Employer).filter_by(code=employer_code)
        has_emp = query.first()

        if has_emp:
            threshold = timedelta(days=1)
            db_date = str_to_datetime(has_emp.last_post).date()
            feed_date = str_to_datetime(emp_dates[employer_code]).date()
            delta = feed_date - db_date
            updated_db = delta <= threshold

            if updated_db:
                already_up_to_date += 1
            else:
                if "VERBOSE" in app.config and app.config["VERBOSE"]:
                    print("Delta: {} | Employer: {}".format(delta, employer_code))
                employers["update"].append(employer_code)

        else:
            employers["create"].append(employer_code)

    if "VERBOSE" in app.config and app.config["VERBOSE"]:
        print("Employer upgrades: update: {}, create: {}".format(
            len(employers["update"]), len(employers["create"])))

    return employers
