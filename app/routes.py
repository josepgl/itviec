from flask import Blueprint, render_template
from ItViec import ItViec

bp = Blueprint('itviec', __name__)


@bp.route("/")
def index():
    return render_template("front_page.html")


@bp.route("/jobs")
def jobs():
    itviec = ItViec()
    jids = itviec.get_latest_jobids()
    jobs = itviec.get_jobs(jids)
    return render_template("jobs.html", jobs=jobs)


@bp.route("/jobs/<int:j_id>/")
def job(j_id):
    itviec = ItViec()
    j = itviec.get_job(j_id)
    if j is None:
        return render_template("404.html"), 404
    return render_template("job.html", job_id=j_id, j=j)


@bp.route("/hcm")
def hcm():
    return render_template("hcm.html")


@bp.route("/tags")
def tags():
    itviec = ItViec()
    tags_count = itviec.get_tags_count()
    return render_template("tags.html", tags=tags_count)
