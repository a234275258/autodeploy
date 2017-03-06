#!/bin/usr/env python
# coding: utf-8

import SocketServer
import time
import os
import ConfigParser
import logging.config
import etcd
import commands
import threading
import shutil

BASE_DIR = os.path.dirname(__file__)  # 程序目录

logging.config.fileConfig(os.path.join(BASE_DIR, "logger.conf"))  # 日志配制文件
logger = logging.getLogger("prodution")  # 取日志标签，可选为development,prodution

config = ConfigParser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'ciserver.conf'))  # 配置文件
ip = config.get('base', 'ip')  # ip地址
port = config.get('base', 'port')  # 端口
dpath = config.get('base', 'dpath')  # 项目路径

svnurl = config.get('svn', 'url')  # svn地址
pjpath = config.get('svn', 'pjpath')  # svn提交目录，需要先设置好svn配置

localip = config.get('local', 'localip')  # 本机ip
localtype = config.get('local', 'localtype')  # 本机类型

etcdip = config.get('etcd', 'etcdip')  # etcd ip地址
etcdport = config.get('etcd', 'etcdport')  # etcd 端口


class MyTcpServer(SocketServer.BaseRequestHandler):
    def recvfile(self, filename):
        dfile = dpath + '/' + filename
        logger.info(u"开始接收文件,文件名为:%s" % dfile)
        f = open(dfile, 'wb+')
        self.request.send('ready')
        while True:
            data = self.request.recv(4096)
            if data == 'EOF':
                logger.info(u"文件:%s接收成功!" % filename)
                break
            f.write(data)
        f.close()

    def sendfile(self, filename):
        logger.info(u"开始发送文件,文件名为%s, 客户端%s" % (filename, str(self.client_address)))
        self.request.send('ready')
        time.sleep(1)
        if not os.path.isfile(filename):
            time.sleep(1)
            self.request.send('EOF')
            logger.error(u"文件%s不存在" % filename)
        else:
            f = open(filename, 'rb+')
            while True:
                data = f.read(4096)
                if not data:
                    break
                self.request.send(data)
            f.close()
            time.sleep(1)
            self.request.send('EOF')
            logger.info(u"文件%s发送成功, 客户端%s" % (filename, str(self.client_address)))

    def handle(self):
        logger.info(u"来自客户端%s的连接" % str(self.client_address))
        while True:
            try:
                data = self.request.recv(4096)
                if not data:
                    logger.info(u"客户端%s终止连接" % str(self.client_address))
                    break
                else:
                    try:
                        action, filename = data.split()
                    except:
                        action = data
                        filename = ""
                    # if filename:
                    #     filename=filename.split('/')[-1]
                    if action == "put":
                        self.recvfile(filename)
                    elif action == 'get':
                        self.sendfile(filename)
                    else:
                        logger.error(u"获取数据错误")
                        continue
            except:
                logger.info(u"客户端%s已经断开连接" % str(self.client_address))
                break


def initetcd():  # 初始化etcd
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
                hostname, localip, localtype, physicalm, freem, cpuidle, freedisk, \
                container, updatedate)
        try:
            client.set(key, value)
            # logger.info("=" * 50)
            # logger.info(u"线程设置键%s，值%s成功" % (key, value))
            # logger.info("=" * 50)
        except:
            pass
            # logger.error("=" * 50)
            # logger.error(u"线程设置键%s，值%s失败" %(key, value))
            # logger.error("=" * 50)
        time.sleep(5)  # 每隔5秒收集一次


