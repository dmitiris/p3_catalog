from psycopg2 import connect as db_connect


# Database connection settings
var_dbname = None  # Change this according to the database you've created
var_user = None  # Change this according to your user ROLE in Database
var_pass = None  # Change this according to your ROLE's password in Database
# change this if you know what you are doing
var_host = 'localhost'
var_port = 5432
# create some example records in database
var_examples = False


# Create connection to DB
def connect(dbname, host=None, port=None, user=None, password=None):
    connect_string = "dbname={}".format(dbname)
    if host is not None:
        connect_string += " host={}".format(host)
    if port is not None:
        connect_string += " port={}".format(port)
    if user is not None:
        connect_string += " user={}".format(user)
    if password is not None:
        connect_string += " password={}".format(password)
    try:
        # print connect_string
        db = db_connect(connect_string)
        cursor = db.cursor()
        return db, cursor
    except:
        print "Something wrong with database connection"

        
# Create tables for application
def create_tables():
    db, cursor = connect(dbname=var_dbname, user=var_user, password=var_pass, host=var_host, port=var_port)
    # Creating tables
    sql_query = '''
        DROP TABLE IF EXISTS books CASCADE;
        DROP TABLE IF EXISTS categories CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        DROP VIEW IF EXISTS view_books CASCADE;
        CREATE TABLE books (
            id SERIAL PRIMARY KEY,
            title text NOT NULL,
            author text,
            description text,
            category text NOT NULL,
            img_url text,
            pub_year smallint,
            owner integer,
            add_date timestamp DEFAULT now()
        );
        CREATE TABLE categories (
            name text PRIMARY KEY
        );
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name text NOT NULL,
            email text UNIQUE NOT NULL,
            picture text
        );
        ALTER TABLE books ADD CONSTRAINT fk_books_category
        FOREIGN KEY (category) REFERENCES categories (name) MATCH FULL;
        ALTER TABLE books ADD CONSTRAINT fk_books_owner
        FOREIGN KEY (owner) REFERENCES users (id) MATCH FULL;

        CREATE VIEW view_books AS
        SELECT b.id, b.title, b.author, b.description, b.category,
            b.img_url, b.pub_year, b.owner, u.name as owner_name,
            b.add_date, b.add_date::date as only_date
        FROM books as b LEFT JOIN users as u ON u.id = b.owner;
    '''
    cursor.execute(sql_query)
    # SQL Functions
    sql_query = '''
        CREATE OR REPLACE FUNCTION get_user_id(email text)
        RETURNS integer AS $$
            SELECT id FROM users WHERE email = $1
        $$ LANGUAGE SQL;

        CREATE OR REPLACE FUNCTION get_user_info(id integer)
        RETURNS users AS $$
            SELECT id, email, name, picture FROM users WHERE id = $1
        $$ LANGUAGE SQL;

        CREATE OR REPLACE FUNCTION insert_user(email text, name text, picture text)
        RETURNS integer AS $$
            INSERT INTO users (email, name, picture)
            SELECT $1, $2, $3 WHERE get_user_id($1) IS null;
            SELECT get_user_id($1);
        $$ LANGUAGE SQL;

        CREATE OR REPLACE FUNCTION get_last_book_id_by_user(owner integer)
        RETURNS integer AS $$
            SELECT id FROM books WHERE owner = $1
            ORDER BY add_date DESC LIMIT 1;
        $$ LANGUAGE SQL;

        CREATE OR REPLACE FUNCTION insert_book(
            title text,
            author text,
            description text,
            category text,
            img_url text,
            pub_year smallint,
            owner integer
        ) RETURNS integer AS $$
            INSERT INTO books (title, author, description, category, img_url, pub_year, owner)
            SELECT $1, $2, $3, $4, $5, $6, $7;
            SELECT get_last_book_id_by_user($7);
        $$ LANGUAGE SQL;

        CREATE OR REPLACE FUNCTION edit_book(
            id integer,
            owner integer,
            title text,
            author text,
            description text,
            category text,
            img_url text,
            pub_year smallint
        ) RETURNS integer AS $$
            UPDATE books
            SET title=$3, author=$4, description=$5,
                category=$6, img_url=$7, pub_year=$8
            WHERE id=$1;
            SELECT $1;
        $$ LANGUAGE SQL;

        CREATE OR REPLACE FUNCTION delete_book(id integer)
        RETURNS void AS $$
            DELETE FROM books WHERE id=$1;
        $$ LANGUAGE SQL;
    '''
    cursor.execute(sql_query)
    # Populate tables with examples
    if var_examples:
        sql_query = '''
INSERT INTO categories (name) VALUES ('Sci-Fi'), ('Detectives'), ('Novels');
INSERT INTO users (name, email, picture) VALUES
('patrik', 'example@example.com',
'http://lh6.googleusercontent.com/-RpevoCaFZgU/AAAAAAAAAAI/AAAAAAAAAG4/h7ttldFzloA/photo.jpg?sz=300'),
('denis', 'ex@example.com', 'http://www.ztb.ro/images/avatars/1574/peace2-bpfull.jpg'),
('kol', 'example@example.org',
'http://4.bp.blogspot.com/_brk9RNpvmGY/TBF97z1xvBI/AAAAAAAAACs/g0DxsNiIS5s/s1600/68-baby-bad-kitty.png');
INSERT INTO books (title, author, description, category, img_url, pub_year, owner, add_date) VALUES
('Book of Poems', 'Author1', 'Some desc of book1', 'Sci-Fi', null, 2000, 1, now() - interval '1 hour'),
('Nellys Book', 'Author2', 'Some desc of book2', 'Detectives', null, 2004, 1, now()),
('Rock Star', 'Author3', 'Some desc of book3', 'Novels', null, 2001, 2, now()),
('To the stars', 'Author4', 'Some desc of book4', 'Sci-Fi', '#', 2012, 2, now());
'''
        cursor.execute(sql_query)

    db.commit()
    cursor.close()
    db.close()
    return 'Tables created'


