import os
import time
import json
import glob

import click
from flask import Blueprint
from flask import current_app as app

import itviec.parsers
import itviec.helpers
from itviec.db import db
from itviec.models import Job, Employer, Tag, JobTag, Address

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
    jobtags = JobTag.query.count()

    print("Jobs: {}".format(jobs))
    print("Tags: {}".format(tags))
    print("Addresses: {}".format(addresses))
    print("JobTags: {}".format(jobtags))
    print("Employers: {}".format(employers))


# Commands ###########################################
@cmd_bp.cli.command('init')
def init_db():
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
    update_employers()
    update_jobs()


@cmd_bp.cli.command('update-stats')
def update_stats():
    update_jobs_stats()


def update_jobs_stats():
    '''Show jobs stats'''
    with open(app.config["JOBS_JSON_FILE"], 'r') as jobs_file:
        jobs = json.load(jobs_file)
    emps = {}
    tags = {}
    hcm = 0
    han = 0
    other = 0
    for job in jobs:
        emp = job["employer_code"]

        if emp in emps:
            emps[emp] += 1
        else:
            emps[emp] = 1

        for tag in job["tags"]:
            if tag in tags:
                tags[tag] += 1
            else:
                tags[tag] = 1

        if "Ho Chi Minh" in job["address"]:
            hcm += 1
        if "Ha Noi" in job["address"]:
            han += 1
        if "Ha Noi" not in job["address"] and "Ho Chi Minh" not in job["address"]:
            other += 1

    print("Found {} jobs on {} employers.".format(len(jobs), len(emps)))
    print("Found {} tags.".format(len(tags)))
    print("Found {} jobs in HCM.".format(hcm))
    print("Found {} jobs in Ha Noi.".format(han))
    print("Found {} jobs in other locations.".format(other))

    six_jobs = 0
    five_jobs = 0
    four_jobs = 0
    three_jobs = 0
    two_jobs = 0
    one_job = 0
    for emp in emps:
        if emps[emp] >= 6:
            six_jobs += 1
        elif emps[emp] == 5:
            five_jobs += 1
        elif emps[emp] == 4:
            four_jobs += 1
        elif emps[emp] == 3:
            three_jobs += 1
        elif emps[emp] == 2:
            two_jobs += 1
        elif emps[emp] == 1:
            one_job += 1
    print("Found {} employers with 6 or more offers.".format(six_jobs))
    print("Found {} employers with 5 offers.".format(five_jobs))
    print("Found {} employers with 4 offers.".format(four_jobs))
    print("Found {} employers with 3 offers.".format(three_jobs))
    print("Found {} employers with 2 offers.".format(two_jobs))
    print("Found {} employers with 1 offers.".format(one_job))
    # for date in dates.keys().sort():
    #     print("{}: ".format(date), "." * dates[date])


def update_jobs():
    '''Download job summary list'''
    jobs = []
    feed = itviec.parsers.JobsFeed()
    for page in feed:
        print(".", end='', flush=True)
        for job_tag in page:
            job_parser = itviec.parsers.JobTagParser(job_tag)
            jobs.append(job_parser.get_dict())
    print("")
    print("Found {} jobs.".format(len(jobs)))
    with open(app.config["JOBS_JSON_FILE"], 'w') as jobs_file:
        jobs_file.write(json.dumps(jobs, sort_keys=True, indent=2))


def update_employers():
    '''Download employer list'''
    r = itviec.helpers.fetch_url(app.config["EMPLOYERS_JSON_URL"], {})
    employers_count = len(r.json())
    print("Found {} employers.".format(employers_count))
    with open(app.config["EMPLOYERS_JSON_FILE"], 'w') as emps_file:
        emps_file.write(json.dumps(r.json(), sort_keys=True, indent=2))


@cmd_bp.cli.command('download')
def download():
    try:
        with open(app.config["JOBS_JSON_FILE"], 'r') as jobs_file:
            jobs = json.load(jobs_file)
    except FileNotFoundError:
        print("Job list missing. Run 'flask update' first.")
        exit(1)

    employer_list = get_employers(jobs)
    print("{} employers".format(len(employer_list)))
    print("{} jobs".format(len(jobs)))

    for employer_code in employer_list:
        download_employer(employer_code)
        time.sleep(3)

    for job in jobs:
        download_job(job["code"])
        time.sleep(1)


def download_job(job_code):
    job_p = itviec.parsers.JobParser(job_code)
    job_p.fetch_and_parse()
    job_p.save_json()
    return job_p.get_dict()


def download_employer(employer_code):
    employer_p = itviec.parsers.EmployerParser(employer_code)
    employer_p.fetch_and_parse()
    employer_p.fetch_and_parse_reviews()
    employer_p.save_json()
    return employer_p.get_dict()


