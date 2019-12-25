#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  storage.py
#
#  Copyright 2019  <josepgl@gmail.com>
#

import sys

import sqlite3


def log(s, *args):
    # ~ print(str(time.time()) + ": storage " + s.format(*args))
    print("storage " + s.format(*args))


class SQLiteStorage:

    name = None
    con = None
    cur = None
    tags = None  # Dict {}

    def __init__(self, name, location):
        self.name = name
        self.location = location

    def __del__(self):
        self.cur = None
        self.close()

    # Open, close ##############################

    def open(self):

        try:
            self.con = sqlite3.connect(self.location)
            # ~ self.con.row_factory = sqlite3.Row
            self.cur = self.con.cursor()
            # ~ self.cur.execute('SELECT SQLITE_VERSION()')
            # ~ return self.cur.fetchone()
            # ~ print( "SQLite version: %s" % data )
        except sqlite3.Error as e:
            print(e)
            sys.exit(1)

    def close(self):
        """Closes the connection"""
        if self.con:
            self.con.close()

    def enable_row(self):
        self.con.row_factory = sqlite3.Row

    # Tables, schema, create ##############################

    def list_tables(self):
        # ~ log("Getting list of tables...")

        self.cur.execute('SELECT name from sqlite_master where type= "table"')
        fetch = self.cur.fetchall()

        result = []
        for line in fetch:
            result.append(line[0])

        return result

    def get_scheme_of_table(self, table):
        # ~ print("{}.get_scheme_of_table()".format(__name__))

        self.cur.execute(
            "select sql from sqlite_master where type = 'table' and name = '{}'".format(
                table
            )
        )
        result = self.cur.fetchone()[0]
        # ~ print( result )

        return result

    def get_schemas(self):
        # ~ print("{}.get_schemas()".format(__name__))

        schemas = {}
        tables = self.list_tables()

        for table in tables:
            schemas[table] = self.get_scheme_of_table(table)

        return schemas

    def create_table(self, table, schema):
        # ~ print("{}.create_table()".format(__name__))
        # ~ print('Creating table {}: {}'.format(table, schema))
        self.cur.execute(schema)

    def create(self, schemas):

        tables_found = self.list_tables()

        for schema_table in schemas:
            if schema_table not in tables_found:
                log("Table '{}' not found. Creating table...", schema_table)
                self.create_table(schema_table, schemas[schema_table])

        # ~ for table in schemas:
        # ~ self.create_table(table, schemas[table])

    # Insert ##############################

    def add_job(self, j):
        """
        'Id INTEGER PRIMARY KEY',
        'LastUpdate TEXT',
        'Title TEXT',
        'Url TEXT',
        'Employer TEXT',
        'EmployerURL TEXT',
        'Salary TEXT',
        'Description TEXT',
        'Address1',
        'Address2',
        'Time TEXT',

        self.id           = param['id']
        self.last_update  = param['last_update']
        self.title        = param['title']
        self.employer_url = param['employer_url']
        self.employer     = param['employer']
        self.url          = param['url']
        self.salary       = param['salary']
        self.address      = param['address']
        self.tags         = param['tags']
        self.desc         = param['desc']
        self.time         = param['time']
        """
        # print("{}.add_job()".format(__name__))

        # template = """INSERT INTO Jobs (
        # Id,
        # LastUpdate,
        # Title,
        # Employer,
        # EmployerUrl,
        # Url,
        # Salary,
        # Description,
        # Address1,
        # Address2,
        # Time
        # )
        # VALUES (
        # "{Id}",
        # "{last_update}",
        # "{title}",
        # "{employer}",
        # "{employer_url}",
        # "{url}",
        # "{salary}",
        # "{desc}",
        # "{address1}",
        # "{address2}",
        # "{time}"
        # );"""

        query = """INSERT INTO Jobs (
                        Id,
                        LastUpdate,
                        Title,
                        Employer,
                        EmployerUrl,
                        Url,
                        Salary,
                        Description,
                        Address1,
                        Address2,
                        Time
                    )
                    VALUES (
                        :id,
                        :last_update,
                        :title,
                        :employer,
                        :employer_url,
                        :url,
                        :salary,
                        :desc,
                        :address1,
                        :address2,
                        :time
                    );"""

        #       # Sometimes not defined
        #       if len(j['address']) > 1:
        #           addr2 = j['address'][1]
        #       else:
        #           addr2 = ''

        # Sometimes not defined
        if len(j["address"]) > 1:
            j["address2"] = j["address"][1]
        else:
            j["address2"] = ""

        j["address1"] = j["address"][0]
        del j["address"]

        # sql_command = template.format(
        # Id           = j['id'],
        # last_update  = j['last_update'],
        # title        = j['title'],
        # employer     = j['employer'],
        # employer_url = j['employer_url'],
        # url          = j['url'],
        # salary       = j['salary'],
        # desc         = j['desc'],
        # address1     = j['address1'],
        # address2     = j['address2'],
        # time         = j['time'],
        # )

        # VERY VERBOSE LOG
        # log("add_job: SQL COMMAND: {}", sql_command)

        try:
            # ~ self.cur.execute(sql_command)
            self.cur.execute(query, j)
            self.con.commit()
        except sqlite3.Error as e:
            log("Exception: add_job: " + str(e))
            return e

    def _insert_tag(self, tag):
        # log("DB inserting tag: {}", tag)
        # print("{}._insert_tag('{}')".format(__name__,tag))
        # print(self.tags)

        # if tag in self.tags:
        # print("W: Tag '{}' already stored.".format(tag))
        # return None

        # print("Current tag: '{}'".format(tag))

        # sql_command = 'insert into Tags ( Tag ) VALUES ("{Tag}");'.format(Tag=tag)
        sql_command = "insert into Tags ( Tag ) VALUES (:Tag)"
        # print("Executing: {}".format(sql_command))

        tag_id = None

        try:
            # ~ self.cur.execute(sql_command)
            self.cur.execute(sql_command, {"Tag": tag})
            self.con.commit()
            tag_id = self.cur.lastrowid

            self.tags[tag] = tag_id
        except sqlite3.Error as e:
            print(e)

        return tag_id

    def link_job_to_tag(self, job_id, tag):

        try:
            # log("link_job_to_tag: Job ID = {}".format(job_id))
            # log("link_job_to_tag: Tag = {}".format(tag))
            # print(self.tags)
            # log("link_job_to_tag: Tag ID = {}".format(self.tags[tag]))

            sql_command = 'insert into JobsTags ( Job, Tag ) VALUES ("{Job}", "{Tag}");'.format(
                Job=job_id, Tag=self.tags[tag]
            )
            self.cur.execute(sql_command)
            self.con.commit()
        except sqlite3.Error as e:
            print(e)

    # Get IDs ################################

    def get_tags(self):

        self.tags = {}  # {Tag: ID}

        # fetch_table returns: [[ID, Tag], ... ]
        temp = self.fetch_table("Tags")
        for i in temp:
            # Store as: {Tag: ID, ... }
            self.tags[i[1]] = i[0]

        return self.tags

    def get_jobs_id(self):
        self.cur.execute("select Id from Jobs")
        result = self.cur.fetchall()

        id_list = [id_line[0] for id_line in result]
        return id_list

    def get_job_tags(self, jid):

        # check if input is integer
        if not type(jid).__name__ == "int":
            raise Exception("Non an integer")

        # "SELECT Tags.Tag FROM JobsTags JOIN Tags ON Tags.Id = JobsTags.Tag WHERE JobsTags.Job = {}"
        self.cur.execute(
            "SELECT Tags.Tag FROM JobsTags JOIN Tags ON Tags.Id = JobsTags.Tag WHERE JobsTags.Job = :id",
            {"id": jid},
        )

        tags = []

        for row in self.cur.fetchall():
            # ~ print(row)
            tags.append(row[0])

        return tags

    # Get IDs ################################

    # TODO: Implement get_job(id)
    # Implemented in ItViec class

    # Stats ####################################

    def has_job_id(self, job_id):

        # check if input is integer
        if not type(job_id).__name__ == "int":
            raise Exception("Non an integer")

        # ~ print('has_job_id(): job_id:: ' + str(job_id) )

        # query db
        # ~ self.cur.execute("select Id from Jobs where Id = '{}'".format(job_id))
        self.cur.execute("select Id from Jobs where Id = :id", {"id": job_id})
        row = self.cur.fetchone()

        # ~ print('has_job_id(): row:: ' + str(row))

        result = False

        if row is not None:
            result = True

        # check query response
        return result

    def has_tag(self, tag):

        # query db
        self.cur.execute("select Tags.Tag from Tags where Tags.Tag = '{}'".format(tag))
        result = self.cur.fetchall()

        length = len(result)

        if length > 1:
            raise Exception("More than one instance of tag {} found".format(tag))

        # check query response
        return length == 1

    # Stats ####################################

    def count_rows_in_table(self, table):
        '''"select count(*) from fixtures"'''
        # print("{}.count_rows_in_table()".format(__name__))

        self.cur.execute("SELECT COUNT(*) from {}".format(table))
        return self.cur.fetchone()[0] - 1

    # DEBUG? ###################################

    def fetch_table(self, table):
        # print("{}.fetch_table()".format(__name__))
        # print("Fetching table: {}".format(table))

        self.cur.execute("select * from {}".format(table))
        result = self.cur.fetchall()

        # for i in result:
        # print( i )

        return result

    def run_query(self, sql_command):
        self.cur.execute(sql_command)
        result = self.cur.fetchall()
        return result

    def run_query_and_commit(self, sql_command):
        self.cur.execute(sql_command)
        self.con.commit()
        result = self.cur.fetchall()
        return result
