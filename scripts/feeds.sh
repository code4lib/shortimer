#!/bin/bash

source /etc/apache2/virtualenv2/bin/activate

cd /home/ed/Projects/shortimer
./manage.py feeds
