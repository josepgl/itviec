from flask import Blueprint, render_template

from itviec.db import db
from itviec.models import Job, Tag, Address

bp = Blueprint('itviec', __name__, cli_group=None)


@bp.route("/")
def index():
    return render_template("front_page.html")


@bp.route("/jobs")
def jobs():
    jobs = db.session.query(Job).order_by(Job.id.desc()).limit(50)
    return render_template("jobs.html", jobs=jobs)


@bp.route("/job/<int:j_id>/")
def job(j_id):
    job = db.session.query(Job).filter(Job.id == j_id)
    if job is None:
        return render_template("404.html"), 404
    return render_template("job.html", job_id=j_id, j=job)


@bp.route("/jobs/hcm")
def hcm_jobs():
    hcm_jobs = Job.query.filter(Job.address.any(name="Ho Chi Minh"))
    return render_template("jobs.html", jobs=hcm_jobs)


@bp.route("/jobs/hanoi")
def hanoi_jobs():
    hanoi_jobs = Job.query.filter(Job.address.any(name="Ha Noi"))
    return render_template("jobs.html", jobs=hanoi_jobs)


@bp.route("/jobs/danang")
def danang_jobs():
    danang_jobs = Job.query.filter(Job.address.any(name="Da Nang"))
    return render_template("jobs.html", jobs=danang_jobs)


@bp.route("/jobs/other")
def other_jobs():
    jobs_union = Job.query.filter(Job.address.any(Address.name.in_(("Ho Chi Minh", "Ha Noi", "Da Nang"))))
    other_jobs = Job.query.except_(jobs_union)
    return render_template("jobs.html", jobs=other_jobs)


@bp.route("/tags")
def tags():
    tags = db.session.query(Tag).all()
    jobs_count = Job.query.count()

    result = []
    for tag in tags:
        count = len(tag.jobs.all())
        if not count:
            continue
        perc = (count / jobs_count) * 100
        result.append((tag.name, count, round(perc, 2)))
    result.sort(key=lambda j: j[1], reverse=True)

    return render_template("tags.html", tags=result)


@bp.route("/locations")
def locations():
    query = db.session.query(Address)
    locs = []
    for loc in query:
        if loc.name.startswith("District "):
            print(loc.name)
        else:
            locs.append(loc.name)
    # query = query.join(job_address).join(Job).group_by(Address.name).order_by(desc("count"))

    return render_template("locations.html", locations=locs)


@bp.route("/about")
def about():
    return render_template("about.html")
