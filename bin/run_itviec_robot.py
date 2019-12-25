#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.curdir))

import ItViec

# ############################################

"""
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
j = ItViec.Job(
    {
        "id": "12345",
        "last_update": "Yesterday",
        "title": "Monkey",
        "employer": "Company Inc.",
        "employer_url": "/companies/company",
        "url": "ci.com",
        "salary": "Something",
        "address": ["Address1", "Address2"],
        "tags": ["Tag1", "Tag2", "Tag3"],
        "desc": "Job offer short description.",
        "time": "1 hour ago",
    }
)


robot = ItViec.ItViec()


# Single job example ###########################
# robot.add_job(j)
# #################################################

# Update example ###########################
# robot.update_db()
# #################################################

# for section_url in robot.feed_section_iterator():
# print("Section: " + section_url)
# for section_page in ItViec.ItViecFeedUrlIterator(section_url):
# print("Page: " + section_page)


# Get list of Job objects from feed ############
# def get_job_list():
# item_list = []

# for list_page in robot.feed_page_iterator():
# for job_block in robot.get_job_blocks_from_page(page):
# item_list.append( job_block )

# return item_list

# item_list = get_job_list()
# print(len(item_list))
# import json
# print( json.dumps(item_list[0]) )


# #####################################
# print("DUMPING TABLES:")
#
# for table in ['Jobs','Tags','JobsTags']:
#   print("Table {}:".format(table))
#   robot.GET_TABLE(table)
#
# print("END OF DUMP")
# #####################################


# job = robot.get_job(60787)
# print(j)
# print(j.get_employer_url())

# company = ItViec.Company.parse_from_url( j.get_employer_url() )


# print(job.get_full_desc())
# job.get_full_desc()

# for row in job:
# print(row)
# keys = row.keys()
# print( "Keys: " + ', '.join(keys) )

# for key in keys:
# print( "{}: {}".format(key, row[key]) )
# print()


# exit()


# Job Ids and titles
# query = "SELECT Id FROM Jobs"
# query = "SELECT Id, Title FROM Jobs"
# query = "SELECT Id, Title FROM Jobs ORDER by Id DESC"
# query = "SELECT Id FROM Jobs ORDER by Id DESC LIMIT 20"
# Job Ids and salary
# query = "SELECT Id, Salary FROM Jobs"
# Tags
# query = "SELECT Tag FROM Tags"
# Address
# query = "SELECT Address1, Address2 FROM Jobs"

# query = '''SELECT Tags.Tag, COUNT(*)
# FROM Tags
# JOIN JobsTags ON Tags.Id = JobsTags.Tag
# GROUP BY Tags.Tag
# ORDER BY COUNT(*) DESC;'''

# query = "SELECT Jobs.Id, Jobs.Title, JobsTags.Tag FROM Jobs JOIN JobsTags ON Jobs.Id = JobsTags.Job WHERE Jobs.Id = 60600 "

# query = """SELECT Jobs.Id, Jobs.Title, Tags.Tag FROM Jobs
# JOIN JobsTags ON Jobs.Id = JobsTags.Job
# JOIN Tags ON Tags.Id = JobsTags.Tag"""

# tags sorted by frequency
# query = """SELECT Tags.Tag, COUNT(*) FROM JobsTags
# JOIN Tags ON Tags.Id = JobsTags.Tag
# GROUP BY Tags.Tag
# ORDER BY 2 DESC"""

# query = "SELECT JobsTags.Job, Tags.Tag FROM JobsTags JOIN Tags ON Tags.Id = JobsTags.Tag"
# query = "SELECT Tags.Tag FROM JobsTags JOIN Tags ON Tags.Id = JobsTags.Tag WHERE JobsTags.Job = 60600"

# query = "SELECT Jobs.Id FROM Jobs WHERE Jobs.Id = 60600 "


def print_query(query):
    print()
    print(query)
    print()

    for item in robot.run_query(query):
        print(item)


# query = "SELECT Id, Salary FROM Jobs"
# print_query(query)

# query = "UPDATE Jobs SET Salary = replace( Salary, 'https://itviec.com', '' ) WHERE Salary LIKE 'https://itviec.com%';"
# print(robot.run_query(query))

query = "SELECT Id, Salary FROM Jobs"
print_query(query)

# Performance test ###
# for _ in range(100000):
# robot.run_query(query)
# 54926 in robot.jobs_id


# robot.db.has_job_id(54926)
# print( robot.jobs.count() )


# update_itviec_db(robot)
# robot.update_db()

robot.close()
