#!/bin/bash

source /etc/apache2/virtualenv/bin/activate

cd /home/ed/Projects/shortimer
./manage.py analytics
