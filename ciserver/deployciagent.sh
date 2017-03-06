#!/bin/bash
# 自动启动autodeploy ciagent
[ -f /etc/init.d/functions ] && source /etc/init.d/functions

if [ $# -eq 0 ];then
  echo "Usage:`basename $0` start|stop|status|restart"
  exit 1
fi
progpath=/ciserver/newciserver
progfile=ciserver.py
source /opt/env/bin/activate
cd ${progpath}

# check svn
checksvn(){
  if ! which svn &>/dev/null;then
    echo "svn客户端未安装，无法正常使用本系统。"
    state=1
  fi

  if ! /usr/bin/svn --version | grep 1.8 &>/dev/null;then
    echo "你的svn客户端版本太低，至少要1.8或以上"
    state=1
  fi
}

# setting svn
setsvn(){
  svnstat=1  # svn标志
  svnurl=`grep url ${confile} | awk -F'[ =]+' '{print $NF}'`
  svnip=`echo ${svnurl} | awk -F'/' '{print $3}'` # 取出svnIP地址
  if [ -d /$HOME/.subversion ];then
    if [ `ls /$HOME/.subversion/auth/svn.ssl.server | wc -l` -eq 0 ];then
      svnstat=1
    else
      for i in `ls /$HOME/.subversion/auth/svn.ssl.server`;do
        if grep ${svnip} /$HOME/.subversion/auth/svn.ssl.server/${i} &>/dev/null;then
          svnstat=0
        fi
      done
    fi
  else
    svnstat=1
  fi

  if [ ${svnstat} -ne 0 ];then  # 如果系统中还没有svn验证信息
    svnuser=`grep svnuser ${confile} | awk -F'[ =]+' '{print $NF}'`
    svnpassword=`grep svnpassword ${confile} | awk -F'[ =]+' '{print $NF}'`
    if ! which expect &>/dev/null;then
      yum install -y expect
      if [ $? -ne 0 ];then
        echo "安装expect失败，请检测yum源，如果能不能安装expect，请手动执行如下命令才可以正常使用本系统。"
        echo "命令：svn co --depth=empty --username ${svnuser} --password ${svnpassword} ${svnurl} /opt/deploy"
      else
        cmd="/usr/bin/svn co --depth=empty --username ${svnuser} --password ${svnpassword} ${svnurl} ${progpath}/deploytemp"
        expect -c "
        spawn ${cmd};
        expect {
                \"*(p)*\" {send \"p\r\"; exp_continue}
                \"*yes*\" {send \"yes\r\"; exp_continue}
                }" &>/dev/null
        if [ -d ${progpath}/deploytemp ];then
          echo -e "\033[32;1msvn设置成功，可以正常使用本系统。\033[0m"
          rm -rf ${progpath}/deploytemp
        else
          echo -e "\033[32;1msvn设置失败，请检查。\033[0m"
        fi
      fi
    else
      cmd="/usr/bin/svn co --depth=empty --username ${svnuser} --password ${svnpassword} ${svnurl} ${progpath}/deploytemp"
      expect -c "
      spawn ${cmd};
      expect {
              \"*(p)*\" {send \"p\r\"; exp_continue}
              \"*yes*\" {send \"yes\r\"; exp_continue}
              }" &>/dev/null
      if [ -d ${progpath}/deploytemp ];then  # 删除生成的临时目录
        echo -e "\033[32;1msvn设置成功，可以正常使用本系统。\033[0m"
        rm -rf ${progpath}/deploytemp
      else
        echo -e "\033[31;1msvn设置失败，请检查。\033[0m"
      fi
    fi
  fi

}

# start
start(){
  checksvn  # 检查svn
  if [ ${state} -eq 0 ];then  # 当svn正常时，设置svn
    setsvn
  fi
  if ps -ef | grep ${progfile}|grep -v grep &>/dev/null; then
    action  "Start autodeploy ciagent..."  /bin/true
  else
    nohup python ${progfile} &>/dev/null &
    sleep 1
    if ps -ef | grep ${progfile}|grep -v grep &>/dev/null; then
     action "Start autodeploy ciagent..."  /bin/true
    else
     action "Start autodeploy ciagent..."  /bin/false
    fi
  fi
}

# stop
stop(){
  if ps -ef | grep ${progfile} |grep -v grep &>/dev/null; then
    ps -ef | grep ${progfile}| grep -v grep | awk '{print $2}' | xargs kill -9
    if [ $? -eq 0 ];then
      action "Stop autodeploy ciagent..."  /bin/true
    else
      action "Stop autodeploy ciagent..."  /bin/false
    fi
  else
    action "Stop autodeploy ciagent..."  /bin/false
  fi
}


# status
status(){
  if ps -ef | grep ${progfile} &>/dev/null; then
      echo  "autodeploy ciagent is running.."
    else
      echo  "autodeploy ciagent is not running.."
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
