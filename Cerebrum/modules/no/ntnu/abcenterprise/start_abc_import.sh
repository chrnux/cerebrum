#! /bin/sh
## set -x
if [ ! -z "${PYTHONPATH}" ] ; then
    export PYTHONPATH="${PYTHONPATH}:"
fi

export PYTHONPATH="${HOME}/cerebrum/Cerebrum/modules/no/ntnu/abcenterprise:${PYTHONPATH}${HOME}/cerebrum/:${HOME}/install/etc/cerebrum/:${HOME}/install/lib/python2.5/site-packages/:$HOME/install/var/www/htdocs/"

## dry-run
./import_ABC_Enterprise.py -d -f $1
##
## import
## ./import_ABC_Enterprise.py -f $1

