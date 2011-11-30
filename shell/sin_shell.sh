#!/usr/bin/env bash

bin=`dirname "$0"`
bin=`cd "$bin"; pwd`

python $bin/../client/python/sin/sin_client.py $*
