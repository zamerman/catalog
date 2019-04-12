#!/usr/bin/env python
# PROGRAMMER: Zachary Amerman
# DATE CREATED: April 1, 2019
# REVISED DATE: April 12, 2019
# PURPOSE: When called serves as a server on localhost port 8000. The site is
#          a catalog of sports items organised into various categories. Items
#          and categories are stored in a sqlite database. The site gives the
#          latest added items, the items in a particular category, and a
#          description of a particular item. In addition, the site can be
#          logged into using google. Logging in enables items to be added, and
#          if if you are the user who added an item you are able to edit or
#          delete it.

# import webpage framework methods and classes from flask library
from flask import Flask, render_template, url_for
from flask import request, redirect, flash, jsonify

# import login and state classes and methods
from flask import session as login_session
import random
import string

# import oauth handlings classes and methods
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# import datetime methods and class
from datetime import datetime

# import sql methods and classes from sqlalchemy library
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from catalog_setup import Base, Category, Item, User

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# setup database handlers
engine = create_engine('sqlite:///catalog.db',
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# app login page
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html',
                           STATE=state,
                           loginsession=login_session)

# gconnect post page
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Check that the state tokens match
    if request.args.get('state') != login_session['state']:
        flash('Invalid state token')
        return redirect(url_for('catalog'))

    # Obtain the authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        flash('Failed to upgrade the authorization code')
        return redirect(url_for('catalog'))

    # Check access token
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        flash('There was an error in the access token info')
        return redirect(url_for('catalog'))

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        flash("Token's user ID doesn't match given user ID")
        return redirect(url_for('catalog'))

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        flash("Token's client ID does not match app's")
        return redirect(url_for('catalog'))

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        flash("Current user is already connected")
        return redirect(url_for('catalog'))

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Add user to table if user is not in database
    user_id = getUserID(login_session['email'])
    if user_id is None:
        user_id = createUser(login_session)
        flash('Created new user: %s' % login_session['username'])
    login_session['user_id'] = user_id

    # Create output and visual response
    output = '''<h1>Welcome, %s</h1><img src="%s" style="width: 300px;
                height: 300px; border-radius: 150px;
                -webkit-border-radius: 150px; -moz-border-radius: 150px;">'''
    flash("you are now logged in as %s" % login_session['username'])
    return output % (login_session['username'], login_session['picture'])


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except NameError:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

# gdisconnect page
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        flash('Current user not connected.')
        return redirect(url_for('catalog'))
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s' %
           login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        flash('Successfully disconnected.')
        return redirect(url_for('catalog'))
    else:
        flash('Failed to revoke token for given user.')
        return redirect(url_for('catalog'))

# app home page
@app.route('/')
@app.route('/catalog/')
def catalog():
    categories = session.query(Category).all()
    latest_items = session.query(Item).order_by(Item.datetimeadded.desc())
    latest_items_10 = latest_items.limit(10)
    return render_template('catalogpage.html',
                           categories=categories,
                           latestItems10=latest_items_10,
                           loginsession=login_session)

