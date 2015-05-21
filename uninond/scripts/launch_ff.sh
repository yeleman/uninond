#!/bin/bash

pgrep -f firefox
if [ $? -ne 0 ];
then
    # launch firefox in french
    LC_ALL=fr_FR.UTF-8 firefox --display :0
fi
