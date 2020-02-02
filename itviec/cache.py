import os
import json

from flask import current_app as app

from itviec.parsers import EmployerParser, JobParser


def fetch_employer(employer_code):
    employer_p = EmployerParser(employer_code)
    employer_p.fetch_and_parse()
    employer_p.fetch_and_parse_reviews()
    employer_p.save_json()
    # return employer_p.get_dict()


def fetch_job(job_code):
    job_p = JobParser(job_code)
    job_p.fetch_and_parse()
    job_p.save_json()
    # return job_p.get_dict()


def get_job(job_code):
    filename = "{}.json".format(job_code)
    path = os.path.join(app.config["JOBS_CACHE_DIR"], filename)

    try:
        with open(path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        # print("Could not find file: {}".format(path))
        raise

    job_p = JobParser(job_code)
    job_p.run()

    return job_p.get_dict()


def get_employer(employer_code):
    filename = "{}.json".format(employer_code)
    path = os.path.join(app.config["EMPLOYERS_CACHE_DIR"], filename)

    try:
        with open(path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        # print("Could not find file: {}".format(path))
        raise

    emp_p = EmployerParser(employer_code)
    emp_p.run()

    return emp_p.get_dict()
