#!/bin/bash

for i in {0..257}
do
    echo "For bit at position "$i
    python3 koala-three-subsets-without-unknown.py $1 $i $2 $3
done
