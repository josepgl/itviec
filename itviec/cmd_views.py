import os
from datetime import datetime

import click
from flask import Blueprint
from flask import current_app as app

import itviec.cache
import itviec.stats
import itviec.time
from itviec.db import db
from itviec import source
from itviec.models import Job, Employer
from itviec.composers import compose_employer, install_employer
from itviec.upgrade import download, upgrade


# for debugging
from pprint import pprint

cmd_bp = Blueprint('itviec_cmd', __name__, cli_group=None)


@cmd_bp.cli.command('init')
def _init():
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
def _update():
    '''Download employer and job summary list'''
    source.fetch_all()


@cmd_bp.cli.command('update-stats')
def _update_stats():
    itviec.stats.update_jobs_stats()
    # itviec.stats.to_be_updated()


@cmd_bp.cli.command('download')
def _download():
    download()


@cmd_bp.cli.command('load')
def _load():
    '''Load employers from newest jobs to oldest'''
    for emp_code in source.get_employers_with_jobs():
        print("# Employer: {}".format(emp_code))

        employer = compose_employer(emp_code)

        db.session.add(employer)
        db.session.commit()


@cmd_bp.cli.command('install')
@click.argument('employer_code')
def _install_employer(employer_code):
    # also used internally
    install_employer(employer_code)


@cmd_bp.cli.command('show')
@click.argument('select_type')
@click.argument('code')
def _show(select_type, code):
    if select_type == "job":
        show_job(code)
    elif select_type == "employer" or select_type == "emp":
        show_employer(code)
    else:
        print("Type not supported. Valid types are 'job' or 'employer'.")
        exit(1)


def show_job(code):
    job = Job.query.filter(Job.code == code).first()
    pprint(job.__dict__)


def show_employer(code):
    employer = Employer.query.filter(Employer.code == code).first()
    pprint(employer.__dict__)


@cmd_bp.cli.command('feed')
@click.argument('page_size', default=20)
def _feed(page_size):
    count = 0
    for jt in source.get_timed_job_tags():
        if count % page_size == 0 and count != 0:
            input("Press a key to show the next page.")
        count += 1

        now = datetime.now()
        delta = now.date() - jt["last_post"].date()
        if delta.days == 0:
            print("#{} [{}] {}".format(count, "Today", jt["title"]))
        else:
            print("#{} [{} days ago] {}".format(count, delta.days, jt["title"]))


@cmd_bp.cli.command('histogram')
def _histogram():
    jpd = {}
    for jt in source.get_timed_job_tags():
        post_date = str(jt["last_post"].date())

        jpd[post_date] = jpd[post_date] + 1 if post_date in jpd else 1
        if post_date in jpd:
            jpd[post_date] += 1
        else:
            jpd[post_date] = 1

    itviec.stats.print_histogram(jpd)


@cmd_bp.cli.command('distance-histo')
def _distance_histo():
    days_ago = {0: 0}
    for jt in source.get_timed_job_tags():
        time = itviec.time.get_distance(jt["distance"])
        if "days" in time:
            count = time["days"]
            days_ago[count] = days_ago[count] + 1 if count in days_ago else 1
        else:
            days_ago[0] += 1

    itviec.stats.print_histogram(days_ago, reverse=True)


@cmd_bp.cli.command('upgrade')
def _upgrade():
    download()
    upgrade()
