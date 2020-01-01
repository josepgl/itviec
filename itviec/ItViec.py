#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ItViec.py
#
#  Copyright 2019  <josepgl@gmail.com>
#
#  ItViec
#  ======
#  Provides an interface to navigate job offers from ItViec
#
#  Subsystems:
#  - Storage (I/O)
#  - Scraper (Input)
#
#  Classes:
#  - ITViec
#  - Section
#  - Page
#  - Job

import json
import requests

import flask
from bs4 import BeautifulSoup, Comment

import config as Config
from .storage import SQLiteStorage

conf = {}
req_http_headers = {}


# Util functions ##########################################
def first_line(s):
    return str(s).splitlines()[0]


def class_name(i):
    return i.__class__.__name__


def log(s, *args):
    print("ItViec " + s.format(*args))


def log_msg(s, *args):
    s = "{}:{}() " + s
    print(s.format(*args))


def msg(s):
    if conf['DEBUG']:
        print(s)


def fetch_url(url):
    # Fetch page
    # print('Fetching url {}'.format(url)) # DEBUG

    response = requests.get(url, headers=req_http_headers)

    # Check response code
    if response.status_code != 200:
        raise StopIteration(
            "Error {0} fetching url: {1}".format(response.status_code, url)
        )

    return response


def get_config():
    config = flask.Config(Config.BASE_DIR)
    Config.set_app_config(config)
    # print(config)

    return config


conf = get_config()


def collect_http_headers(conf):
    for k, v in conf.get_namespace('HTTP_HEADER_').items():
        req_http_headers[k.replace("_", "-").capitalize()] = v
    return req_http_headers


req_http_headers = collect_http_headers(conf)


# Section #################################################
class ITViecSection:
    def __init__(self, name, ID, url):
        self.name = name
        self.ID = ID
        self.url = url

    def __repr__(self):
        return "Section ID='{}' Name='{}' URL='{}'"\
            .format(self.ID, self.name, self.url)

    def __iter__(self):
        return ItViecSectionPageIterator(self.url)


def _init_ITViecSections():

    url = conf["URL"]

    CITIES = {
        "ho-chi-minh-hcm": "Ho Chi Minh",
        "ha-noi": "Ha Noi",
        "da-nang": "Da Nang",
        "others": "Others",
    }

    secs = []

    for ID in CITIES:
        name = CITIES[ID]
        sec_url = "{}/{}".format(url, ID)  # construct url

        s = ITViecSection(name, ID, sec_url)
        secs.append(s)

    return secs


class ItViecSectionPageIterator:
    def __init__(self, url):

        self.url = url

    def __next__(self):

        # Check if there is a url
        if self.url is None or self.url is "":
            raise StopIteration("Error: No URL for current iteration")

        # Fetch page
        response = fetch_url(self.url)
        resp_json = response.json()

        # Key:  suggestion
        # Key:  show_more_html
        # Key:  jobs_html

        # 1.- Next URL
        next_url_block = resp_json["show_more_html"]
        soup = BeautifulSoup(next_url_block, "html.parser")

        # Define the local variable
        next_url = None
        prev_url = None

        # Get next page url if exists
        a = soup.find("a", href=True, rel="next")
        # print( type(a).__name__ )
        next_url = a["href"] if type(a).__name__ is "Tag" else ""
        # print("Next URL: " + next_url)

        # Get previous page url if exists
        for a in soup.find_all("a", href=True, rel="prev"):
            prev_url = a["href"]
            break

        # Build page
        page = Page(self.url, resp_json["jobs_html"], prev_url, next_url)
        # print("Page in It: " + str(page))

        self.url = next_url

        # Return html page
        return page


# Page ####################################################
class Page:
    def __init__(self, url, content, prev_p, next_p):
        self.url = url
        self.content = content
        self.prev_p = prev_p
        self.next_p = next_p

    def __iter__(self):
        return JobIteratorInPage(self.content)

    def __repr__(self):
        return self.url


