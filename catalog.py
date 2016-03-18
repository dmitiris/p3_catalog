from flask import Flask, render_template, make_response, request, flash, redirect, abort, url_for, jsonify
from flask import session as user_session
from uuid import uuid4
from csql import Query, var_dbname
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
app = Flask(__name__)

# Client id for Google API
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog"


# region Functions

# Checks if user is logged. Uses user_id in session cookie to
# identify user. Returns boolean and user info dictionary.
def is_authenticated(u_session, users):
    """
    Checks if user is logged
    :param u_session: dict
    :param users: list of ids
    :return: boolean, user dict
    """
    try:
        if u_session['user_id'] in users:
            user = {
                'id': u_session['user_id'],
                'name': u_session['username'],
                'email': u_session['email'],
                'picture': u_session['picture']
            }
            return True, user
    except KeyError:
        return False, None


# State is required by Google Auth API. This function checks if state
# is in session cookie.
def get_state():
    """
    If exist gets state from cookie, else generates state and writes it to cookie
    :return: returns state variable
    """
    try:
        state = user_session['state']
    except KeyError:
        state = uuid4()
        user_session['state'] = str(state)
    return state


# Checks if key is in dictionary and returns either key or value
# or some custom value.
def form_data(form, key, value):
    """
    Checks if key is in the form and returns its value
    :param form: request.form object
    :param key: Key name
    :param value: Value in case there is no key
    :return:
    """
    try:
        return form[key]
    except KeyError:
        return value
# endregion functions


