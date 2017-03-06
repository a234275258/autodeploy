#!/bin/bash
# 自动启动autodeploy web
[ -f /etc/init.d/functions ] && source /etc/init.d/functions

if [ $# -eq 0 ];then
  echo "Usage:`basename $0` start|stop|status|restart"
  exit 1
fi
progpath=/autodeploy/prog
progfile=${progpath}/fileserver.py    # 启用文件服务器
webconf=/autodeploy/autodeploy.ini   # 启动web的配置文件
virtualenv=/autodeploy/master/bin/activate
cd ${progpath}


# start
start(){
  state1=0
  state2=0
  source ${virtualenv}  # source环境变量
  if ps -ef | grep ${progfile}|grep -v grep &>/dev/null; then  # 处理文件服务
    state1=1
  else
    nohup python ${progfile} &>/dev/null &
    sleep 1
    if ps -ef | grep ${progfile}|grep -v grep &>/dev/null; then  # 检测是否成功
      state1=1
    fi
  fi

  if ps -ef | grep  ${webconf} |grep -v grep &>/dev/null; then  # 处理web
    state2=1
  else
    uwsgi --ini ${webconf} &>/dev/null
    sleep 1
    if ps -ef | grep  ${webconf} |grep -v grep &>/dev/null; then  # 检测是否成功
      state2=1
    fi
  fi  

  if [ ${state1} -eq 1 -a ${state2} -eq 1 ];then
   action "Start autodeploy web..."  /bin/true
  else
   action "Start autodeploy web..."  /bin/false
  fi
}


# stop
stop(){
  state1=0
  state2=0
  if ps -ef | grep ${progfile} |grep -v grep &>/dev/null; then
    ps -ef | grep ${progfile}| grep -v grep | awk '{print $2}' | xargs kill -9
    if [ $? -eq 0 ];then
      state1=1
    fi
  fi
  if ps -ef | grep ${webconf} |grep -v grep &>/dev/null; then
    ps -ef | grep ${webconf}| grep -v grep | head -n1| awk '{print $2}' | xargs kill -9
    if [ $? -eq 0 ];then
      state2=1
    fi
  fi
  if [ ${state1} -eq 1 -a ${state2} -eq 1 ];then
   action "Stop autodeploy web..."  /bin/true
  else
   action "Stop autodeploy web..."  /bin/false
  fi
}


# status
status(){
  state1=0
  state2=0
  if ps -ef | grep ${progfile} |grep -v grep&>/dev/null; then
    state1=1
  fi
  if ps -ef | grep ${webconf} |grep -v grep &>/dev/null; then
    state2=1
  fi
  if [ ${state1} -eq 1 -a ${state2} -eq 1 ];then
    echo  "autodeploy web is running.." 
  else
    echo  "autodeploy web is not running.." 
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