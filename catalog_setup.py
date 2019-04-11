#!/usr/bin/env python
# PROGRAMMER: Zachary Amerman
# DATE CREATED: April 6, 2019
# REVISED DATE: April 10, 2019
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
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


# Create Gear class
class Gear(Base):
    __tablename__ = 'gear'

    name = Column(String(80), nullable=False, unique=True)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    datetimeadded = Column(DateTime, nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


# Create engine for catalog
engine = create_engine('sqlite:///catalogwithusers.db')

# Create database
Base.metadata.create_all(engine)
