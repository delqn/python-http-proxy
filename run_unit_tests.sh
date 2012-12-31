#!/bin/bash

pushd tests
for x in $(ls test*.py)
do
	python $x
done
popd
