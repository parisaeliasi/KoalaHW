#!/bin/bash

for ((i=0;i<257;i++));do
    echo 'For bit position '$i
    bash try_all_quadratic_key.sh $i
done
