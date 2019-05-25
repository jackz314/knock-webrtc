#!/bin/bash
# starts with correct tag info, increment build number
LAST_TAG=$(git describe --tags --abbrev=0 --always)
if [ $LAST_TAG==1.0.* ]
then
    NEW_NUM=$((${LAST_TAG:4}+1)) #only keep the number and increment
    echo $NEW_NUM
else #start a new build number
    echo 8 # this is temporary
fi