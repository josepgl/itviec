from app import app
from flask import render_template

from ItViec import ItViec


@app.route("/")
def index():
    itviec = ItViec()
    jids = itviec.get_latest_jobids()
    jobs = itviec.get_jobs(jids)
    return render_template("front_page.html", jobs=jobs)


@app.route("/jobs")
def jobs():
    return render_template("jobs.html")


@app.route("/jobs/<int:j_id>/")
def job(j_id):
    itviec = ItViec()
    j = itviec.get_job(j_id)
    if j is None:
        return render_template("404.html"), 404
    return render_template("job.html", job_id=j_id, j=j)


@app.route("/hcm")
def hcm():
    return render_template("hcm.html")


@app.route("/tags")
def tags():
    itviec = ItViec()
    tags_count = itviec.get_tags_count()
    return render_template("tags.html", tags=tags_count)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/members/<string:m_name>/")
def getMember(m_name):
    # return name #</string:name>
    return render_template("front_page.html", name=m_name)


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template("404.html"), 404


@app.route("/config")
def getConfig():
    return app.config
