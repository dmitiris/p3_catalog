###Package:
1. **static** - directory with static files (currently holds only style.css)
2. **templates** - directory with html templates
3. **catalog.py** - main file
4. **client_secrets.json** - authorization file for Google API
5. **csql.py** - python file to work with PostgreSQL database
6. **readme.md** - deployment instructions and other usefull info

###Requires:
1. PostgreSQL Server
2. Python 2.7
3. Python modules:
	+ Psycopg2 (http://initd.org/psycopg/docs/install.html)
	+ Flask (http://flask.pocoo.org/docs/0.10/installation/#system-wide-installation)
	+ Json 
	+ Requests - built-in python
	+ Uuid - built-in python
	+ Oauth2client
	
To install python packages I recommend to use pip installer (https://pip.pypa.io/en/stable/installing/)

###Installation:
1. [Create database](#db)
2. [Allow md5 connection to PostgreSQL database](#md5)
3. [Set connection string in csql.py](#csql)
4. [Create tables](#tables)
5. [Server](#serv)

####<a name="db"></a>1. Database creation
#####1.1. Connect to PostgreSQL as administrative user
&nbsp;&nbsp;&nbsp;&nbsp;By default it is <b>postgres</b> user. 
&nbsp;&nbsp;&nbsp;&nbsp;<i>e.g. for Linux:</i>
&nbsp;&nbsp;&nbsp;&nbsp;<code>sudo -u postgres psql</code>
#####1.2. Create PostgreSQL role for application
&nbsp;&nbsp;&nbsp;&nbsp;<code>CREATE USER *user_name*;</code>
#####1.3. Set password for created role
&nbsp;&nbsp;&nbsp;&nbsp;<code>ALTER ROLE *user_name* WITH PASSWORD '*password*';</code>
#####1.4. Switch to newly created user
&nbsp;&nbsp;&nbsp;&nbsp;<code>\c *user_name*</code>
#####1.5. Create database
&nbsp;&nbsp;&nbsp;&nbsp;<code>CREATE DATABASE *db_name*;</code>

####<a name="md5"></a>2. Allowing md5 connection to PostgreSQL database
#####2.1. Edit pg_hba.conf
&nbsp;&nbsp;&nbsp;&nbsp;for example for default postgreSQL version 9.3 in Ubuntu<br>
&nbsp;&nbsp;&nbsp;&nbsp;<code>sudo nano /etc/postgresql/9.3/main/pg_hba.conf</code><br>
&nbsp;&nbsp;&nbsp;&nbsp;add line with the context<br>
&nbsp;&nbsp;&nbsp;&nbsp;<code>host *db_name* *user_name* *host_ip* md5</code><br>
#####2.2. Restart PostgreSQL server
&nbsp;&nbsp;&nbsp;&nbsp;<code>sudo service postgresql restart</code>

####<a name="csql"></a>3. Editing csql.py
&nbsp;&nbsp;&nbsp;&nbsp;Find string saying `# Database connection settings` in csql.py, set credentials accordingly.<br>
&nbsp;&nbsp;&nbsp;&nbsp;`var_dbname` - Database name<br>
&nbsp;&nbsp;&nbsp;&nbsp;`var_user` - PostgreSQL user name<br>
&nbsp;&nbsp;&nbsp;&nbsp;`var_pass` - PostgreSQL user password<br>
&nbsp;&nbsp;&nbsp;&nbsp;`var_host` - PostgreSQL server host (by default 'localhost')<br>
&nbsp;&nbsp;&nbsp;&nbsp;`var_port` - PostgreSQL server port (by default '5432')<br>
&nbsp;&nbsp;&nbsp;&nbsp;`var_examples` - if `True` insert few example records in the database<br>

####<a name="tables"></a>4. Creating application database tables
Launch csql.py in command line, for example `python csql.py`. You will be prompted to create tables.<br>
**CAUTION! If you have already tables in database with some information and similar names they will be dropped and overwritten!**

####<a name="serv"></a>5. Running server
You can run the application by simply launching catalog.py file (e.g. `python catalog.py`), or create wsgi file and run it with nginx, apache, or any other server software supporting wsgi.

