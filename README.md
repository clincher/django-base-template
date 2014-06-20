{% if False %}
# Django 1.6 Base Template #

## About ##

This template is based off of the work of [Mozilla Playdoh][playdoh] and
[Two Scoops of Django][twoscoops], as well as experience with other Django
layouts/project templates. Playdoh is mainly setup for Mozilla's systems and is
overly-complicated for a simple project template. (Though it does provide some
very good real-world use examples.)

As much as I could, all the code has been updated to use the new suggested layout
and functionality in Django 1.6.

[playdoh]: https://github.com/mozilla/playdoh
[twoscoops]: https://github.com/twoscoops/django-twoscoops-project

## Features ##

By default, this project template includes:

A set of basic templates built from HTML5Boilerplate 4.1.0 and Twitter Bootstrap 3.0.2 (located in the
base app, with css and javascript loaded from CloudFlare CDN by default).

Templating:

- django_compressor for compressing javascript/css/less/sass

Security:

- bleach
- bcrypt - uses bcrypt for password hashing by default

Background Tasks:

- Celery

Migrations:

- South

Caching:

- python-memcached

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
- Uncomment your preferred database adapter in requirements/compiled.txt (MySQL, Postgresql, or skip this step to stick with SQLite)
- $ pip3 install -r requirements/local.txt
- $ cp projectname/settings/local-dist.py projectname/settings/local.py
- $ python manage.py syncdb --migrate
- $ python manage.py runserver

{% endif %}
# The {{ project_name|title }} Project #

## About ##

Describe your project here.

## Prerequisites ##

- Python 3.0+
- pip
- virtualenvwrapper

## Installation ##

License
-------
This software is licensed under the [New BSD License][BSD]. For more
information, read the file ``LICENSE``.

[BSD]: http://opensource.org/licenses/BSD-3-Clause