def get_employers(job_list):
    employers = {}
    for job in job_list:
        employers[job["employer_code"]] = None
    return employers.keys()


@cmd_bp.cli.command('test-emp-feed')
def test_emp_feed():
    feed = itviec.parsers.EmployerFeed()
    print("feed.len: " + str(len(feed)))
    for emp_pack in feed.json:
        emp_code = emp_pack[0]
        print("Employer code: {}".format(emp_code))
        employer_p = itviec.parsers.EmployerParser(emp_code)
        employer = Employer(**employer_p)
        emp_sum = "Jobs: {} Reviews: {}"
        print(employer, emp_sum.format(len(employer.jobs), len(employer.reviews)))
        print("<------------------------------------>")


@cmd_bp.cli.command('test-jobs-feed')
def test_jobs_feed():
    feed = itviec.parsers.JobsFeed()

    for job_tag in feed.job_tags():
        job_p = itviec.parsers.JobTagParser(job_tag)
        job = Job.from_dict(job_p.get_dict())

        print(job.last_update, job, "@", job.employer_code)
        print(job.address)
        print(job.tags)


@cmd_bp.cli.command('upgrade-jobs')
def upgrade_jobs():
    feed = itviec.parsers.JobsFeed()
    j_count = 1

    for j_tag in feed.job_tags():
        job_p = itviec.parsers.JobTagParser(j_tag)
        job = Job.from_dict(job_p.get_dict())
        job.save()

        job_msg = "{}: {} @ {}"
        print(job_msg.format(j_count, job, job.employer_code))
        j_count += 1


@cmd_bp.cli.command('tags-count')
def tags_count():
    from sqlalchemy import func, desc

    query = db.session.query(Tag.name, func.count(JobTag.job_id).label('count'))
    query = query.join(JobTag).group_by(Tag.name).order_by(desc("count")).limit(20)
    print(query)
    for row in query:
        print(row)


@cmd_bp.cli.command('employers-jobs-count')
def employers_jobs_count():
    from sqlalchemy import func, desc

    query = db.session.query(Job.employer_code, func.count(Job.employer_code).label('count'))
    query = query.group_by(Job.employer_code).order_by(desc("count")).limit(100)
    print(query)
    for row in query:
        print(row)


# job ############################################################
@job_bp.cli.command('feed2json')
def job_feed2json():
    feed = itviec.parsers.JobsFeed()

    for j_tag in feed.job_tags():
        p = itviec.parsers.JobTagParser(j_tag)

        print(p.get_json())
        p.save_json()


def load_jobs_json():
    filenames = glob.glob("{}/jobs/*.json".format(app.instance_path))

    job_dicts = []
    for filename in filenames:
        with open(filename, 'r') as json_file:
            jdict = json.load(json_file)
            job_dicts.append(jdict)
    return job_dicts


@job_bp.cli.command('json2db')
def job_json2dict():
    job_dicts = load_jobs_json()

    jobs = []
    for jd in job_dicts:
        jobs.append(Job.from_dict(jd))

    db.session.commit()


@job_bp.cli.command('show')
@click.argument('jid')
def job_show(jid):
    pprint(Job.query.filter(Job.id == jid).first().__dict__)


@job_bp.cli.command('parse')
@click.argument('code')
def parse_job(code):
    job_p = itviec.parsers.JobParser(code)
    job_p.fetch_and_parse()
    job_d = job_p.digest()

    pprint(job_d)


@job_bp.cli.command('instance')
@click.argument('code')
def instantiate_job(code):
    job_p = itviec.parsers.JobParser(code)
    job_p.fetch_and_parse()
    job = Job.from_dict(job_p.get_dict())

    pprint(job)


# employer ############################################################
@emp_bp.cli.command('parse')
@click.argument('code')
def parse_employer(code):
    employer_p = itviec.parsers.EmployerParser(code)
    employer_p.fetch_and_parse()
    employer_p.fetch_and_parse_reviews()

    pprint(employer_p.__dict__)


@emp_bp.cli.command('feed2json')
@click.argument('max_count', default=10_000)
def employer_feed2json(max_count=None):
    import time

    if max_count is None:
        max_count = 100_000
    max_count = int(max_count)

    feed = itviec.parsers.EmployerFeed()
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

        p = itviec.parsers.EmployerParser(emp_code)
        p.fetch_and_parse()
        p.save_json()

        if loop_count == max_count:
            break

        time.sleep(1)


@emp_bp.cli.command('prio2json')
@click.argument('max_count', default=None)
def employer_prio2json(max_count):
    import time

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

        p = itviec.parsers.EmployerParser(emp_code)
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
