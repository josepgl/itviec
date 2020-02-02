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
