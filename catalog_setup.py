#!/usr/bin/env python
# PROGRAMMER: Zachary Amerman
# DATE CREATED: April 6, 2019
# REVISED DATE: April 10, 2019
# PURPOSE:

# Import sqlalchemy database classes and methods
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# Create base class
Base = declarative_base()


# Create Category class
class Category(Base):
    __tablename__ = 'category'

    name = Column(String(80), nullable=False, unique=True)
    id = Column(Integer, primary_key=True)


# Create Gear class
class Gear(Base):
    __tablename__ = 'gear'

    name = Column(String(80), nullable=False, unique=True)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    datetimeadded = Column(DateTime, nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)


# Create engine for catalog
engine = create_engine('sqlite:///catalog.db')

# Create database
Base.metadata.create_all(engine)
