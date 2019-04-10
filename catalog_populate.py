#!/usr/bin/env python
# PROGRAMMER: Zachary Amerman
# DATE CREATED: April 6, 2019
# REVISED DATE: April 10, 2019
# PURPOSE: Adds some inital categories and items to the 'category.db' database.

# Import database classes and functions

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog_setup import Base, Category, Gear

# Import datetime class and methods
from datetime import datetime

# Create database engine and bind it to Base
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

# Create database sessions
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Store some initial category names
categories = ["Soccer", "Basketball", 'Baseball', 'Frisbee', 'Snowboarding',
              'Rock Climbing', 'Football', 'Skating', 'Hockey']

# Store some initial gear
gear = {'Soccerball': ['ball for playing soccer', 'Soccer'],
        'Snowboard': ['board for snowboarding', 'Snowboarding']}

# Insert categories into category table in database
for category in categories:
    newCategory = Category(name=category)
    session.add(newCategory)
    session.commit()

# Insert Gear into Gear table in database
for item in gear:
    category = session.query(Category).filter_by(name=gear[item][1]).one()
    newGear = Gear(name=item,
                   description=gear[item][0],
                   datetimeadded=datetime.now(),
                   category=category)
    session.add(newGear)
    session.commit()
