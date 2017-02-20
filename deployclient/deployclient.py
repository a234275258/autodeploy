#!/bin/usr/env python
# coding: utf-8

import socket
import os
import ConfigParser
import logging.config
import etcd
import time
import commands
import sys
import threading

BASE_DIR = os.path.dirname(__file__)  # 程序目录
logging.config.fileConfig(os.path.join(BASE_DIR, "logger.conf"))  # 日志配制文件
logger = logging.getLogger("prodution")  # 取日志标签，可选为development,prodution

config = ConfigParser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'deployclient.conf'))

masterip = config.get('master', 'masterip')
masterport = config.get('master', 'masterport')

localip = config.get('local', 'localip')
localtype = config.get('local', 'localtype')
pjpath = config.get('local', 'pjpath')

etcdip = config.get('etcd', 'etcdip')  # etcd ip地址
etcdport = config.get('etcd', 'etcdport')  # etcd 端口


def checkmaster():  # 检测master是否启动文件传输
    ip = masterip
    port = masterport
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(5)
        result = s.connect_ex((ip, int(port)))
        if result == 0:
            return 1
        else:
            return 0
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


def deployproject(pjname):  # 部署模块
    if "-web" in pjname:  # web项
        stat, res = commands.getstatusoutput("docker ps -a | grep \"%s\" | \
                    grep -v 'pause' | grep -v 'Exited' | awk '{print $1}'" % (pjname))
    else:
        stat, res = commands.getstatusoutput("docker ps -a | grep  \"%s\"  | \
                            grep -v 'pause' | grep -v 'Exited' | grep -v '-web' | awk '{print $1}'" % (pjname))
    print res
    if res:
        stat, res1 = commands.getstatusoutput("docker restart %s" % (res))
        logger.info("%s部署成功" % pjname)
        return 1
    else:
        logger.info("%s项目没有运行在此node上" % pjname)
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
    result = checkmaster()  # 检测文件服务器是否有效
    if not result:
        logger.error(u"文件服务器%s无法连接" % masterip)
        sys.exit(1)

    result = initetcd()  # 初始化etcd
    if not result:
        logger.error(u'etcd服务器%s无法连接' % etcd)
        sys.exit(1)
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
            try:
                result = client.read(basekey)
                for i in result.children:
                    if "deploy" in i.key:  # 部署
                        print i.value
                        deployvalue = str(i.value)
                        deployvalue = eval(deployvalue)  # 把获取的json字符转换成字典
                        pjname = deployvalue.get("pjname")  # 获取项目名
                        sourcefile = deployvalue.get("file")  # 获取文件名
                        localfile = pjpath + '/' + pjname + '/' + pjname + '.jar'  # 本地文件名为项目路径+项目名+项目名+jar
                        print sourcefile, localfile
                        if os.path.exists(pjpath + '/' + pjname):  # 如果项目文件存在，表示已经部署过
                            if os.path.exists(localfile):
                                os.remove(localfile)
                                #os.rename(localfile,
                                          #localfile + time.strftime("%Y-%m-%d-%H:%m:%S", time.localtime()))  # 重命名
                        else:
                            os.makedirs(pjpath + '/' + pjname)  # 创建目录
                        logger.info(u"==========开始下载文件%s==============" % localfile)
                        filestat = getfile(sourcefile, localfile)  # 下载项目文件
                        if filestat:
                            logger.info(u"==========文件%s下载成功==============" % localfile)
                            result = deployproject(pjname)
                            chuid = str(i.key).split("deploy-")[1]  # 取uuid
                            key = basekey + "/nodelog-" + chuid
                            time.sleep(2)
                            print key
                            if result:  # 部署成功
                                client.set(key, "%s结点%s部署成功" % (localip, pjname))
                            else:
                                client.set(key, "%s结点没有运行%s项目" % (localip, pjname))
                        else:
                            logger.error(u"==========文件%s下载失败==============" % localfile)
                        try:
                            client.delete(i.key)
                        except Exception, e:
                            logger.error(u'删除键值%s错误' % e)
                time.sleep(2)
            except Exception, e:
                logger.error(u'etcd键值读取错误，错误代码：%s' % e)

    except Exception, e:
        logger.error(u'程序运行错误，错误代码：%s' % e)
        sys.exit(1)
