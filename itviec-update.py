#!/usr/bin/env python3

import ItViec


def update_itviec_db(robot):
    for section in ItViec._init_ITViecSections():
        print(section)

        for page in section:
            print("main: Page: " + page.url)

            for job in page:
                # ~ print(job.id)

                if robot.db.has_job_id(job.id):
                    continue
                else:
                    robot.add_job(job)


if __name__ == "__main__":

    robot = ItViec.ItViec()
    update_itviec_db(robot)
    robot.close()
