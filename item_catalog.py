# import webpage framework methods and classes from flask library
from flask import Flask, render_template, url_for
app = Flask(__name__)

# import sql methods and classes from sqlalchemy library
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from catalog_setup import Base, Category, Gear

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# app home page
@app.route('/')
@app.route('/catalog/')
def initialCatalog():
    categories = session.query(Category).all()
    latestGear = session.query(Gear).all()
    return render_template('catalogpage.html',
                        categories=categories,
                        latestGear=latestGear)

# app categories catalog page
#@app.route('/catalog/<string:category>/items/')

# app item information page
#@app.route('/catalog/<string:category>/<string:item_name>')

# app item creation page
#@app.route('/catalog/create/')

# app item editer page
#@app.route('/catalog/<string:item_name>/edit/')

# app item deleter page
#@app.route('/catalog/<string:item_name>/delete/')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
