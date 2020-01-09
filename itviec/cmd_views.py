import json
import glob
import click
from flask import Blueprint
from flask import current_app as app

# import itviec.ItViec as ItViec
import itviec.parsers
from itviec.db import session
from itviec.models import Job, Employer, Tag, JobTag

# for debugging
from pprint import pprint

bp = Blueprint('itviec_cmd', __name__, cli_group=None)


@bp.cli.command('update-db')
def update_db():
    itv = ItViec.ItViec()

    for section in ItViec._init_ITViecSections():
        print(section)

        for page in section:
            print("main: Page: " + page.url)

            for job in page:
                # ~ print(job.id)

                if itv.db.has_job_id(job.id):
                    continue
                else:
                    pass
                    # itv.add_job(job)

    itv.close()


@bp.cli.command('test-job')
@click.argument('jid')
def test_job(jid):
    print(Job.request_job(jid))


@bp.cli.command('test-emp')
@click.argument('code')
def test_emp(code):
    employer = Employer.request_employer(code)
    # print(employer)
    pprint(employer.__dict__)


@bp.cli.command('test-emp-feed')
# @click.argument('code')
def test_emp_feed():
    feed = itviec.parsers.EmployerFeed()
    # print("feed: " + str(feed))
    print("feed.len: " + str(len(feed)))
    # print("feed class: " + str(feed.__class__))
    # print("feed response.text: " + feed.response.text)
    # print("feed.json class: " + str(feed.json.__class__))
    for emp_pack in feed.json:
        emp_code = emp_pack[0]
        print("Employer code: {}".format(emp_code))
        emp_instance = Employer.request_employer(emp_code)
        emp_sum = "Jobs: {} Reviews: {}"
        print(emp_instance, emp_sum.format(len(emp_instance.jobs), len(emp_instance.reviews)))
        print("<------------------------------------>")


@bp.cli.command('test-jobs-feed')
def test_jobs_feed():
    feed = itviec.parsers.JobsFeed()

    for job_tag in feed.job_tags():
        job = Job.from_tag(job_tag)

        # print(str(job.__class__))
        print(job.last_update, job, "@", job.employer_code)
        print(job.address)
        print(job.tags)


@bp.cli.command('update-jobs')
def update_jobs():
    feed = itviec.parsers.JobsFeed()
    j_count = 1

    for j_tag in feed.job_tags():
        job = Job.from_tag(j_tag)
        job.save()

        job_msg = "{}: {} @ {}"
        print(job_msg.format(j_count, job, job.employer_code))
        j_count += 1


@bp.cli.command('job-tag-json')
@click.argument('max')
def job_tag_json(max=None):
    if max:
        try:
            max = int(max)
        except:
            pass

    feed = itviec.parsers.JobsFeed()

    for j_tag in feed.job_tags():
        p = itviec.parsers.JobSummaryParser(j_tag)

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


@bp.cli.command('job-json-dict')
def job_json_dict(max=None):

    job_dicts = load_jobs_json()

    tags = {}
    addresses = {}
    jobs = []
    for jd in job_dicts:
        # for tag in jd["tags"]:
        #     tags[tag] = ""
        # for add in jd["address"]:
        #     addresses[add] = ""
        # for key in jd:
        #     pprint(jd[key])
        jobs.append(Job.from_dict(jd))

    print("Tags:", str(tags.keys()))
    print("Addresses:", str(addresses.keys()))
    session.commit()

    return None


@bp.cli.command('tags-count')
def tags_count():
    from sqlalchemy import func, desc

    query = session.query(Tag.name, func.count(JobTag.job_id).label('count'))
    print(query)
    query = query.join(JobTag).group_by(Tag.name).order_by(desc("count")).limit(20)
    print(query)
    for row in query:
        print(row)