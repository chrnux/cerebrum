#
# Configuration file for Cerebrum, bofh.sh and bofhd.sh.
# The idea is to keep all the configuration in one place.
#
# For Cerebrum/USIT.
#
# Save this file as ~/.cerebrumrc.
#
# A file like ~/.cereconf/uio/cerepath.py will override the common configuration.
#
# Changelog:
#   2013-06-26, Alexander Rødseth <rodseth@usit.uio.no>
#

CEREBRUM_PATH=~/checkout/cerebrum
CERECONF_PATH=~/.cerebrum

# Set CEREBRUM_INST to uio if it's not already set
[ -z "$CEREBRUM_INST" ] && CEREBRUM_INST=uio

# UIO
CEREBRUM_DATABASE_USER_uio=cerebrum
CEREBRUM_DATABASE_HOST_uio=dbpg-cere-utv.uio.no
CEREBRUM_DATABASE_NAME_uio=cerebrum_uio_rw

# UIA
CEREBRUM_DATABASE_USER_uia=cerebrum
CEREBRUM_DATABASE_HOST_uia=dbpg-cere-utv.uio.no
CEREBRUM_DATABASE_NAME_uia=cerebrum_uio_rw

# For cereconf.py
export CERECONF_GLOBAL="/cerebrum/$CEREBRUM_INST/etc/cerebrum"
eval export CEREBRUM_DATABASE_USER=\$CEREBRUM_DATABASE_USER_$CEREBRUM_INST
eval export CEREBRUM_DATABASE_HOST=\$CEREBRUM_DATABASE_HOST_$CEREBRUM_INST
eval export CEREBRUM_DATABASE_NAME=\$CEREBRUM_DATABASE_NAME_$CEREBRUM_INST

# BOFHD
BOFHD_CONFIG_DAT="$CERECONF_PATH/bofhd/config.dat"
BOFHD_PY="$CEREBRUM_PATH/servers/bofhd/bofhd.py"
BOFHD_PORT=1337

# BOFH
BOFH_PROMPT=bofhtest
#BOFH_USER=bootstrap_account
BOFH_USER="$USER"

# PYTHON
PYTHON_BIN=/local/bin/python

# PYTHONPATH
PYTHON_SITE_PACKAGES=/site/lib/python2.5/site-packages
PYTHON_CEREBRUM_MODULES="$CEREBRUM_PATH"
CERECONF_COMMON=$CERECONF_PATH/common
CERECONF_CUSTOM=$CERECONF_PATH/"$CEREBRUM_INST/"
export PYTHONPATH="$PYTHON_SITE_PACKAGES:$CERECONF_CUSTOM:$CERECONF_COMMON:$CERECONF_GLOBAL:$PYTHON_CEREBRUM_MODULES"

# Output various settings
echo
echo "Cerebrum configuration:"
echo
echo -e "\tinstitution:\t$CEREBRUM_INST"
echo -e "\tdb user:\t$CEREBRUM_DATABASE_USER"
echo -e "\tdb host:\t$CEREBRUM_DATABASE_HOST"
echo -e "\tdb name:\t$CEREBRUM_DATABASE_NAME"
echo -e "\tPYTHONPATH:\t$PYTHONPATH"
echo

# Write config.dat for BOFHD if it doesn't exist
if [ ! -e "$CERECONF_PATH/bofhd/config.dat" ]; then
  mkdir -p "$CERECONF_PATH/bofhd"
  cat << 'EOF' > "$CERECONF_PATH/bofhd/config.dat"
# Config file for bofhd
Cerebrum.modules.no.uio.bofhd_uio_cmds/BofhdExtension
Cerebrum.modules.no.uio.bofhd_guestaccounts_cmds/BofhdExtension
#Cerebrum.modules.no.uio.printer_quota.bofhd_pq_cmds/BofhdExtension
Cerebrum.modules.no.uio.bofhd_ephorte_cmds/BofhdExtension
#Cerebrum.modules.dns.bofhd_dns_cmds/BofhdExtension
#Cerebrum.modules.dns.Subnet/BofhdExtension
EOF
fi

# Write cereconf.py if it doesn't exist
if [ ! -e "$CERECONF_PATH/common/cereconf.py" ]; then
  mkdir -p "$CERECONF_PATH/common"
  cat << 'EOF' > "$CERECONF_PATH/common/cereconf.py"
import sys, os, os.path
execfile(os.path.join(os.getenv('CERECONF_GLOBAL'), 'cereconf.py'))
CEREBRUM_DATABASE_CONNECT_DATA['user'] = os.getenv('CEREBRUM_DATABASE_USER', "cerebrum")
CEREBRUM_DATABASE_CONNECT_DATA['host'] = os.getenv('CEREBRUM_DATABASE_HOST', "dbpg-cere-utv.uio.no")
CEREBRUM_DATABASE_NAME = os.getenv('CEREBRUM_DATABASE_NAME', "cerebrum_uio_rw")
EOF
fi

