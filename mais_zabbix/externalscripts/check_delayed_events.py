#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
#------------------------------------------------------------------------
# GW-Server Delayed Event Data Check Program (ver.1.0)
# this checks delayed new events exist in event table.
# this is called by Zabbix and is executed as external script.
#
# Usage: check_delayed_events.py <delay>
#  argument:
#   delay :delay time (seconds)
#  oupput:
#   '0 <message>' :OK. all events are NOT delayed.
#   '1 <message>' :NG. delayed events are found.
#   '99 <message>' :other error occurred.
#  exit code:
#   always 0
#
# Author: K.Ohshiba
# Copyright: KDDI Corporation 2017
#------------------------------------------------------------------------
# Modified
# 2017/07/30 K.Ohshiba 1st version.
# 2017/08/24 K.Ohshiba adapted to Pylint
'''

# --- import libraries ---
import os
import sys
import syslog
from datetime import datetime as DT
from datetime import timedelta
import mysql.connector

# --- import local modules ---
import gwcommon

# --- syslog setting ---
PGNAME = sys.argv[0].split('/')[-1]
syslog.openlog(PGNAME, logoption=syslog.LOG_PID, facility=syslog.LOG_LOCAL6)

# --- define constants ---
PRIMARY_FLG = "/var/lib/baogw/primary"

# --- define functions ---
def usage():
    ''' print usage '''
    print('''usage: %s <delay>
 delay : delayed time threshold (seconds)''' % (sys.argv[0].split('/')[-1]))

# send result to zabbix and eyslog
def send_syslog(severity, message):
    ''' write message to system log for only scripts. '''
    syslog.syslog('%s: %s' % (severity, message))

# do DB operation
def exec_db_access(conn, cursor, statement):
    ''' database access function '''
    try:
        cursor.execute(statement)
        dbres = cursor.fetchall()
    except:
        send_syslog(gwcommon.LOG_CRIT, sys.exc_info()[0])
        print("99 DB operation error.")
        raise
    return dbres

# search delayed events
def search_delayed_events(conn, cursor, delaytime):
    ''' search events leaved 5 minutes more from events table. '''
    dtimestr = delaytime.strftime('%Y-%m-%d %H:%M:%S')
    sqlval = (gwcommon.GW_EVENT_STATUS_NEW, dtimestr)
    statement = "SELECT gw_event_id FROM gw_events WHERE event_status='%s' AND update_time < '%s'" \
        % sqlval
    dlyevts = exec_db_access(conn, cursor, statement)
    return dlyevts

# --- main ---
def main():
    ''' main routine '''
    # --- check args ---
    if len(sys.argv) < 2:
        print("99 too few arguments.")
        usage()
        return

    # --- get arguments ---
    try:
        delaythr = int(sys.argv[1])
    except ValueError:
        print("99 could not convert argument to an integer.")
        return

    # --- check primary flag ---
    if os.path.exists(PRIMARY_FLG) is False:
        print("0 quit. because of secondary server.")
        return

    # --- connect to db ---
    try:
        conn = mysql.connector.connect(host=gwcommon.MY_HOST, user=gwcommon.MY_USER, \
            passwd=gwcommon.MY_PASSWD, db=gwcommon.MY_DB, charset=gwcommon.MY_CHRSET)
        cursor = conn.cursor()
    except mysql.connector.errors.IntegrityError:
        send_syslog(gwcommon.LOG_CRIT, sys.exc_info()[0])
        print("99 DB connection error.")
        return

    # --- make search threshold time ---
    ptime = DT.now()
    delaytime = ptime - timedelta(seconds=delaythr)

    # --- search delayed events ---
    delayevts = search_delayed_events(conn, cursor, delaytime)

    # ---- evaluate results ---
    evtnum = len(delayevts)
    if evtnum == 0:
        # OK: no delayed events found.
        send_syslog(gwcommon.LOG_INFO, "no delayed events found.")
        result = "0 no delayed events found."
    else:
        # NG: delayed events found.
        evtlist = []
        for evt in delayevts:
            evtlist.append(str(evt[0]))
            evtstr = ','.join(evtlist)
        send_syslog(gwcommon.LOG_CRIT, "%d delayed events found. %s" % (evtnum, evtstr))
        result = "1 %d delayed events found." % evtnum

    # --- return result to zabbix
    print(result)

    # --- end operation ---
    cursor.close()
    conn.close()
    syslog.closelog()
    return

# --- end of main ---

if __name__ == '__main__':
    try:
        main()
    except Exception as msg:
        send_syslog(gwcommon.LOG_CRIT, sys.exc_info()[0])

# EOF