# app categories catalog page
@app.route('/catalog/<string:category_name>/')
def categoryCatalog(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(category=category)
    return render_template('categorypage.html',
                           category=category,
                           categories=categories,
                           items=items,
                           loginsession=login_session)

# app item information page
@app.route('/catalog/<string:cat_name>/<string:item_name>/<int:item_id>/')
def itemCatalog(cat_name, item_name, item_id):
    category = session.query(Category).filter_by(name=cat_name).one()
    item = session.query(Item).filter_by(name=item_name,
                                         id=item_id,
                                         category=category).one()
    categories = session.query(Category).all()
    if 'user_id' in login_session:
        user_created = item.user_id == login_session['user_id']
    else:
        user_created = False
    return render_template('itempage.html',
                           categories=categories,
                           item=item,
                           loginsession=login_session,
                           usercreated=user_created)

# JSON pages
# JSON endpoint for home page
@app.route('/catalog/JSON/')
def catalogJSON():
    categories = session.query(Category).all()
    latest_items = session.query(Item).order_by(Item.datetimeadded.desc())
    latest_items_10 = latest_items.limit(10)
    return jsonify(LatestGear=[item.serialize for item in latest_items_10])

# JSON endpoint for a category page
@app.route('/catalog/<string:category_name>/JSON/')
def categoryCatelogJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(category=category).all()
    return jsonify(CategoryItems=[item.serialize for item in items])

# JSON endpoint for an item page
@app.route('/catalog/<string:cat_name>/<string:item_name>/<int:item_id>/JSON/')
def itemCatelogJSON(cat_name, item_name, item_id):
    category = session.query(Category).filter_by(name=cat_name).one()
    item = session.query(Item).filter_by(name=item_name,
                                         id=item_id,
                                         category=category).one()
    categories = session.query(Category).all()
    return jsonify(Item=[item.serialize])

# app item creation page
@app.route('/catalog/create/', methods=['GET', 'POST'])
def createItem():
    # Check if user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    # Extract categories for navigation bar
    categories = session.query(Category)
    list_categories = categories.all()

    # Check which method was used to call function
    # If POST method is called then make changes to database and redirect to
    # home page
    if request.method == 'POST':
        # If category exists find it
        # Else create Category
        cat_name = request.form['category']
        if categories.filter_by(name=cat_name).count() > 0:
            category = categories.filter_by(name=cat_name).one()
        else:
            category = Category(name=cat_name)
            session.add(category)
            session.commit()
            flash('New Category created')

        item = Item(name=request.form['name'],
                    description=request.form['description'],
                    datetimeadded=datetime.now(),
                    category=category,
                    user_id=login_session['user_id'])
        session.add(item)
        session.commit()

        # Give visual response and redirect
        flash('New Item Created!')
        return redirect(url_for('catalog'))

    # If GET method is called render the new item template
    else:
        return render_template('newitempage.html',
                               categories=list_categories,
                               loginsession=login_session)

# app item editer page
@app.route('/catalog/<string:item_name>/<int:item_id>/edit/',
           methods=['GET', 'POST'])
def editItem(item_name, item_id):
    # Check if user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    # Extract categories and item for navigation and database purposes
    categories = session.query(Category)
    list_categories = categories.all()
    item = session.query(Item).filter_by(name=item_name, id=item_id).one()
    items = session.query(Item)

    # Check if user is authorized to edit this item
    if login_session['user_id'] != item.user_id:
        flash('User is not authorized to edit this item')
        return redirect(url_for('catalog'))

    # Check which method was used to call upon this function
    if request.method == 'POST':

        # Grab the new category name and check if a Category for that exists
        # in the database. If it does not create it
        cat_name = request.form['category']
        if categories.filter_by(name=cat_name).count() == 0:
            category = Category(name=cat_name)
            session.add(category)
            session.commit()
            flash('New Category Created!')
        else:
            category = categories.filter_by(name=cat_name).one()

        # Grab the old category
        old_category = item.category

        # Edit the item
        item.name = request.form['name']
        item.description = request.form['description']
        item.category = category
        item.datetimeadded = datetime.now()
        session.add(item)
        session.commit()

        # Check if the old category has any items in it and if it does not
        # delete the category
        if session.query(Item).filter_by(category=old_category).count() == 0:
            session.delete(old_category)
            session.commit()
            flash("%s had no items in it and was deleted!"
                  % old_category.name)

        # Give visual response and redirect
        flash('Item was edited!')
        return redirect(url_for('itemCatalog',
                                cat_name=item.category.name,
                                item_name=item.name,
                                item_id=item.id))
    else:
        return render_template('edititempage.html',
                               categories=list_categories,
                               item=item,
                               loginsession=login_session)

# app item deleter page
@app.route('/catalog/<string:item_name>/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(item_name, item_id):
    # Check if user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    # Grab items and categories from database
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(name=item_name, id=item_id).one()

    # Check if user is authorized to delete this item
    if login_session['user_id'] != item.user_id:
        flash('User is not authorized to delete this item')
        return redirect(url_for('catalog'))

    # If method is post delete item
    if request.method == 'POST':
        # Grab the items category
        category = item.category

        # Delete the item
        session.delete(item)
        session.commit()

        # Check if the old category has any items in it and if it does not
        # delete the category
        if session.query(Item).filter_by(category=category).count() == 0:
            session.delete(category)
            session.commit()
            flash("%s had no items in it and was deleted!" % category.name)

        # Give a visual response to the user and redirect to the home page
        flash('An item was deleted!')
        return redirect(url_for('catalog'))

    # Present delete page
    else:
        return render_template('deleteitempage.html',
                               categories=categories,
                               item=item,
                               loginsession=login_session)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
