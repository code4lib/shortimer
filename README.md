shortimer
---------

shortimer is a [django](http://www.djangoproject.com) web app that collects job 
announcements from the code4lib discussion list and puts them on the Web. 
Basically shortimer subscribes to the code4lib discussion list, and periodically
pops its email account looking for job advertisements. When it notices what
looks like a job ad it adds it to the database, where it can be curated by
folks who have an account.

To get shortimer running locally you'll need to follow these instructions. The 
first step installs Python's virtualenv which provides a sandbox environment 
for you to install the other dependencies. Clearly apt-get is only available 
on Debian based systems, but you will probably have a similar mechanism to 
get virtualenv installed using other packages managers (homebrew, rpm, etc).
From there on things should work independent of what operating system you are
using.

1. `sudo apt-get install python-virtualenv`
1. `git clone git://github.com/code4lib/shortimer.git`
1. `cd shortimer`
1. `virtualenv --no-site-packages ENV`
1. `source ENV/bin/activate`
1. `pip install -r requirements.pip`
1. `cp settings.py.template settings.py`
1. in order for people to login with their github, facebook, twitter, linkedin
credentials you'll need to create applications on those sites, and fill in oauth
keys in your settings.py. For development you can probably get by with just one
login provider.
1. `python manage.py syncdb --migrate`
1. `python manage.py loaddata subjects_keywords`
1. fetch and load the code4lib email archive `python manage.py load_mboxes`
1. `python manage.py runserver`
1. point web browser at http://locahost:8000

License:

Public Domain


