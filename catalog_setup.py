#!/usr/bin/env python
# PROGRAMMER: Zachary Amerman
# DATE CREATED: April 6, 2019
# REVISED DATE: April 12, 2019
# PURPOSE: Sets up a sqlite database called 'catalog.db' which has two tables
#          one for categoriesand one for items. The items are connected with a
#          category.

# Import sqlalchemy database classes and methods
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# Create base class
Base = declarative_base()

# Create User class
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(80), nullable=False, unique=True)
    picture = Column(String(80))

# Create Category class
class Category(Base):
    __tablename__ = 'category'

    name = Column(String(80), nullable=False, unique=True)
    id = Column(Integer, primary_key=True)


# Create Item class
class Item(Base):
    __tablename__ = 'items'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    datetimeadded = Column(DateTime, nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # setup serializer function for json endpoints
    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'category_name': self.category.name
        }

# Create engine for catalog
engine = create_engine('sqlite:///catalog.db')

# Create database
Base.metadata.create_all(engine)
