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
import shutil

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

svnurl = config.get('svn', 'url')  # etcd 端口


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
                    grep -v 'pause' | grep -v 'Exited' | awk '{print $1}'" % pjname)
    else:
        stat, res = commands.getstatusoutput("docker ps -a | grep  \"%s\"  | \
                            grep -v 'pause' | grep -v 'Exited' | grep -v '-web' | awk '{print $1}'" % pjname)
    if res:
        #stat, res1 = commands.getstatusoutput("docker restart %s" % (res))  # 重启容器
        stat, res1 = commands.getstatusoutput("echo %s | xargs -I {} docker rm -f  {}" % res)  # 删除容器，让kubernetes重新拉起
        logger.info("%s部署成功" % pjname)
        return 1
    else:
        logger.info("%s项目没有运行在此node上" % pjname)
        return 0


# 获取系统信息,接收两个参数，第一个为键，第二个为etcd连接对像
def getsysteminfo(key, client):
    hostname = ""  # 主机名
    physicalm = ""  # 物理内存大小
    freem = ""  # 空闲内存
    cpuidle = ""  # 空闲cpu
    freedisk = ""  # 空闲磁盘
    container = ""  # 容器个数
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
                '"container":"%s","updatedate":"%s"}' % (
                    hostname, localip, localtype, physicalm, freem, cpuidle, freedisk,
                    container, updatedate)
        try:
            client.set(key, value)
            # logger.info("=" * 50)
            # logger.info(u"线程设置键%s，值%s成功" % (key, value))
            # logger.info("=" * 50)
        except:
            pass
            # logger.error("=" * 50)
            # logger.error(u"线程设置键%s，值%s失败" % (key, value))
            # logger.error("=" * 50)
        time.sleep(5)  # 每隔5秒收集一次


def handlerfile(sourcefile, localfile, filetype):  # 从远程下载文件到本地,入参为源文件，目标文件
    logger.info("=" * 50)
    logger.info(u"复制远程文件:%s到本地，文件名为：%s" % (sourcefile, localfile))
    logger.info("=" * 50)
    try:
        ppath = str(os.path.split(localfile)[0])  # 取出物理路径
        warpath = str(os.path.split(localfile)[1].split('.')[0]).strip()  # 取出war包对应的路径
        if os.path.exists(ppath):  # 如果项目文件存在，表示已经部署过
            if str(filetype).strip() == "war":   # 如果文件是war，需要创建logs目录
                logspath = "%s/logs" % os.path.split(ppath)[0]
                if not os.path.exists(logspath): # 如果不存在路径
                    os.makedirs(logspath)  # 创建目录
            if os.path.exists(localfile):
                os.remove(localfile)  # 删除原有文件
            if os.path.exists("%s/%s" % (ppath, warpath)):   # 如果webapps下面的跟war包相名目录存在就删除
                shutil.rmtree("%s/%s" % (ppath, warpath))
                logger.info(u'目录%s删除成功' % ("%s/%s" % (ppath, warpath)))
                # os.rename(localfile,
                # localfile + time.strftime("%Y-%m-%d-%H:%m:%S", time.localtime()))  # 重命名
        else:
            os.makedirs(ppath)  # 创建目录
            if str(filetype).strip() == "war":   # 如果文件是war，需要创建logs目录
                logspath = "%s/logs" % os.path.split(ppath)[0]
                if not os.path.exists(logspath):
                    os.makedirs(logspath)  # 创建目录

        logger.info(u"开始下载文件%s" % localfile)
        try:
            command = """svn cat %s > %s""" % (sourcefile, localfile)  # 从svn上接取文件到本地
            stat, res = commands.getstatusoutput(command)
            logger.info(u"文件%s下载成功%s" % (localfile, res))
            return 1
        except Exception, e:
            logger.error(u"文件%s下载失败,错误代码%s" % (localfile, e))
            return 0
            # filestat = getfile(sourcefile, localfile)  # 下载项目文件
            # if filestat:
            #     logger.info(u"==========文件%s下载成功==============" % localfile)
            #     return 1
            # else:
            #     logger.error(u"==========文件%s下载失败==============" % localfile)
            #     return 0
    except Exception, e:
        logger.error(u"文件%s下载失败,错误代码%s" % (localfile, e))
        return 0