class JobIteratorInPage:
    def __init__(self, content):

        if content is None:
            raise Exception("Page is empty")

        self.soup = BeautifulSoup(content, "html.parser")
        # print( "Soup class: " + str(type(self.soup)) )

        self.div = self.soup.div
        # print( "div tag class: " + str(type(self.div)) )

        self.next_block = self.div.find_next(class_="job")
        # print( "self.next_block class: " + str(type(self.next_block)) )
        # print("Next block: " + str(self.next_block).splitlines()[0])

    def __next__(self):

        # Check if there is a block
        if self.next_block is None:
            raise StopIteration("No more blocks in page")

        job = parse_job(self.next_block)

        self.next_block = self.next_block.find_next(class_="job")
        # ~ print("Next block: "+str(self.next_block).splitlines()[0])

        return job


# Job #####################################################
class Job:
    def __init__(self, param):
        self.id = int(param["id"])
        self.last_update = param["last_update"]
        self.title = param["title"]
        self.employer_url = param["employer_url"]
        self.employer = param["employer"]
        self.url = param["url"]
        self.salary = param["salary"]
        self.address = param["address"]
        self.tags = param["tags"]
        self.desc = param["desc"]
        self.time = param["time"]

    def __repr__(self):
        # return str(self.__dict__)

        # DEBUG #
        return "\n".join(
            [
                'ID:           "{}"'.format(self.id),
                'Last update:  "{}"'.format(self.last_update),
                'Title:        "{}"'.format(self.title),
                'Employer URL: "{}"'.format(self.employer_url),
                'Employer:     "{}"'.format(self.employer),
                'URL:          "{}"'.format(self.url),
                'Salary:       "{}"'.format(self.salary),
                'Address:      "{}"'.format(self.address),
                'Tags:         "{}"'.format(self.tags),
                'Description:  "{}"'.format(self.desc),
                'Time:         "{}"'.format(self.time),
                "",
            ]
        )
        # DEBUG #

    def get_url(self):
        return conf['BASE_URL'] + self.url

    def get_employer_url(self):
        return conf['BASE_URL'] + self.employer_url

    def has_full_desc(self):
        defined = self.hasAttribute("f_desc")
        initialized = len(self.f_desc) > 0

        return defined and initialized

    def get_full_desc(self):

        response = fetch_url(self.get_url(), None)

        bs = BeautifulSoup(response.text, "html.parser")
        div = bs.div

        j_detail = div.find_next(class_="job-detail")
        # print("Job details tag: " + str(j_detail).splitlines()[0])

        f_desc = {"reasons": "", "desc": "", "skills": "", "why": ""}

        for child in j_detail.children:

            if child.__class__.__name__ != "Tag":
                continue

            child_class = child["class"][0]

            if child_class == "job_reason_to_join_us":
                print("Reasons: " + str(child).splitlines()[0])
                f_desc["reasons"] = str(child)
            if child_class == "job_description":
                print("Description: " + str(child).splitlines()[0])
                f_desc["desc"] = str(child)
            if child_class == "skills_experience":
                print("Skills: " + str(child).splitlines()[0])
                f_desc["skills"] = str(child)
            if child_class == "love_working_here":
                print("Why: " + str(child).splitlines()[0])
                f_desc["why"] = str(child)

        # print(f_desc)

        return f_desc


def parse_job(job_block):
    """
    Extract job details from html and build a dictionary to create a Job
    instance

    Input: html list source
    Output: Job object
    """

    # soup = BeautifulSoup( job_block, "html.parser" )

    j_bl = job_block

    job = {}

    job["id"] = j_bl["id"][4:]
    job["last_update"] = (
        j_bl.find_next(string=lambda text: isinstance(text, Comment))
        .extract()
        .split('"')[1]
    )
    job["title"] = j_bl.find_all("a")[1].text.strip()
    job["employer_url"] = j_bl.find_all("a", {"target": "_blank"})[0]["href"]
    job["employer"] = j_bl.find_all("a", {"target": "_blank"})[0]["href"]\
        .split("/")[-1]
    job["url"] = j_bl.find_all("h2", class_="title")[0].a["href"]
    job["salary"] = j_bl.find_all("span", class_="salary-text")[0].text.strip()
    job["address"] = (
        j_bl.find_all("div", class_="address")[0].text.strip().split("\n\n\n")
    )
    job["tags"] = (
        j_bl.find_all("div", class_="tag-list")[0].text.strip().split("\n\n\n")
    )
    job["desc"] = j_bl.find_all("div", class_="description")[0].text.strip()
    job["time"] = j_bl.find_all("span", class_="distance-time")[0].text.strip()

    # datetime_format = '%Y-%m-%d %H:%M:%S %z'
    # time_obj = datetime.strptime(job['last_update'], datetime_format)
    # time_obj = datetime.fromisoformat(job['last_update'])

    # print("last_update: " + job['last_update'])
    # print(type(time_obj))
    # print(time_obj)
    # print(time_obj.strftime(datetime_format))
    # print(time_obj.isoformat())

    j = Job(job)
    # print(j) # DEBUG

    # exit()

    return j


