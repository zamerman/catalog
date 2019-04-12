README v0.2 / 12 APRIL 2019

# Sports Catalog Project

## Introduction
This project is created for the purpose of fulfilling the Udacity Fullstack Web
Developer Nanodegree Project 4 Requirements.

This project locally hosts a server off of port 8000 on your computer. This
server contains a sports gear catalog based off of a sqlite database. Using
the database we can view the latest gear items, the items in a particular sports
category, or a particular item. We can also login using Google which gives us
the ability to add items, and if we are the user who created an item we can
edit or delete the item. JSON endpoints are also included for all pages which
present information

## Usage
To see the project, first run the following commands.
* `python catalog_setup.py`
* `python item_catalog.py`

Now, you can go onto your internet browser and access `localhost:8000` in order
to see the site. The site will empty at first as nothing has been entered.
Login with a google account to add, edit, and delete items.

### Requirements
The python version used to program and test these programs is 2.7.12. Use the
code shown below to check your python version.
```
vagrant@vagrant:/vagrant/project_1$ python --version
Python 2.7.12
```
