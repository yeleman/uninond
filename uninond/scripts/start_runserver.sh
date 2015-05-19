#!/bin/bash

cd /home/uninond/uninond

LANG=fr_FR.UTF-8 /usr/local/bin/pew in uninondenv ./manage.py runserver 0.0.0.0:8000
