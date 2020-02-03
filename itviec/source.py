import json

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
    print("Found {} jobs.".format(len(jobs)))
    to_json_file(jobs, app.config["JOBS_JSON_FILE"])


def fetch_employers():
    '''Download employer list'''
    response = fetch_url(app.config["EMPLOYERS_JSON_URL"], {})
    employers_count = len(response.json())
    print("Found {} employers.".format(employers_count))
    to_json_file(response.json(), app.config["EMPLOYERS_JSON_FILE"])


def fetch_all():
    fetch_employers()
    fetch_jobs()


def get_jobtags():
    try:
        with open(app.config["JOBS_JSON_FILE"], 'r') as jobs_file:
            jobs = json.load(jobs_file)
    except OSError:
        print("Job list missing. Run 'flask update' first.")
        exit(1)

    return jobs


def get_job_codes():
    return [j["code"] for j in get_jobtags()]


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
    employers = {j["employer_code"]: None for j in get_jobtags()}
    return list(employers.keys())
