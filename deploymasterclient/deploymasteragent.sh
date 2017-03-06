#!/bin/bash
# 自动启动autodeploy masteragent
[ -f /etc/init.d/functions ] && source /etc/init.d/functions

if [ $# -eq 0 ];then
  echo "Usage:`basename $0` start|stop|status|restart"
  exit 1
fi
progpath=/opt/deploymasterclient
progfile=deploymasterclient.py 
cd ${progpath}

# start
start(){
  if ps -ef | grep ${progfile}|grep -v grep &>/dev/null; then
    action  "Start autodeploy masteragent..."  /bin/true
  else
    nohup python ${progfile} &>/dev/null &
    sleep 1
    if ps -ef | grep ${progfile}|grep -v grep &>/dev/null; then
     action "Start autodeploy masteragent..."  /bin/true
    else
     action "Start autodeploy masteragent..."  /bin/false
    fi
  fi
}

# stop
stop(){
  if ps -ef | grep ${progfile} |grep -v grep &>/dev/null; then
    ps -ef | grep ${progfile}| grep -v grep | awk '{print $2}' | xargs kill -9
    if [ $? -eq 0 ];then
      action "Stop autodeploy masteragent..."  /bin/true
    else
      action "Stop autodeploy masteragent..."  /bin/false
    fi
  else
    action "Stop autodeploy masteragent..."  /bin/false
  fi
}


# status
status(){
  if ps -ef | grep ${progfile} &>/dev/null; then
      echo  "autodeploy masteragent is running.." 
    else
      echo  "autodeploy masteragent is not running.." 
    fi
}


case $1 in
start)
  start
  ;;
stop)
  stop
  ;;
status)
  status
  ;;
restart)
  stop
  sleep 1
  start
  ;;
-h|--help)
  echo "Usage:`basename $0` start|stop|status|restart"
  exit 1
  ;;
*)
  echo "Usage:`basename $0` start|stop|status|restart"
  exit 1
  ;;
esac
