#!/bin/bash

while true
do
    python manage.py dotask greenpepper.email --settings=$1
done

