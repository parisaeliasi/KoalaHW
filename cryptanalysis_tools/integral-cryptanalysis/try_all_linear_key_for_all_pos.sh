#!/bin/bash

for i in {0..257}
do
    echo "For pos "$i
    for j in {0..257}
    do
	echo "For key bit "$j
	python3 koala-three-subsets-without-unknown.py $1 $i $2 $j
    done
done
