#!/bin/bash

pushd tests
for x in $(ls test*.py)
do
	python2 $x
done
popd
