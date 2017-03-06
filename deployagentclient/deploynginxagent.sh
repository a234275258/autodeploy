#!/bin/bash
# 自动启动autodeploy agent
[ -f /etc/init.d/functions ] && source /etc/init.d/functions

if [ $# -eq 0 ];then
  echo "Usage:`basename $0` start|stop|status|restart"
  exit 1
fi
progpath=/root/deployagentclient-prod
progfile=deployagentclient.py
source /opt/autodeploy/bin/activate
cd ${progpath}

# start
start(){
  if ps -ef | grep ${progfile}|grep -v grep &>/dev/null; then
    action  "Start autodeploy nginxagent..."  /bin/true
  else
    nohup python ${progfile} &>/dev/null &
    sleep 1
    if ps -ef | grep ${progfile}|grep -v grep &>/dev/null; then
     action "Start autodeploy nginxagent..."  /bin/true
    else
     action "Start autodeploy nginxagent..."  /bin/false
    fi
  fi
}

# stop
stop(){
  if ps -ef | grep ${progfile} |grep -v grep &>/dev/null; then
    ps -ef | grep ${progfile}| grep -v grep | awk '{print $2}' | xargs kill -9
    if [ $? -eq 0 ];then
      action "Stop autodeploy nginxagent..."  /bin/true
    else
      action "Stop autodeploy nginxagent..."  /bin/false
    fi
  else
    action "Stop autodeploy nginxagent..."  /bin/false
  fi
}


# status
status(){
  if ps -ef | grep ${progfile} &>/dev/null; then
      echo  "autodeploy nginxagent is running.." 
    else
      echo  "autodeploy nginxagent is not running.." 
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