# region Google API connect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != user_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = user_session.get('credentials')
    stored_gplus_id = user_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    user_session['access_token'] = credentials.access_token
    user_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    # Write user data in session cookie
    user_session['username'] = data['name']
    user_session['picture'] = data['picture']
    user_session['email'] = data['email']

    query = Query()
    user_id = query.create_user(user_session)
    query.close()
    user_session['user_id'] = user_id
    output = ''.join([
        '<h1>Welcome, ', user_session['username'], '!</h1>',
        '<img'
            ' src=',
            '"',
                user_session['picture'],
            '"',
            ' style=',
            '"',
                'width: 300px; ', 'height: 300px; ',
                'border-radius: 150px; ', '-webkit-border-radius: 150px; ',
                '-moz-border-radius: 150px;',
            '"',
        '>'
    ])
    flash("you are now logged in as %s" % user_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = user_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: ' 
    print user_session['username']
    if access_token is None:
        print 'Access Token is None'
        msg = {'msg': 'Current user not connected.'}
        return render_template('logout.html', msg=msg)
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % user_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del user_session['access_token']
        del user_session['gplus_id']
        del user_session['username']
        del user_session['email']
        del user_session['picture']
        del user_session['user_id']
        del user_session['state']
        msg = {'msg': 'Successfully disconnected.'}
        return render_template('logout.html', msg=msg)
    else:
        msg = {'msg': 'Failed to revoke token for given user.'}
        return render_template('logout.html', msg=msg)
# endregion


# Main Page
@app.route('/')
@app.route('/catalog')
def showCatalogPage():
    state = get_state()
    query = Query()
    categories = query.select_categories()
    users = query.get_user_ids()
    auth, user = is_authenticated(user_session, users)
    recent = query.select_books(
        columns=['id', 'title', 'category'],
        recent=True,
        number=5)
    query.close()
    return render_template('showcatalog.html', categories=categories, recent=recent, auth=auth, user=user, STATE=state)


# Page with catalog items
@app.route('/catalog/<category>/items')
def showCategoryPage(category):
    state = get_state()
    query = Query()
    users = query.get_user_ids()
    auth, user = is_authenticated(user_session, users)
    categories = query.select_categories()
    books = query.select_books(
        columns=['id', 'title', 'category', 'owner'],
        limits={'category': category}
    )
    query.close()
    return render_template('showcategory.html', categories=categories, books=books, auth=auth, user=user, STATE=state)


# Page with details of an item
@app.route('/catalog/<category>/<int:item_id>', methods=['GET', 'POST'])
def showItemPage(category, item_id):
    state = get_state()
    query = Query()
    users = query.get_user_ids()
    auth, user = is_authenticated(user_session, users)
    book = query.select_books(
        columns=['id', 'title', 'category', 'pub_year', 'author', 'description', 'owner', 'owner_name', 'only_date'],
        limits={'id': item_id},
        number=1
    )[0]
    query.close()
    return render_template('showitem.html', auth=auth, user=user, book=book, category=category, STATE=state)


# Add item page (available only for auth users)
@app.route('/catalog/add', methods=['GET', 'POST'])
def addItemPage():
    state = get_state()
    query = Query()
    users = query.get_user_ids()
    auth, user = is_authenticated(user_session, users)
    # If user is not authenticated, then auth is False and 
    # html-template has rule that if false show message that access is restricted
    if auth is False:
        categories = []
        return render_template('additem.html', auth=auth, user=user, categories=categories, STATE=state)
    # in Post request user sends information on book and new book is created.
    if request.method == 'POST' and auth is True:
        new_book = {
            'title': form_data(request.form, 'title', None),
            'author': form_data(request.form, 'author', None),
            'pub_year': form_data(request.form, 'pub_year', None),
            'description': form_data(request.form, 'description', None),
            'category': form_data(request.form, 'category', None),
            'owner': user_session['user_id'],
            'img_url': None,  # TODO: in case file upload implemented
        }
        book_id = query.create_book(new_book)
        return redirect(url_for('showItemPage', category=new_book['category'], item_id=book_id))
    categories = query.select_categories()
    query.close()
    return render_template('additem.html', auth=auth, user=user, categories=categories, STATE=state)


# Page to edit item details (available only for auth users)
@app.route('/catalog/<int:item_id>/edit', methods=['GET', 'POST'])
def editItemPage(item_id):
    state = get_state()
    query = Query()
    users = query.get_user_ids()
    auth, user = is_authenticated(user_session, users)
    # This page is only for registered users
    if auth is False:
        query.close()
        return render_template('edititem.html', auth=auth, valid=False)
    # Request book data from DB including ownership
    book_data = query.select_books(
        columns=['id', 'owner', 'title', 'author', 'pub_year', 'description', 'category'],
        limits={'id': item_id},
        number=1
    )[0]
    # Checks if user is the owner of the book
    if book_data['owner'] != user['id']:
        query.close()
        return render_template('edititem.html', auth=auth, user=user, valid=False, STATE=state)
    # Handling POST request
    if request.method == 'POST':
        edit_book = {
            'id': item_id,
            'owner': book_data['owner'],
            'title': form_data(request.form, 'title', None),
            'author': form_data(request.form, 'author', None),
            'pub_year': form_data(request.form, 'pub_year', None),
            'description': form_data(request.form, 'description', None),
            'category': form_data(request.form, 'category', None),
            'img_url': None,  # TODO: in case file upload implemented
        }
        try:
            edit_book['pub_year'] = int(edit_book['pub_year'])
        except:
            edit_book['pub_year'] = None
        book_id = query.edit_book(edit_book)
        query.close()
        return redirect(url_for('showItemPage', category=edit_book['category'], item_id=book_id, STATE=state))
    categories = query.select_categories()
    query.close()
    return render_template('edititem.html', auth=auth, user=user,
                           valid=True, book=book_data, categories=categories, STATE=state)


# Page to delete items
@app.route('/catalog/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItemPage(item_id):
    state = get_state()
    query = Query()
    users = query.get_user_ids()
    auth, user = is_authenticated(user_session, users)
    # This page is only for registered users
    if auth is False:
        query.close()
        return render_template('deleteitem.html', auth=auth, valid=False, STATE=state)
    book_data = query.select_books(columns=['id', 'owner', 'category'], limits={'id': item_id}, number=1)[0]
    # Checks if user is the owner of the book
    if book_data['owner'] != user['id']:
        query.close()
        return render_template('deleteitem.html', auth=auth, user=user, valid=False, STATE=state)
    # Handling POST request
    if request.method == 'POST':
        query.delete_book(book_data)
        query.close()
        return redirect(url_for('showCategoryPage', category=book_data['category'], STATE=state))
    query.close()
    return render_template('deleteitem.html', auth=auth, user=user, valid=True, book=book_data, STATE=state)


# JSON out
@app.route('/catalog.json')
def showJSON():
    query = Query()
    categories = query.select_categories()
    books = query.select_books(
        columns=[
            'id', 'title', 'category', 'pub_year', 'author', 'description',
            'owner', 'owner_name', 'only_date', 'add_date'
        ],
    )
    query.close()
    books_by_cat = {}
    for book in books:
        book['only_date'] = str(book['only_date'])
        book['add_date'] = str(book['add_date'])
        try:
            books_by_cat[book['category']].append(book)
        except KeyError:
            books_by_cat[book['category']] = [book]
    for cat in categories:
        cat['books'] = books_by_cat[cat['name']]
    result = {'categories': categories}
    return jsonify(result)


if __name__ == '__main__':
    if var_dbname is None:
        print 'Please setup database connection in csql.py'
    else:
        app.debug = True
        app.secret_key = str(uuid4())
        app.run(host='0.0.0.0', port=5000)
