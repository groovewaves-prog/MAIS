#!/bin/sh
#------------------------------------------------------------------------------
# insert to smmpttlog form trap_recive_server
# make by oozera
#------------------------------------------------------------------------------


echo '=== start insert ==='

#---- logging path ----
SNMPTT_PATH='/var/log/snmptt/'

#---- logging file ----
#SNMPTT_FILE_NAME='snmptt.log'
SNMPTT_FILE_NAME='test_for_shell_snmptt.log'


INSERT_DATA=$1

#---- echo data ----
echo "insert data:$INSERT_DATA"

#---- insert data ----
echo "insert snmptt path --> $SNMPTT_PATH$SNMPTT_FILE_NAME"

echo $INSERT_DATA >> $SNMPTT_PATH$SNMPTT_FILE_NAME

echo '=== finsh insert ==='

exit 0