# Jobs ####################################################
class Jobs:
    def __init__(self, db):
        self.db = db

    def get_ids(self):
        query = "SELECT Id FROM Jobs"
        self.db.cur.execute(query)

        jids = [row[0] for row in self.db.cur.fetchall()]
        j = jids.pop()  # remove header
        print(j)

        return jids

    def count(self):
        return self.db.count_rows_in_table("Jobs")
        # return len(self.get_ids())


# Employers ################################################
class Employers:
    def __init__(self):
        pass  # TODO

    @classmethod
    def request_all_names(self):
        response = fetch_url(Config.EMPLOYERS_JSON_URL)

        return json.loads(response.text)


# #########################################################
# ItViec ##################################################
# #########################################################
class ItViec:
    """
    - On __init__:
        - Read configuration
            - Name
            - Url
            - Pages
            - Headers
        - Connects to database and initilizes it
            - Connect
            - Check tables exist

    - Scraper
        -Iterators:
            - URL iterator
            - HTML page iterator
            - Items iterator (full abstraction)

    - Stores job offers in DB
        - Job => DB
            - Store one
            - Store batch

    - DB can be updated
    - Implements basic queries
    """

    feed = None
    db = None
    tags = None  # dict( {Tag: ID} )
    jobs_id = None  # list[]

    SCHEMAS = {
        "Jobs": """CREATE TABLE Jobs(
            Id INT PRIMARY KEY,
            LastUpdate TEXT,
            Title TEXT,
            Url TEXT,
            Employer TEXT,
            EmployerURL TEXT,
            Salary TEXT,
            Description TEXT,
            Address1 TEXT,
            Address2 TEXT,
            Time  TEXT)""",
        "Tags": """CREATE TABLE Tags(
            Id INTEGER PRIMARY KEY,
            Tag TEXT UNIQUE)""",
        "JobsTags": """CREATE TABLE JobsTags(
            Id INTEGER PRIMARY KEY,
            Tag INTEGER,
            Job INTEGER,
            UNIQUE(Tag, Job))""",
    }

    CITIES = {
        "ho-chi-minh-hcm": "Ho Chi Minh",
        "ha-noi": "Ha Noi",
        "da-nang": "Da Nang",
        "others": "Others",
    }

    def __init__(self):
        """Constructor:

        - Calls super class constructor
            - Loads configuration
                - URL
                - Pages
                - HTTP Headers
        - Database init
            - Opens DB
            - Creates tables if required
            - Shows count of Jobs and Tags on DB
            -

        """

        self.sections = _init_ITViecSections()

        self.db = SQLiteStorage(__name__, conf['DATABASE'])
        self.db.open()
        self.db.create(self.SCHEMAS)

        n_j = self.db.count_rows_in_table("Jobs")
        log_msg("Jobs in database: {}", __name__, "init", n_j)
        n_t = self.db.count_rows_in_table("Tags")
        log_msg("Tags in database: {}", __name__, "init", n_t)

        # print(self.db.get_schemas())
        self.tags = self.db.get_tags()  # required
        self.jobs_id = self.db.get_jobs_id()

        self.jobs = Jobs(self.db)

    def __del__(self):
        del self.db

    def close(self):
        self.db.close()

    # DEBUG #########################################

    def GET_TABLE(self, table):
        return self.db.fetch_table(table)

    def run_query(self, sql_command):
        return self.db.run_query(sql_command)

    # Insert #########################################

    def add_job(self, job):

        log("add_job: Adding job ID {} to database", job.id)
        # log(str(job))

        has_job = self.db.has_job_id(job.id)
        # print("add_job(): has_job: " + str(has_job))

        if has_job:
            db_job = self.get_job(job.id)
            print("Found job in database: " + db_job)
            print("New job: " + job)

            return

        # Store Job
        self.db.add_job(job.__dict__)

        # Tags
        for tag in job.tags:
            # Create tag if necessary
            self.add_tag(tag)

            # Link tag to job
            self.db.link_job_to_tag(job.id, tag)

    #       try:
    #           self.db.add_job( job.__dict__ )
    #
    #           # Tags
    #           for tag in job.tags:
    #               # Create tag if necessary
    #               self.add_tag( tag )
    #
    #               # Link tag to job
    #               self.db.link_job_to_tag(job.id, tag)
    #
    #           # Update index with new job_id
    #           self.jobs_id.append( job.id )
    #
    #       except sqlite3.Error as e:
    #
    #           log( 'add_job: ' + str(e) )
    #           return e

    def add_tag(self, tag):

        if self.db.has_tag(tag):
            # log("Tag '{}' already exists", tag)
            return None

        log("Adding tag '{}'", tag)

        # Update database
        tag_id = self.db._insert_tag(tag)

        return tag_id

    # Get Job #########################################

    def get_job(self, jID):
        # get job object from db
        # job constructor from DB???
        # print("get_job({})".format(jID))
        sql_query = "select * from Jobs where Jobs.Id = {}".format(jID)
        # print("get_job(): SQL query:: ", sql_query)
        # job_row = self.db.run_query('select * from Jobs where Jobs.Id = {}'.format(jID))[0]
        q_result = self.db.run_query(sql_query)
        # print("get_job(): SQL Query result:: ", q_result)
        job_row = q_result[0]

        # get tags for job ID
        tags = self.db.run_query(
            """select Tags.Tag from Tags
        JOIN JobsTags where JobsTags.Tag = Tags.Id AND JobsTags.Job = {}""".format(
                jID
            )
        )
        # [[A,],[B,],[C,], ] => [A,B,C,]
        tags = [t_row[0] for t_row in tags]

        # instatiate job
        job_dict = {}

        job_fields_list = (
            "id",
            "last_update",
            "title",
            "url",
            "employer",
            "employer_url",
            "salary",
            "desc",
            "address1",
            "address2",
            # 'description',
            "time",
        )

        for i in range(0, len(job_fields_list)):
            job_dict[job_fields_list[i]] = job_row[i]

        job_dict["address"] = [job_dict["address1"], job_dict["address2"]]
        del job_dict["address1"]
        del job_dict["address2"]
        job_dict["tags"] = self.db.get_job_tags(jID)

        # print(job_dict)

        job = Job(job_dict)

        return job

    # Stats #########################################
    def get_tags_count(self):
        tags_cnt = []

        query = """SELECT Tags.Tag, COUNT(*)
        FROM Tags
        JOIN JobsTags ON Tags.Id = JobsTags.Tag
        GROUP BY Tags.Tag
        ORDER BY COUNT(*) DESC;"""

        self.db.cur.execute(query)

        tags_cnt = self.db.cur.fetchall()

        return tags_cnt

    def get_latest_jobids(self):
        jids = []

        query = "SELECT Id FROM Jobs ORDER by Id DESC LIMIT 51"

        self.db.cur.execute(query)

        for row in self.db.cur.fetchall():
            jids.append(row[0])

        jids.pop(0)

        return jids

    def get_jobs(self, jids):
        jobs = []

        for jid in jids:
            jobs.append(self.get_job(jid))

        return jobs

    def update_db(self):

        for section in _init_ITViecSections():
            print(section)

            for page in section:

                for job in page:

                    if self.db.has_job_id(job.id):
                        continue
                    else:
                        self.add_job(job)
