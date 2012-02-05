#!/bin/bash

while true
do
    python manage.py dotask greenpepper.s3 --settings=$1
done

