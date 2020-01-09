from flask import Blueprint, render_template
from flask import current_app as app

# import itviec.ItViec as ItViec
from itviec.db import db
from itviec.models import Job, Employer, Tag

# for debugging
from pprint import pprint

bp = Blueprint('itviec', __name__, cli_group=None)


@bp.route("/")
def index():
    return render_template("front_page.html")


@bp.route("/jobs")
def jobs():
    jobs = db.session.query(Job).order_by(Job.id.desc()).limit(50)
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
    from sqlalchemy import func, desc
    from itviec.models import JobTag

    query = db.session.query(Tag.name, func.count(JobTag.job_id).label('count'))
    query = query.join(JobTag).group_by(Tag.name).order_by(desc("count"))

    return render_template("tags.html", tags=query)


@bp.route("/about")
def about():
    return render_template("about.html")
