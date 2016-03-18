Application requires working SQL database. To create one:
1. Create database in PostgreSQL. Make sure 

Package:
1. static - directory with static files (currently holds only style.css)
2. templates - directory with html templates
3. catalog.py - main file
4. client_secrets.json - authorization file for Google API
5. csql.py - python file to work with PostgreSQL database
6. readme.md - deployment instructions and other usefull info

Requires:
1. PostgreSQL Server
2. Python 2.7
3. Python modules:
	3.1. Psycopg2 (http://initd.org/psycopg/docs/install.html)
	3.2. Flask (http://flask.pocoo.org/docs/0.10/installation/#system-wide-installation)
	3.3. Json 
	3.4. Requests - built-in python
	3.5. Uuid - built-in python
	3.6. Oauth2client
	
To install python packages I recommend to use pip installer (https://pip.pypa.io/en/stable/installing/)

Installation:
1. Create database. 
2. Allow md5 connection to PostgreSQL database (instructions available only for ubuntu)
3. Set connection string in csql.py
4. Create tables.

1. Database creation
1.1. Connect to PostgreSQL as administrative user.
By default it is 'postgres' user. 
(e.g. for Linux: sudo -u postgres psql)
1.2. Create PostgreSQL role for application.
(e.g. CREATE USER user_name;)
1.3. Set password for created role.
(e.g. ALTER ROLE user_name WITH PASSWORD 'password';)
1.4. Switch to newly created user.
(e.g. \c user_name)
1.5. Create database.
CREATE DATABASE db_name;

2. Allowing md5 connection to PostgreSQL database.
(Instructions available only for ubuntu)
2.1. Edit pg_hba.conf
for example for default postgreSQL version 9.3
nano /etc/postgresql/9.3/main/pg_hba.conf
add line with the context
host 
2.2. Restart PostgreSQL server
sudo service postgresql restart

3. Editing csql.py
Find string saying "# Database connection settings" in csql.py, set credentials accordingly.
var_dbname - Database name
var_user - PostgreSQL user name
var_pass - PostgreSQL user password
var_host - PostgreSQL server host (by default 'localhost')
var_port - PostgreSQL server port (by default '5432')
var_examples - if True insert few example records in database

4. Creating application database tables.
Launch csql.py in command line, for example "python csql.py". You will be prompted to create tables.
CAUTION! If you have already tables in database with some information and similar names they will be dropped and overwritten!

5. Running server.
You can run the application by simply launching catalog.py file (e.g. python catalog.py), or create mod_wsgi file and run it with nginx, apache, or any other server software supporting wsgi.
