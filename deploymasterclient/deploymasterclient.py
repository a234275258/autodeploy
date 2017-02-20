#!/bin/usr/env python
# coding: utf-8

import socket
import os
import ConfigParser
import logging.config
import etcd
import time
import shutil
import re
import commands
import threading

BASE_DIR = os.path.dirname(__file__)  # 程序目录
logging.config.fileConfig(os.path.join(BASE_DIR, "logger.conf"))  # 日志配制文件
logger = logging.getLogger("prodution")  # 取日志标签，可选为development,prodution

config = ConfigParser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'deploymasterclient.conf'))

masterip = config.get('master', 'masterip')
masterport = config.get('master', 'masterport')

localip = config.get('local', 'localip')
localtype = config.get('local', 'localtype')

etcdip = config.get('etcd', 'etcdip')  # etcd ip地址
etcdport = config.get('etcd', 'etcdport')  # etcd 端口

rcmb = config.get('mb', 'rcmb')  # 复本控制器模板
semb = config.get('mb', 'semb')  # 服务模板

pjsnamespace = config.get('namespace', 'pjnamespace')  # 项目名称空间


# 判断模块是否存在
def k8scheck(pjname):
    if re.search('-', pjname):  # 如果为真为web项目
        stat, res = commands.getstatusoutput("kubectl get rc \
            --namespace=%s|awk 'NR>=2'|grep '\<%s\>'|wc -l" % (pjsnamespace, pjname))
    else:
        stat, res = commands.getstatusoutput("kubectl get rc \
            --namespace=%s|awk 'NR>=2'|grep '\<%s\>' | grep -v web |wc -l" % (pjsnamespace, pjname))
    if int(res) >= 1:
        return 1
    else:
        return 0


# 检测当前复本数
def checkrccount(pjname):
    try:
        if '-web' in pjname:  # 代表web项目
            stat, res = commands.getstatusoutput(
                "kubectl  get rc --namespace=%s | grep '%s' | wc -l" % (pjsnamespace, pjname))
        else:
            stat, res = commands.getstatusoutput(
                "kubectl  get rc --namespace=%s | grep '%s'| grep -v 'web' | wc -l" % (pjsnamespace, pjname))
        return res
    except Exception, e:
        logger.error(u"获取%s项目复本数失败，错误代码%s" % (pjname, e))
        return 0


# 检测是否需要开启外部访问se
def checksecount(pjname):
    try:
        if '-web' in pjname:  # 代表web项目
            stat, res = commands.getstatusoutput(
                "kubectl  get service --namespace=%s | grep '%s' | wc -l" % (pjsnamespace, pjname))
        else:
            stat, res = commands.getstatusoutput(
                "kubectl  get service --namespace=%s | grep '%s'| grep -v 'web' | wc -l" % (pjsnamespace, pjname))
        return res
    except Exception, e:
        logger.error(u"获取%s项目服务失败，错误代码%s" % (pjname, e))
        return 0


# 调整rc个数
def scalerc(pjname, replicas):
    try:
        stat, res = commands.getstatusoutput(
            "kubectl scale --replicas=%s rc %s --namespace=%s" % (replicas, pjname, pjsnamespace))
        return res
    except Exception, e:
        logger.error(u'项目%s调整复本个数失败，错误代码：%s' % (pjname, e))
        return 0


# 删除项目服务
def delservice(pjname):
    try:
        stat, res = commands.getstatusoutput("kubectl delete service %s --namespace=%s" % (pjname, pjsnamespace))
        return res
    except Exception, e:
        logger.error(u'删除项目服务%s失败，错误代码：%s' % (pjname, e))
        return 0


# 获取项目外部暴露端口
def getnodport(pjname):
    try:
        stat, res = commands.getstatusoutput("kubectl describe service %s --namespace=%s \
                  | grep -i 'nodeport' | grep -iv 'type' | awk  '{print $3}' | awk -F '/' '{print $1}'" % (
        pjname, pjsnamespace))
        return res
    except Exception, e:
        logger.error(u'项目%s获取外部端口失败，错误代码：%s' % (pjname, e))
        return 0


# 模板处理函数,入参为项目名，复本数
def rcmbhander(pjname, replicas):
    try:
        rcmbfile = os.path.join(BASE_DIR, rcmb)
        rcmbtemp = os.path.join(BASE_DIR, rcmb.split('.')[0] + '-' + pjname + '.yaml')
        shutil.copyfile(rcmbfile, rcmbtemp)  # 复制文件

        f = open(rcmbtemp, 'r+')  # 读取文件内容
        context = f.readlines()
        f.close()
        for i in range(len(context)):
            context[i] = context[i].replace('zhmb1', pjname)  # 替换项目名
            if re.search("replicas", context[i]):
                context[i] = re.sub('[0-9]', str(replicas), context[i])  # 替换复本数

        f = open(rcmbtemp, 'w+')  # 回写文件
        f.writelines(context)
        f.close()
        stat, res = commands.getstatusoutput("kubectl create -f %s" % (rcmbtemp))
        os.remove(rcmbtemp)
        return res
    except:
        return 0


