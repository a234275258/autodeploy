#!/bin/usr/env python
# coding: utf-8

import socket
import os
import ConfigParser
import logging.config
import etcd
import time

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


if __name__ == "__main__":
    result = initetcd()  # 初始化etcd
    if not result:
        logger.error(u'etcd服务器%s无法连接' % etcd)
        exit(1)
    logger.info(u"程序开始运行，初始化完成")
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        basekey = '/node' + '/' + localtype + '-' + localip
        while True:
            result = client.read(basekey)
            for i in result.children:
                if i.dir:  # 子项为目录
                    subresult = client.read(i.key)
                    if "deploy" in i.key:   # 部署
                        print i.key
                        for project in subresult.children:
                            targetfile = project.value  # 服务器文件名
                            localfile = pjpath+'/'+str(os.path.split(project.key)[1])+'/'+str(os.path.split(project.key)[1])+'.'+str(project.value.split('.')[-1])  # 本地文件名为项目路径+项目名+项目名+服务器文件名扩展名
                            print targetfile, localfile
                            filestat = getfile(targetfile, localfile)  # 下载项目文件
                            if filestat:
                                print "开始部署模块"
            time.sleep(1)


    except Exception,e:
        logger.error(u'etcd服务器%s无法连接' %e)
        exit(1)