def handerfile(pjname, sourcefile, targetfile, svnversion):  # 入参为项目名，源文件，目标文件,svn版本号
    svncommitinfo = targetfile  # 取出文件名作为svn提交信息
    targetfile = "%s/%s/%s/%s" % (pjpath, pjname, svnversion, targetfile)  # 拼接目标文件路径与名称
    basepath = "%s/%s" % (pjpath, pjname)  # 项目文件路径
    versionpath = "%s/%s/%s" % (pjpath, pjname, svnversion)  # 版本路径
    try:
        if not os.path.exists(versionpath):  # 如果不存在版本目录
            if not os.path.exists(basepath):  # 如果不存在项目路径，代表项目第一次构建
                os.makedirs(versionpath)  # 创建目录，会连同项目路径一起创建
                shutil.copy(sourcefile, targetfile)
                command = """cd %s ;svn add %s; svn commit -m '%s'""" % (
                    pjpath, basepath, svncommitinfo)  # 执行命令先进入工作目录，添加基目录
                stat, res = commands.getstatusoutput(command)
                return res  # 返回命令执行log
            else:
                os.makedirs(versionpath)  # 新建项目目录
                shutil.copy(sourcefile, targetfile)
                command = """cd %s ;svn add %s; svn commit -m '%s'""" % (
                    pjpath, versionpath, svncommitinfo)  # 执行命令先进入工作目录，添加基目录
                stat, res = commands.getstatusoutput(command)
                return res  # 返回命令执行log
        else:  # 如果目录都存在了
            shutil.copy(sourcefile, targetfile)
            command = """cd %s ;svn add %s; svn commit -m '%s'""" % (
                pjpath, targetfile, svncommitinfo)  # 执行命令先进入工作目录，添加刚加入的文件，并提交svn
            stat, res = commands.getstatusoutput(command)
            return res  # 返回命令执行log
    except Exception, e:
        logger.error(u"项目%s文件复制或svn提交失败，失败代码：%s" % (pjname, e))
        return 0


def deletejenkinsworkspace(pjname, workpath):  # 删除jenkins工作空间
    try:
        if os.path.exists(workpath):
            command = """rm -rf %s""" % workpath
            stat, res = commands.getstatusoutput(command)
            logger.info("项目%s 工作区间删除成功，日志为：%s" % (pjname, "%s%s" %(command, res)))
    except Exception, e:
        logger.error(u"删除项目%s工作空间目录%s失败，错误代码：%s" % (pjname, workpath, e))
        return 0


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
        t = threading.Thread(target=getsysteminfo, args=(key, client,))
        t.setDaemon(True)  # 设置主线程退出后，子线程一并退出
        t.start()
        basekey = '/node' + '/' + localtype + '-' + localip
        while True:
            result = client.read(basekey)
            for i in result.children:
                if "commitfile" in i.key:  # 复制文件
                    logger.info("-" * 50)
                    logger.info(u"开始任务，任务信息：%s" % str(i.value))
                    commitfilevalue = str(i.value)
                    commitfilevalue = eval(commitfilevalue)  # 把获取的json字符转换成字典
                    pjname = str(commitfilevalue.get("pjname")).split('_')[0]  # 获取项目名
                    rpcsourcefile = str(commitfilevalue.get("rpcsourcefile"))  # rpc源文件名
                    websourcefile = str(commitfilevalue.get("websourcefile"))  # web源文件名
                    svnversion = int(commitfilevalue.get("svnversion"))  # 版本号
                    isweb = int(commitfilevalue.get("isweb"))  # 是否启用web项目
                    rpctargetfile = str(commitfilevalue.get("rpctargetfile"))  # rpc目标文件
                    webtargetfile = str(commitfilevalue.get("webtargetfile"))  # web目标文件
                    deletepath = commitfilevalue.get("deletepath")  # 要删除的目录，jenkins工作空间

                    result = handerfile(pjname, rpcsourcefile, rpctargetfile, svnversion)  # 复制rpc项目
                    if result:
                        logger.info("项目%s rpc项目文件复制并提并svn成功，日志为：%s" % (pjname, result))
                    if isweb:  # 开启web
                        result = handerfile(pjname, websourcefile, webtargetfile, svnversion)  # 复制web项目
                        if result:
                            logger.info("项目%s web项目文件复制并提并svn成功，日志为：%s" % (pjname, result))

                    deletejenkinsworkspace(pjname, "%s%s" % (deletepath, commitfilevalue.get("pjname")))  # 删除工作区间

                    logger.info(u"任务结束，任务信息：%s" % str(i.value))
                    logger.info("-" * 50)
                    client.delete(i.key)  # 删除复制完成的键值
            time.sleep(2)  # 每隔2秒重试一次
    except Exception, e:
        logger.error(u'etcd服务器无法连接,错误代码%s' % e)
        exit(1)
