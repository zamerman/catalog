#!/usr/bin/env python
# PROGRAMMER: Zachary Amerman
# DATE CREATED: April 1, 2019
# REVISED DATE: April 10, 2019
# PURPOSE: When called serves as a server on localhost port 8000. The site is
#          a catalog of sports items organised into various categories. Items
#          and categories are stored in a sqlite database. The site gives the
#          latest added items, the items in a particular category, and a
#          description of a particular item. In addition, the site can be logged
#          into using google. Logging in enables items to be added, edited, or
#          deleted.
#
## Site paths/pages
# localhost:8000
# localhost:8000/catalog/
# localhost:8000/login/
# localhost:8000/gconnect
# localhost:8000/gdisconnect
# localhost:8000/catalog/<string:category_name>/
# localhost:8000/catalog/<string:category_name>/<string:item_name>/
# localhost:8000/catalog/create/
# localhost:8000/catalog/<string:item_name>/edit/
# localhost:8000/catalog/<string:item_name>/delete/

# import webpage framework methods and classes from flask library
from flask import Flask, render_template, url_for, request, redirect, flash
app = Flask(__name__)

# import login and state classes and methods
from flask import session as login_session
import random, string

# import oauth handlings classes and methods
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# import datetime methods and class
from datetime import datetime

# import sql methods and classes from sqlalchemy library
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from catalog_setup import Base, Category, Gear, User

# set up database handlers
engine = create_engine('sqlite:///catalogwithusers.db',
                    connect_args={'check_same_thread':False},
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
    return render_template('login.html', STATE=state)

# gconnect post page
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Check that the state tokens match
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorizationcode.'),
            401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check access token
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
        access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

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

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

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

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

# gdisconnect page
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        flash('Current user not connected.')
        return redirect(url_for('initialCatalog'))
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
        flash('Successfully disconnected.')
        return redirect(url_for('initialCatalog'))
    else:
        flash('Failed to revoke token for given user.')
        return redirect(url_for('initialCatalog'))

# app home page
@app.route('/')
@app.route('/catalog/')
def initialCatalog():
    categories = session.query(Category).all()
    latestGear = session.query(Gear).order_by(Gear.datetimeadded.desc())
    latestGear10 = latestGear.limit(10)
    return render_template('catalogpage.html',
                        categories=categories,
                        latestGear=latestGear10)

# app categories catalog page
@app.route('/catalog/<string:category_name>/')
def categoryCatalog(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).all()
    latestGear = session.query(Gear).filter_by(category=category)
    return render_template('categorypage.html',
                        category=category,
                        categories=categories,
                        latestGear=latestGear)

# app item information page
@app.route('/catalog/<string:category_name>/<string:item_name>')
def gearCatalog(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    gear = session.query(Gear).filter_by(name=item_name,category=category).one()
    categories = session.query(Category).all()
    return render_template('gearpage.html',
                        categories=categories,
                        gear=gear)



# app item creation page
@app.route('/catalog/create/', methods=['GET', 'POST'])
def createGear():
    # Check if user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
        s
    # Extract categories for navigation bar
    categories = session.query(Category).all()

    # Check which method was used to call function
    # If POST method is called then make changes to database and redirect to
    # home page
    if request.method == 'POST':
        # If the name of the item is unclaimed create it
        # Else flash an error
        item_name = request.form['name']
        if session.query(Gear).filter_by(name=item_name).count() == 0:
            # If category exists find it
            # Else create Category
            cat_name=request.form['category']
            if session.query(Category).filter_by(name=cat_name).count() > 0:
                category=session.query(Category).filter_by(name=cat_name).one()
            else:
                category=Category(cat_name)
                session.add(category)
                session.commit()
                flash('New Category created')

            gear=Gear(name=request.form['name'],
                description=request.form['description'],
                datetimeadded=datetime.now(),
                category=category)
            session.add(gear)
            session.commit()
            flash('New Gear Item Created!')
        else:
            flash('Name of item is already claimed!')

        return redirect(url_for('initialCatalog'))

    # If GET method is called render the new gear template
    else:
        return render_template('newgearpage.html',
                            categories=categories)

# app item editer page
@app.route('/catalog/<string:item_name>/edit/', methods=['GET', 'POST'])
def editGear(item_name):
    # Check if user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    # Extract categories and gear for navigation and display purposes
    categories = session.query(Category).all()
    gear=session.query(Gear).filter_by(name=item_name).one()

    # Check which method was used to call upon this function
    if request.method == 'POST':

        # Check if the name of the gear is still the same or if the namespace
        # is free
        if (request.form['name'] == gear.name or
        session.query(Gear).filter_by(name=request.form['name']).count() == 0):

            cat_name=request.form['category']
            if session.query(Category).filter_by(name=cat_name).count()==0:
                category=Category(name=cat_name)
                session.add(category)
                session.commit()
                flash('New Category Created!')
            else:
                category=session.query(Category).filter_by(name=cat_name).one()

            gear.name = request.form['name']
            gear.description = request.form['description']
            gear.category = category
            gear.datetimeadded = datetime.now()

            session.add(gear)
            session.commit()

            flash('Item was edited!')

        # The name collides with names for another item
        else:
            flash('Another item already has that name!')

        return redirect(url_for('gearCatalog',
                            category_name=gear.category.name,
                            item_name=gear.name))
    else:
        return render_template('editgearpage.html',
                            categories=categories,
                            gear=gear)

# app item deleter page
@app.route('/catalog/<string:item_name>/delete/',
           methods=['GET', 'POST'])
def deleteGear(item_name):
    # Check if user is logged in
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    # Grab the gear which is being considered for deletion
    gear=session.query(Gear).filter_by(name=item_name).one()

    # If method is post delete gear
    if request.method == 'POST':
        session.delete(gear)
        session.commit()
        flash('An item was deleted!')
        return redirect(url_for('initialCatalog'))

    # Present delete page
    else:
        categories = session.query(Category).all()
        return render_template('deletegearpage.html',
                               categories=categories,
                               gear=gear)

if __name__ == '__main__':
    app.secret_key='super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
