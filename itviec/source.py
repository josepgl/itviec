import json
from datetime import datetime

from flask import current_app as app

from itviec.feeds import JobsFeed
from itviec.parsers import JobTagParser
from itviec.helpers import fetch_url, to_json_file


def fetch_jobs():
    '''Download job summary list'''
    jobs = []
    feed = JobsFeed()
    for page in feed:
        print(".", end='', flush=True)
        for job_tag in page:
            job_parser = JobTagParser(job_tag)
            jobs.append(job_parser.get_dict())
    print("")
    to_json_file(jobs, app.config["JOBS_JSON_FILE"])
    emp_count = len(get_employers_with_jobs())
    print("Found {} jobs from {} employers.".format(len(jobs), emp_count))


def fetch_employers():
    '''Download employer list'''
    response = fetch_url(app.config["EMPLOYERS_JSON_URL"], {})
    employers_count = len(response.json())
    to_json_file(response.json(), app.config["EMPLOYERS_JSON_FILE"])
    print("Found {} employers.".format(employers_count))


def fetch_all():
    fetch_employers()
    fetch_jobs()


def get_job_tags():
    try:
        with open(app.config["JOBS_JSON_FILE"], 'r') as jobs_file:
            jobs = json.load(jobs_file)
    except OSError:
        print("Job list missing. Run 'flask update' first.")
        exit(1)

    return jobs


def get_timed_job_tags():
    jobs = get_job_tags()
    for j in jobs:
        j["last_post"] = datetime.strptime(j["last_post"], app.config["DATETIME_FORMAT"])
    return jobs


def get_job_codes():
    return [j["code"] for j in get_job_tags()]


def get_employer_codes():
    try:
        with open(app.config["EMPLOYERS_JSON_FILE"], 'r') as emps_file:
            employers = json.load(emps_file)
    except OSError:
        print("Employer list missing. Run 'flask update' first.")
        exit(1)

    codes = [emp[0] for emp in employers]
    return codes


def get_employers_with_jobs():
    employers = {j["employer_code"]: None for j in get_job_tags()}
    return list(employers.keys())


def get_employers_with_feed_date():
    employers = {}
    for j in get_job_tags():
        if j["employer_code"] in employers:
            if employers[j["employer_code"]] < j["last_post"]:
                employers[j["employer_code"]] = j["last_post"]
        else:
            employers[j["employer_code"]] = j["last_post"]
    return employers


def get_employer_feed_date(employer_code):
    last_post = ""
    for j in get_job_tags():
        if j["employer_code"] == employer_code:
            if j["last_post"] > last_post:
                last_post = j["last_post"]
    if not last_post:
        return None
    return last_post