# 模板处理函数,入参为项目名，项目端口
def sembhander(pjname, port):
    try:
        sembfile = os.path.join(BASE_DIR, semb)
        sembtemp = os.path.join(BASE_DIR, semb.split('.')[0] + '-' + pjname + '.yaml')
        shutil.copyfile(sembfile, sembtemp)  # 复制文件

        f = open(sembtemp, 'r+')  # 读取文件内容
        context = f.readlines()
        f.close()
        for i in range(len(context)):
            context[i] = context[i].replace('zhmb1', pjname)  # 替换项目名
            if re.search("9999", context[i]):
                context[i] = re.sub('9999', str(port), context[i])  # 替换复本数

        f = open(sembtemp, 'w+')  # 回写文件
        f.writelines(context)
        f.close()
        stat, res = commands.getstatusoutput("kubectl create -f %s" % (sembtemp))
        os.remove(sembtemp)
        return res
    except:
        return 0


def getfile(targetfile, localfile):
    ip = masterip
    port = masterport
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    localdir = os.path.split(localfile)[0]
    filestat = 0
    if not os.path.exists(localdir):
        try:
            os.makedirs(localdir)
        except:
            logger.error(u'创建%s目录失败', localdir)
    try:
        s.connect((ip, int(port)))
        client_command = "get %s" % targetfile
        s.send(client_command)
        data = s.recv(4096)
        if data == 'ready':
            f = open(localfile, 'wb+')
            while True:
                data = s.recv(4096)
                if data == 'EOF':
                    logger.error(u'文件%s传输完成' % localfile)
                    break
                f.write(data)
            f.close()
        filesize = os.path.getsize(localfile)
        filestat = 1 if filesize else 0
    except:
        logger.error(u'下载%s文件%s失败' % (ip, targetfile))
    finally:
        s.close()
        return filestat


def initetcd():
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        key = '/node' + '/' + localtype + '-' + localip + '/ip'  # 在node目录下生成以类型加IP的键值对
        value = localip
        try:
            client.get(key)  # 如果key存在
            if client.get(key).value != localip:
                client.delete(key, recursive=True)  # 删除key
        except:
            pass
        client.set(key, value)
        return 1
    except:
        return 0


# 获取系统信息,接收两个参数，第一个为键，第二个为etcd连接对像
def getsysteminfo(key, client):
    hostname = ""    # 主机名
    physicalm = ""   # 物理内存大小
    freem = ""       # 空闲内存
    cpuidle = ""     # 空闲cpu
    freedisk = ""    # 空闲磁盘
    container = ""   # 容器个数
    updatedate = ""  # 更新时间

    while True:
        # 获取主机名
        command = """hostname | awk -F'.' '{print $1}'"""
        stat, res = commands.getstatusoutput(command)
        hostname = res

        # 获取物理内存, 可用内存
        command = """free -m | grep "^Mem" | awk '{print $2":"$4}'"""
        stat, res = commands.getstatusoutput(command)
        try:
            physicalm, freem = res.split(":")
            if int(physicalm) > 1024:
                physicalm = str(round(int(physicalm) / 1024.0)) + "G"
            else:
                physicalm = str(physicalm) + "M"
            if int(freem) > 1024:
                freem = "%.1fG" % (int(freem) / 1024.0)
            else:
                freem = str(freem) + "M"
        except:
            physicalm, freem = 0, 0

        # 获取磁盘内存
        command = """df -hT | egrep "xfs|ext4|nfs" | awk '{print $NF,$(NF-2)}' | tr  '\n' \" \""""
        stat, res = commands.getstatusoutput(command)
        freedisk = res

        # 获取cpu空闲率
        command = """vmstat | awk 'NR==3{print $(NF-2)}'"""
        stat, res = commands.getstatusoutput(command)
        cpuidle = res

        # 获取容器个数
        command = """docker info 2>/dev/null | grep 'Running:' | awk -F':' '{print $2}'"""
        stat, res = commands.getstatusoutput(command)
        if res:
            container = res
        else:
            container = 0

        updatedate = time.strftime('%Y-%m-%d %H:%M:%S')

        # 拼装结果返回
        value = '{"hostname":"%s","ip":"%s","type":"%s","physicalm":"%s", "freem":"%s","cpuidle":"%s","freedisk":"%s",' \
                '"container":"%s","updatedate":"%s"}' %(hostname, localip, localtype, physicalm, freem, cpuidle, freedisk, \
                container, updatedate)
        try:
            client.set(key, value)
            logger.info("=" * 50)
            logger.info(u"线程设置键%s，值%s成功" % (key, value))
            logger.info("=" * 50)
        except:
            logger.error("=" * 50)
            logger.error(u"线程设置键%s，值%s失败" %(key, value))
            logger.error("=" * 50)
        time.sleep(5)  # 每隔5秒收集一次


