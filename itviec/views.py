import click
from flask import Blueprint, render_template

import itviec.ItViec as ItViec
import itviec.models

bp = Blueprint('itviec', __name__, cli_group=None)


@bp.route("/")
def index():
    return render_template("front_page.html")


@bp.route("/jobs")
def jobs():
    itv = ItViec.ItViec()
    jids = itv.get_latest_jobids()
    jobs = itv.get_jobs(jids)
    return render_template("jobs.html", jobs=jobs)


@bp.route("/jobs/<int:j_id>/")
def job(j_id):
    itv = ItViec.ItViec()
    j = itv.get_job(j_id)
    if j is None:
        return render_template("404.html"), 404
    return render_template("job.html", job_id=j_id, j=j)


@bp.route("/hcm")
def hcm():
    return render_template("hcm.html")


@bp.route("/tags")
def tags():
    itv = ItViec.ItViec()
    tags_count = itv.get_tags_count()
    return render_template("tags.html", tags=tags_count)


@bp.route("/about")
def about():
    return render_template("about.html")


# cli blueprints
@bp.cli.command('update-db')
# @click.argument('name')
# def update_db(name):
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
    print(itviec.models.Job.request_job(jid))


@bp.cli.command('test-emp')
@click.argument('code')
def test_emp(code):
    print(itviec.models.Employer.request_employer(code))


@bp.cli.command('test-emp-feed')
# @click.argument('code')
def test_emp_feed():
    feed = itviec.parsers.EmployerFeed()
    print("feed: " + str(feed))
    print("feed.len: " + str(len(feed)))
    print("feed class: " + str(feed.__class__))
    # print("feed response.text: " + feed.response.text)
    print("feed.json class: " + str(feed.json.__class__))
    for emp_pack in feed.json:
        emp_code = emp_pack[0]
        print("Employer code: {}".format(emp_code))
        emp_instance = itviec.models.Employer.request_employer(emp_code)
        print(emp_instance)


@bp.cli.command('test-jobs-feed')
def test_jobs_feed():
    feed = itviec.parsers.JobsFeed()

    for job_tag in feed.job_tags():
        job = itviec.models.Job.from_tag(job_tag)

        # print(str(job.__class__))
        print(job.last_update, job, "@", job.employer_code)
        print(job.address)
        print(job.tags)
