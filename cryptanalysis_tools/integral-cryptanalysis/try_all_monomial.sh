#!/bin/bash

echo "start computing"
for ((i=0;i<31;i++));do
    for ((j=i+1;j<32;j++));do
	a=$((i*2))
	b=$((i*2+1))
	c=$((j*2))
	d=$((j*2+1))
        python3 koala-three-subsets.py 1 $a,$b,$c,$d $1
    done
done

echo "finished"
