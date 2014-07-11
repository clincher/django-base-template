{% if False %}
# Django 1.6 Base Template #

## About ##

This template is based off of the work of [Mozilla Playdoh][playdoh] and
[Two Scoops of Django][twoscoops], as well as experience with other Django
layouts/project templates.

This template should work with Django 1.6 and python 3.3+

## Features ##

Migrations:

- South

Caching:

- pylibmc

Admin:

- Includes django-debug-toolbar for development and production (enabled for superusers)

Testing:

- nose and django-nose
- pylint, pep8, and coverage

Any of these options can added, modified, or removed as you like after creating your project.

## How to use this project template to create your project ##

- mkvirtualenv project_name
- pip3 install django
- $ django-admin.py startproject --template https://github.com/clincher/django-base-template/zipball/master --extension py,md,rst project_name
- $ cd project_name
- $ pip3 install -r requirements/local.txt
- $ cp projectname/settings/local-dist.py projectname/settings/local.py
- $ python manage.py syncdb --migrate
- $ python manage.py runserver

{% endif %}
# The {{ project_name|title }} Project #

## About ##

Describe your project here.

## Prerequisites ##

- Python 3.3+
- pip
- virtualenvwrapper

## Installation ##

License
-------
This software is licensed under the [New BSD License][BSD]. For more
information, read the file ``LICENSE``.

[BSD]: http://opensource.org/licenses/BSD-3-Clause
