from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog_setup import Base, Category, Gear

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind=engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

categories = ["Soccer", "Basketball", 'Baseball', 'Frisbee', 'Snowboarding',
        'Rock Climbing', 'Football', 'Skating', 'Hockey']

gear = {'Soccerball':['ball for playing soccer', 'Soccer'],
        'Snowboard':['board for snowboarding', 'Snowboarding']}

for category in categories:
    newCategory = Category(name=category)
    session.add(newCategory)
    session.commit()

for item in gear:
    category=session.query(Category).filter_by(name=gear[item][1]).one()
    newGear = Gear(name=item, description=gear[item][0], category=category)
    session.add(newGear)
    session.commit()
