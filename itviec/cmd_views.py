import json
import glob
import click
from flask import Blueprint
from flask import current_app as app

import itviec.parsers
from itviec.db import db
from itviec.models import Job, Employer, Tag, JobTag, Address

# for debugging
from pprint import pprint

cmd_bp = Blueprint('itviec_cmd', __name__, cli_group=None)
db_bp = Blueprint('itviec_cmd_db', __name__, cli_group="db")
job_bp = Blueprint('itviec_cmd_job', __name__, cli_group="job")
emp_bp = Blueprint('itviec_cmd_employer', __name__, cli_group="employer")


@db_bp.cli.command('init')
def init_db():
    print("Initializing database")
    db.init_db()


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


@cmd_bp.cli.command('update-db')
def update_db():
    pass


@cmd_bp.cli.command('test-emp-feed')
def test_emp_feed():
    feed = itviec.parsers.EmployerFeed()
    print("feed.len: " + str(len(feed)))
    for emp_pack in feed.json:
        emp_code = emp_pack[0]
        print("Employer code: {}".format(emp_code))
        emp_instance = Employer.request_employer(emp_code)
        emp_sum = "Jobs: {} Reviews: {}"
        print(emp_instance, emp_sum.format(len(emp_instance.jobs), len(emp_instance.reviews)))
        print("<------------------------------------>")


@cmd_bp.cli.command('test-jobs-feed')
def test_jobs_feed():
    feed = itviec.parsers.JobsFeed()

    for job_tag in feed.job_tags():
        job = Job.from_tag(job_tag)

        print(job.last_update, job, "@", job.employer_code)
        print(job.address)
        print(job.tags)


@cmd_bp.cli.command('update-jobs')
def update_jobs():
    feed = itviec.parsers.JobsFeed()
    j_count = 1

    for j_tag in feed.job_tags():
        job = Job.from_tag(j_tag)
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
def job_feed2json(max=None):
    if max:
        try:
            max = int(max)
        except:
            pass

    feed = itviec.parsers.JobsFeed()

    for j_tag in feed.job_tags():
        p = itviec.parsers.JobTagParser(j_tag)

        print(p.get_json())
        p.save_json()

        if max:
            max = max - 1
            if max < 1:
                break


def load_jobs_json():
    filenames = glob.glob("{}/jobs/*.json".format(app.instance_path))

    job_dicts = []
    for filename in filenames:
        with open(filename, 'r') as json_file:
            jdict = json.load(json_file)
            job_dicts.append(jdict)
    return job_dicts


@job_bp.cli.command('json2db')
def job_json2dict(max=None):

    job_dicts = load_jobs_json()

    jobs = []
    for jd in job_dicts:
        jobs.append(Job.from_dict(jd))

    db.session.commit()

    return None


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
    employer_p.digest()
    employer_p.fetch_and_parse_reviews()

    # pprint(employer_p.__dict__)
    pprint(employer_p.reviews)
    # for rev in employer_p.reviews:
    #     pprint(rev.review)


@emp_bp.cli.command('feed2json')
@click.argument('max_count', default=10_000)
def employer_feed2json(max_count=None):
    import time
    import random

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
        # pprint(p.emp)
        # print(p.get_json())
        p.save_json()

        if loop_count == max_count:
            break

        # time.sleep(0.9)
        time.sleep(random.randrange(4, 12, 1) / 10)


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

        time.sleep(0.8)


@emp_bp.cli.command('with-job')
def employer_with_job():
    query = db.session.query(Job.employer_code).group_by(Job.employer_code).all()
    emp_w_job = []
    for row in query:
        emp_w_job.append(row[0])
    print(emp_w_job)
