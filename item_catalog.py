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
from catalog_setup import Base, Category, Gear

# set up database handlers
engine = create_engine('sqlite:///catalog.db',
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
    return render_template('login.html')

# gconnect post page
@app.route('/gconnect/', methods=['POST'])

# app home page
@app.route('/')
@app.route('/catalog/')
def initialCatalog():
    categories = session.query(Category).all()
    latestGear = session.query(Gear).order_by(Gear.datetimeadded.desc())
    return render_template('catalogpage.html',
                        categories=categories,
                        latestGear=latestGear)

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
    gear=session.query(Gear).filter_by(name=item_name).one()
    if request.method == 'POST':
        session.delete(gear)
        session.commit()
        flash('An item was deleted!')
        return redirect(url_for('initialCatalog'))
    else:
        categories = session.query(Category).all()
        return render_template('deletegearpage.html',
                               categories=categories,
                               gear=gear)

if __name__ == '__main__':
    app.secret_key='super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
