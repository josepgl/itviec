DROP TABLE IF EXISTS employer;
DROP TABLE IF EXISTS job;
DROP TABLE IF EXISTS tag;
DROP TABLE IF EXISTS employer_job;
DROP TABLE IF EXISTS employer_tag;
DROP TABLE IF EXISTS job_tag;

CREATE TABLE employer(
	id INTEGER PRIMARY KEY,
	code TEXT,
	name TEXT,
	url TEXT,
	logo TEXT,
	location TEXT,
	industry TEXT,
	employees TEXT,
	coutry TEXT,
	working_days TEXT,
	overtime TEXT,
	website TEXT,

	description TEXT,
);
# Linked to jobs

CREATE TABLE job(
	id INT PRIMARY KEY,
	last_update TEXT,
	title TEXT,
	url TEXT,
	employer TEXT,
	salary TEXT,
	description TEXT,
	address_1 TEXT,
	address_2 TEXT,

	FOREIGN KEY (employer) REFERENCES employer (code)
);

CREATE TABLE tag(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	tag TEXT UNIQUE
);

CREATE TABLE employer_job(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	employer TEXT,
	job TEXT UNIQUE,
	UNIQUE(employer, job)
);

CREATE TABLE job_tag(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	tag_id INTEGER,
	job_id INTEGER,
	UNIQUE(tag_id, job_id)
);

CREATE TABLE employer_tag(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	tag INTEGER,
	employer INTEGER,
	UNIQUE(tag_id, employer_id)
);


# Example ###############################################

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