if __name__ == "__main__":
    # result = checkmaster()  # 检测文件服务器是否有效,只有当web端启用本地存文件的时候才需要
    # if not result:
    #     logger.error(u"文件服务器%s无法连接" % masterip)
    #     sys.exit(1)

    result = initetcd()  # 初始化etcd
    if not result:
        logger.error(u'etcd服务器%s无法连接' % etcd)
        sys.exit(1)
    logger.info(u"程序开始运行，初始化完成")
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        # 启动线程，用于收集系统信息
        key = '/node' + '/' + localtype + '-' + localip + '/systeminfo'
        t = threading.Thread(target=getsysteminfo, args=(key, client,))
        t.setDaemon(True)  # 设置主线程退出后，子线程一并退出
        t.start()
        basekey = '/node' + '/' + localtype + '-' + localip
        while True:
            try:
                result = client.read(basekey)
                for i in result.children:
                    if "deploy" in i.key:  # 部署
                        logger.info('-' * 50)
                        logger.info(u"开始部署任务，任务的信息为%s" % str(i.value))
                        deployvalue = str(i.value)
                        deployvalue = eval(deployvalue)  # 把获取的json字符转换成字典
                        pjname = str(deployvalue.get("pjname")).split('_')[0]  # 获取项目名,并替换掉_号后面的
                        enableweb = int(deployvalue.get('enableweb'))  # 获取是否启用web
                        filetype = str(deployvalue.get('filetype'))  # 获取文件类型，为jar或war

                        # 处理rpc项目的文件
                        sourcefile = deployvalue.get("file")  # 获取文件名
                        if filetype.strip() == "jar":  # 部署为jar包
                            localfile = pjpath + '/' + pjname + '/' + pjname + '.jar'  # 本地文件名为项目路径+项目名+项目名+jar
                        else:
                            localfile = "%s/%s/webapps/%s.war" % (pjpath, pjname,
                                                                  str(sourcefile.split('/')[-1]).split('-')[0])  # war文件路径
                        rpcstat = handlerfile(sourcefile, localfile, filetype)

                        chuid = str(i.key).split("deploy-")[1]  # 取uuid，做为返回log的键使用
                        key = basekey + "/nodelog-" + chuid
                        rpcmessage = ""  # rpc项目的部署消息
                        webmessage = ""  # web项目的部署消息
                        if rpcstat:  # 文下载成功开始部署
                            result = deployproject(pjname)
                            if result:  # 部署成功
                                rpcmessage = "%s结点%s部署成功" % (localip, pjname)
                            else:
                                rpcmessage = "%s结点没有运行%s项目" % (localip, pjname)

                        # 处理web项目文件
                        if enableweb:  # 启用web项目，部署web项目
                            sourcefile = deployvalue.get("fileweb")  # 获取文件名
                            if filetype.strip() == "jar":  # 部署为jar包
                                localfile = "%s/%s-web/%s-web.jar" % (pjpath, pjname, pjname)  # 本地文件名为项目路径+项目名+项目名+jar
                            else:
                                localfile = "%s/%s-web/webapps/%s.war" % (pjpath, pjname,
                                                                          str(sourcefile.split('/')[-1]).split('-')[0])  # war文件路径
                            webstat = handlerfile(sourcefile, localfile, filetype)
                            if webstat:  # 文下载成功开始部署
                                result = deployproject("%s-web" % pjname)
                                if result:  # 部署成功
                                    webmessage = "%s结点%s部署成功" % (localip, "%s-web" % pjname)
                                else:
                                    webmessage = "%s结点没有运行%s项目" % (localip, "%s-web" % pjname)
                        else:
                            webmessage = "项目%s不需要web项目" % pjname

                        # rpc与web都已处理完毕，回写日志
                        client.set(key, "[ %s ]===[ %s ]" % (rpcmessage, webmessage))

                        logger.info(u"任务已完成，任务的信息为%s" % str(i.value))
                        logger.info('-' * 50)
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
