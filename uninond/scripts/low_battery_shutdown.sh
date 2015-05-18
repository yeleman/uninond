#!/bin/bash

# script launched at regular intervals

cd /home/uninond/uninond

# check if we should go down (battery level under 10%)
SHUT=`/home/uninond/.local/share/virtualenvs/uninondenv/bin/python -c 'import acpi; print("Y" if acpi.acpi()[-1][1] == "Discharging" and acpi.acpi()[-1][2] <= 10 else "N")'`

if [ "$SHUT" = "Y" ]
then
    ./scripts/powerbtn.sh "System battery criticaly low (<8%). shutting down"
fi
