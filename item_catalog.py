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
    categories = session.query(Category).all()
    if request.method == 'POST':
        category_name=request.form['category']
        if session.query(Category).filter_by(name=category_name).count() == 0:
            category=Category(name=category_name)
            session.add(category)
            session.commit()
        else:
            category=session.query(Category).filter_by(name=category_name).one()
        gear=Gear(name=request.form['name'],
            description=request.form['description'],
            datetimeadded=datetime.now(),
            category=category)
        session.add(gear)
        session.commit()
        return redirect(url_for('initialCatalog'))
    else:
        return render_template('newgearpage.html',
                            categories=categories)

# app item editer page
#@app.route('/catalog/<string:item_name>/edit/')

# app item deleter page
#@app.route('/catalog/<string:item_name>/delete/')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
