# import webpage framework methods and classes from flask library
from flask import Flask, render_template, url_for, request, redirect, flash
app = Flask(__name__)

from datetime import datetime

# import sql methods and classes from sqlalchemy library
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from catalog_setup import Base, Category, Gear

engine = create_engine('sqlite:///catalog.db',
                    connect_args={'check_same_thread':False},
                    poolclass=StaticPool)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

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
    gear = session.query(Gear).filter_by(name=item_name, category=category).one()
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

        # Store category name and gear name in variables
        category_name=request.form['category']
        gear_name=request.form['name']

        # Check if the gear we are creating already exists in he database
        # For web page navigation purposes all gear names must be unique
        if session.query(Gear).filter_by(name=gear_name).count() > 0:
            flash('Gear with that name already exists!')
        else:

            # Check if the category for our new gear exists if not create it
            if session.query(Category).filter_by(name=category_name).count()==0:
                category=Category(name=category_name)
                session.add(category)
                session.commit()
                flash('New Category Created!')
            else:
                category=session.query(Category).filter_by(name=category_name).one()

            # Create new gear item
            gear=Gear(name=gear_name,
                description=request.form['description'],
                datetimeadded=datetime.now(),
                category=category)
            session.add(gear)
            session.commit()
            flash('New Gear Item Created!')
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

        category_name=request.form['category']

        # Check if the name of the gear is still the same
        if request.form['name'] == gear.name:

            if session.query(Category).filter_by(name=category_name).count()==0:
                category=Category(name=category_name)
                session.add(category)
                session.commit()
                flash('New Category Created!')
            else:
                category=session.query(Category).filter_by(name=category_name).one()

            gear.description = request.form['description']
            gear.category = category
            gear.datetimeadded = datetime.now()

            session.add(gear)
            session.commit()

            flash('Item was edited!')

        # The name of the gear is different
        else:
            # Check if the new name collides with the names of other gear
            if session.query(Gear).filter_by(name=request.form['name']).count()==0:

                if session.query(Category).filter_by(name=category_name).count()==0:
                    category=Category(name=category_name)
                    session.add(category)
                    session.commit()
                    flash('New Category Created!')
                else:
                    category=session.query(Category).filter_by(name=category_name).one()

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
