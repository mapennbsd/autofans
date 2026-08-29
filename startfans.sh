#!/bin/sh

LOGFILE='/home/mapenn/autofans/log/faninfo.log'
RUNFILE='/home/mapenn/autofans/autofans.py'

if test -f $LOGFILE
then
       mv $LOGFILE $LOGFILE.`date +%Y%m%d`
fi

touch $LOGFILE

nohup $RUNFILE > $LOGFILE 2>&1 &

exit 0
