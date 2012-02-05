#!/bin/bash

while true
do
    python manage.py dotask greenpepper.recipe --settings=$1
done

