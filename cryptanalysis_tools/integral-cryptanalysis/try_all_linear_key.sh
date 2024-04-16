#!/bin/bash

for i in {0..257}
do
    echo "For key bit "$i
    python3 koala-three-subsets-without-unknown.py $1 $2 $3 $i
done