# Object to deal with DB queries. Initializing object opens connection.
class Query:
    def __init__(self):
        self.books = None
        self.users = None
        self.categories = None
        self.db, self.cursor = connect(dbname=var_dbname, user=var_user,
                                       password=var_pass, host=var_host, port=var_port)
    
    # Close DB connection
    def close(self):
        self.cursor.close()
        self.db.close()

    # Create list of dicts with data [{column_name:value},{...},...]
    def sql2dict(self, sql_data, col_names):
        result = []
        for x in range(0, len(sql_data)):
            temp = {}
            for y in range(0, len(col_names)):
                temp[col_names[y]] = sql_data[x][y]
            result.append(temp)
        return result

    # Execute select from books table SQL query. Return rows in list of
    # dictionaries. [{column_name:value},{...},...]. Can handle certain
    # limitations on query, like number of lines to return.
    def select_books(self, columns, limits=None, number=None, recent=False):
        """

        :param columns: list of columns from table books
        :param limits: dict of columns and values to check
        :param number: number of rows to return
        :param recent: boolean - orders by date desc
        :return: list of data dicts
        """
        db, cursor = self.db, self.cursor
        cols = ', '.join(columns)
        lims = ''
        limitations = {
            'category': "category='%s'",
            'owner': "owner=%s",
            'id': "id=%s",
            'recent': ' ORDER BY add_date DESC',
            'number': ' LIMIT %s',
        }
        if limits is not None:
            # limitations = {
            #     'category':'category=\'%s\'',
            #     'owner':'owner=\'%s\'',
            #     'id':'id=%s'
            # }
            lims += ' WHERE ' + ' AND '.join([limitations[lim] % limits[lim] for lim in limits])
        if recent:
            lims += limitations['recent']
        if number is not None:
            lims += limitations['number'] % number
        sql_query = '''
            SELECT %s FROM view_books %s;
        ''' % (cols, lims)
        cursor.execute(sql_query)
        result = cursor.fetchall()
        return self.sql2dict(result, columns)

    # Get all categories from DB table.
    def select_categories(self):
        db, cursor = self.db, self.cursor
        sql_query = '''
            SELECT name FROM categories;
        '''
        cursor.execute(sql_query)
        result = cursor.fetchall()
        return self.sql2dict(result, ['name'])
    
    # Check if user is in DB, if not create user.
    # Returns user id
    def create_user(self, user_session):
        db, cursor = self.db, self.cursor
        email = str(user_session['email'])
        name = str(user_session['username'])
        picture = str(user_session['picture'])
        sql_query = '''
            SELECT insert_user(%(email)s::text, %(name)s::text, %(picture)s::text);
        '''
        # print email, name, picture
        # print type(email), type(name), type(picture)
        sql_data = {'email': email, 'name': name, 'picture': picture, }
        cursor.execute(sql_query, sql_data)
        user_id = cursor.fetchone()[0]
        db.commit()
        return user_id
    
    # Get user details from DB
    def get_user_info(self, user_id):
        db, cursor = self.db, self.cursor
        sql_query = '''
            SELECT get_user_info(%s);
        ''' % user_id
        cursor.execute(sql_query)
        row = cursor.fetchone()[0][1:-1].split(',')
        user = {'id': row[0], 'email': row[1], 'name': row[2], 'picture': row[3]}
        return user
        
    # Get user id
    def get_user_id(self, email):
        db, cursor = self.db, self.cursor
        sql_query = '''
            SELECT get_user_id(%s);
        '''
        sql_data = [email, ]
        cursor.execute(sql_query, sql_data)
        user_id = cursor.fetchone()[0]
        return user_id

    # Get all user ids
    def get_user_ids(self):
        db, cursor = self.db, self.cursor
        sql_query = '''
            SELECT id FROM users;
        '''
        cursor.execute(sql_query)
        result = cursor.fetchall()
        users = [user_id[0] for user_id in result]
        return users

    # Insert new entry for book in DB
    def create_book(self, sql_data):
        db, cursor = self.db, self.cursor
        sql_query = '''
            SELECT insert_book(
                %(title)s, %(author)s, %(description)s,
                %(category)s, %(img_url)s, %(pub_year)s,
                %(owner)s);
        '''
        cursor.execute(sql_query, sql_data)
        result = cursor.fetchone()[0]
        db.commit()
        return result

    # Update book entry in DB
    def edit_book(self, sql_data):
        db, cursor = self.db, self.cursor
        sql_query = '''
            SELECT edit_book(
                %(id)s::integer, %(owner)s::integer,
                %(title)s::text, %(author)s::text, %(description)s::text,
                %(category)s::text, %(img_url)s::text, %(pub_year)s::smallint);
        '''
        # print data
        cursor.execute(sql_query, sql_data)
        result = cursor.fetchone()[0]
        db.commit()
        return result

    # Delete book entry
    def delete_book(self, sql_data):
        db, cursor = self.db, self.cursor
        sql_query = '''
            SELECT delete_book(%(id)s);
        '''
        cursor.execute(sql_query, sql_data)
        db.commit()


if __name__ == "__main__":
    print "This will create application tables and delete all",
    print "previously stored information from application database (if there were any)."
    data = raw_input("Are you sure you want to continue? (yes/no): ").upper()
    print data
    if data in ['YES', 'Y']:
        print create_tables()
    else:
        print 'No tables created'