if __name__ == "__main__":
    result = initetcd()  # 初始化etcd
    if not result:
        logger.error(u'etcd服务器%s无法连接' % etcd)
        exit(1)
    logger.info(u"程序开始运行，初始化完成")
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        # 启动线程，用于收集系统信息
        key = '/node' + '/' + localtype + '-' + localip + '/systeminfo'
        t = threading.Thread(target=getsysteminfo, args=(key, client, ))
        t.setDaemon(True)  # 设置主线程退出后，子线程一并退出
        t.start()
        basekey = '/node' + '/' + localtype + '-' + localip
        while True:
            result = client.read(basekey)
            for i in result.children:
                if "deploy" in i.key:  # 部署
                    deployvalue = str(i.value)
                    logger.info(u"开始部署%s项目" % deployvalue)
                    deployvalue = eval(deployvalue)  # 把获取的json字符转换成字典
                    pjname = deployvalue.get("pjname")
                    port = deployvalue.get("port")
                    replics = deployvalue.get('replics')
                    isagent = int(deployvalue.get('isagent'))

                    result = k8scheck(pjname)
                    if not result:  # 如果项目不存在
                        log = rcmbhander(pjname, replics)  # 部署rc
                        chuid = str(i.key).split("deploy-")[1]  # 取uuid
                        key = basekey + "/rclog-" + chuid
                        if log:  # 如果有返回日志
                            client.set(key, log)
                        else:
                            client.set(key, '项目%s rc已经存在！' % pjname)
                        if isagent:
                            log = sembhander(pjname, port)  # 如果启用外部访问端口，部署services
                            chuid = str(i.key).split("deploy-")[1]  # 取uuid
                            key = basekey + "/selog-" + chuid
                            if log:  # 如果有返回日志
                                client.set(key, log)
                            else:
                                client.set(key, '项目%s service已经存在！' % pjname)
                    else:  # 项目存在
                        chuid = str(i.key).split("deploy-")[1]  # 取uuid
                        rcs = checkrccount(pjname)  # 检测项目的当前复本数
                        key = basekey + "/rclog-" + chuid
                        if int(rcs) == replics:  # 如果现有的相同
                            client.set(key, '项目%s rc已经存在，并且没有改变动！' % pjname)
                        else:
                            rechar = scalerc(pjname, replics)
                            if not rechar:
                                client.set(key, '项目%s更改复本数成功，返回结果%s。' % (pjname, rechar))
                            else:
                                client.set(key, '项目%s更改复本数失败。' % (pjname))

                        key = basekey + "/selog-" + chuid
                        if isagent:  # 如果项目需要暴露外部端口
                            if int(checksecount(pjname)):  # 服务已经存在
                                oldport = int(getnodport(pjname))
                                if oldport != port:
                                    delservice(pjname)  # 删除现有se
                                    time.sleep(1)
                                    log = sembhander(pjname, port)  # 如果项目改变了端口，部署services
                                    chuid = str(i.key).split("deploy-")[1]  # 取uuid
                                    key = basekey + "/selog-" + chuid
                                    if log:  # 如果有返回日志
                                        client.set(key, log)
                                    else:
                                        client.set(key, "%s项目创建服务失败,端口%s" %(pjname, port))
                                else:
                                    client.set(key, "%s项目已存在，不需要重新创建服务" % pjname)
                            else:
                                log = sembhander(pjname, port)  # 如果不存在，部署services
                                chuid = str(i.key).split("deploy-")[1]  # 取uuid
                                key = basekey + "/selog-" + chuid
                                if log:  # 如果有返回日志
                                    client.set(key, log)
                                else:
                                    client.set(key, "%s项目创建服务失败,端口%s" % (pjname, port))
                        else:
                            if int(checksecount(pjname)):
                                delre = delservice(pjname)
                                if delre:
                                    client.set(key, '%s 删除项目%s服务成功,日志：%s' \
                                               % (time.strftime('%Y-%m-%d %H:%M:%S'), pjname, delre))
                                else:
                                    client.set(key, '%s 删除项目%s服务失败' \
                                               % (time.strftime('%Y-%m-%d %H:%M:%S'), pjname))
                            else:
                                client.set(key, '项目%s 不需要开放service！' % pjname)
                    client.delete(i.key)  # 删除部署完成的键值
            time.sleep(2)  # 每隔2秒重试一次
    except Exception, e:
        logger.error(u'etcd服务器%s无法连接' % e)
        exit(1)
