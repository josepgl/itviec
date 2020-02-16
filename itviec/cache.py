import os
import json
from datetime import timedelta

from flask import current_app as app

from itviec.parsers import EmployerParser, JobParser
from itviec.time import str_to_datetime
from itviec.source import get_employer_feed_date


def fetch_employer(employer_code):
    employer_p = EmployerParser(employer_code)
    employer_p.fetch_and_parse()
    employer_p.fetch_and_parse_reviews()
    employer_p.save_json()


def fetch_job(job_code):
    job_p = JobParser(job_code)
    job_p.fetch_and_parse()
    job_p.save_json()


def get_job(job_code):
    filename = "{}.json".format(job_code)
    path = os.path.join(app.config["JOBS_CACHE_DIR"], filename)

    try:
        with open(path, "r") as json_file:
            return json.load(json_file)
    except OSError:
        raise


def get_employer(employer_code):
    filename = "{}.json".format(employer_code)
    path = os.path.join(app.config["EMPLOYERS_CACHE_DIR"], filename)

    try:
        with open(path, "r") as json_file:
            return json.load(json_file)
    except OSError:
        raise


def is_job_cache_hit(job_tag):
    '''Cache is valid up to 24 hours after last_post from job's feed.

    Input: job_tag from job's feed
    '''
    code = job_tag["code"]
    # A cache file must exist
    try:
        cache = get_job(code)
    except OSError:
        if app.config["DEBUG"] is True:
            print("Could not find cache for job with code '{}'".format(code))
        return False

    # Compare 'last_post' dates in cache and update list
    threshold = timedelta(days=1)
    cache_post = str_to_datetime(cache["last_post"])
    feed_post = str_to_datetime(job_tag["last_post"])
    delta = feed_post - cache_post

    # No more than 24h difference between feed and cache
    if delta <= threshold:
        return True

    if "VERBOSE" in app.config and app.config["VERBOSE"]:
        print("Delta: {} | Job: {}".format(delta, code))
    return False


def is_employer_cache_hit(code, last_post=None):
    # A cache file must exist
    try:
        cache = get_employer(code)
    except OSError:
        if app.config["DEBUG"] is True:
            print("Could not find cache for employer with code '{}'".format(code))
        return False

    if not last_post:
        last_post = get_employer_feed_date(code)

    threshold = timedelta(days=1)
    cache_post = str_to_datetime(cache["last_post"])
    feed_post = str_to_datetime(last_post)
    delta = feed_post - cache_post

    # No more than 24h difference between feed and cache
    if delta <= threshold:
        return True

    if "VERBOSE" in app.config and app.config["VERBOSE"]:
        print("Delta: {} | Employer: {}".format(delta, code))
    return False


def job_cache_or_fetch(job_tag):
    try:
        job_d = get_job(job_tag["code"])
    except OSError:
        fetch_job(job_tag["code"])
        job_d = get_job(job_tag["code"])
    return job_d


def employer_cache_or_fetch(employer_code):
    try:
        job_d = get_employer(employer_code)
    except OSError:
        fetch_employer(employer_code)
        job_d = get_employer(employer_code)
    return job_d


def is_job_cached(job_code):
    filename = "{}.json".format(job_code)
    path = os.path.join(app.config["JOBS_CACHE_DIR"], filename)
    return os.path.isfile(path)


def is_employer_cached(employer_code):
    filename = "{}.json".format(employer_code)
    path = os.path.join(app.config["EMPLOYERS_CACHE_DIR"], filename)
    return os.path.isfile(path)
