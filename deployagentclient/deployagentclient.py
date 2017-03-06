#!/bin/usr/env python
# coding: utf-8

import socket
import os
import ConfigParser
import logging.config
import etcd
import time
import re
import commands
import shutil
import threading

BASE_DIR = os.path.dirname(__file__)  # 程序目录
logging.config.fileConfig(os.path.join(BASE_DIR, "logger.conf"))  # 日志配制文件
logger = logging.getLogger("prodution")  # 取日志标签，可选为development,prodution

config = ConfigParser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'deployagentclient.conf'))

masterip = config.get('master', 'masterip')
masterport = config.get('master', 'masterport')

localip = config.get('local', 'localip')
localtype = config.get('local', 'localtype')

etcdip = config.get('etcd', 'etcdip')  # etcd ip地址
etcdport = config.get('etcd', 'etcdport')  # etcd 端口

httpmb = config.get('mb', 'httpmb')  # nginx http代理模板文件

tcpmb = config.get('mb', 'tcpmb')  # nginx tcp代理模板文件

nginxhttpconf = config.get('local', 'nginxhttpconf')  # nginx http代理配制文件路径

nginxtcpconf = config.get('local', 'nginxtcpconf')  # nginx tcp代理配制文件路径

nginxscript = config.get('nginxscript', 'nginxscript')  # nginx 启动脚本


# 添加upstream,入参为基本upstream配置，upstream IP地址列表个数，端口，返回处理好的列表
def addupstream(basechar, upstreamiplen, port, upstreamip):
    upstreamlist = []
    for i in range(upstreamiplen):
        tempstr = str(basechar).replace("15105", str(port))
        tempstr = tempstr.replace('baseip', upstreamip[i])
        upstreamlist.append(tempstr)
    return upstreamlist


# 检测nginx目前项目的端口,入参为配制文件名，端口，返回结果1代表项目端口跟现有要重新部署一致，0为不一致，需要重新部署
def checkport(filename, port):
    f = open(filename, 'r+')
    content = f.readlines()
    f.close()
    for i in range(len(content)):
        if str(port) in content[i]:   # 如果想要判断严格，可以再加Listen in
            return 1
    return 0


# 处理nginx部署，传参项目名，端口，代理协议，后端代理 返回值为0或部署日志
def nginxhander(pjname, port, agentxy, nodem):
    if agentxy == "http":
        filename = nginxhttpconf + '/' + pjname + '.conf'
        if os.path.exists(nginxtcpconf + '/' + pjname + '.conf'):  # 项目以前是tcp代理,这次为http
            os.remove(nginxtcpconf + '/' + pjname + '.conf')  # 删除文件
    else:
        filename = nginxtcpconf + '/' + pjname + '.conf'
        if os.path.exists(nginxhttpconf + '/' + pjname + '.conf'):  # 项目以前是http代理,这次为tcp
            os.remove(nginxhttpconf + '/' + pjname + '.conf')  # 删除文件
    if os.path.exists(filename):  # 如果配置文件已存在
        result = checkport(filename, port)   # 检测以前的端口是不是跟现有的端口一样，如果一样就不重新部署
        if not result:
            return nginxdeploy(filename, port, agentxy, nodem)  # 重新部署
        else:
            return 0
    else:
        return nginxdeploy(filename, port, agentxy, nodem)


def nginxdeploy(filename, port, agentxy, nodem):  # 处理nginx部署，传入文件名，端口, 协议，后端负载服务器
    if agentxy == "tcp":
        mbfile = os.path.join(BASE_DIR, "tcpmb.conf")
    else:
        mbfile = os.path.join(BASE_DIR, "httpmb.conf")
    httpmbtemp = filename
    shutil.copyfile(mbfile, httpmbtemp)  # 复制文件
    f = open(httpmbtemp, 'r+')  # 读取文件内容
    nodemtemp = nodem.split('|')  # 把后端负载机器列表使用|分开并组成列表
    upstreamiplen = len(nodemtemp)
    context = f.readlines()
    f.close()
    upstreamconf = ""  # upstream配置
    upstreamindex = 0  # upstream配置项在列表中的索引号
    for i in range(len(context)):
        context[i] = context[i].replace('mb', pjname)  # 替换项目
        if "baseip" in context[i]:
            upstreamconf = context[i]
            upstreamindex = i
        if re.search("15105", context[i]):
            context[i] = str(context[i]).replace("15105", str(port))  # 替换端口
    upstreamlist = addupstream(upstreamconf, upstreamiplen, port, nodemtemp)  # 返回处理好的upstream列表
    context.remove(context[upstreamindex])  # 先移除列表中已有的
    for i in upstreamlist:  # 把处理好的列表插入到content列表中
        context.insert(upstreamindex, i)
        upstreamindex = + 1
    f = open(httpmbtemp, 'w+')  # 回写文件
    f.writelines(context)
    f.close()

    stat, res = commands.getstatusoutput("%s configtest" % nginxscript)  # 检测配置文件是否正确
    if "successful" in res:  # 如果检测成功
        stat, res = commands.getstatusoutput("%s reload" % nginxscript)  # 重新加载配置文件
        return res
    else:
        return res


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
            # logger.info("=" * 50)
            # logger.info(u"线程设置键%s，值%s成功" % (key, value))
            # logger.info("=" * 50)
        except:
            pass
            # logger.error("=" * 50)
            # logger.error(u"线程设置键%s，值%s失败" %(key, value))
            # logger.error("=" * 50)
        time.sleep(5)  # 每隔5秒收集一次


def removeproj(pjname):  # 删除模块的反向代理,返回执行结果
    for i in [nginxhttpconf, nginxhttpconf]:  # 遍历这两个目录，如发现有项目名开头的配置文件，就移除
        for j in [pjname, "%s-web" % pjname]: # rpc或web项目
            filename = "%s/%s.conf" %(i, j)
            if os.path.exists(filename):  # 如果配置文件已存在
                os.remove(filename)
                stat, res = commands.getstatusoutput("%s configtest" % nginxscript)  # 检测配置文件是否正确
                if "successful" in res:  # 如果检测成功
                    stat, res = commands.getstatusoutput("%s reload" % nginxscript)  # 重新加载配置文件
                    return res
                else:
                    return res
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
        t = threading.Thread(target=getsysteminfo, args=(key, client, ))
        t.setDaemon(True)  # 设置主线程退出后，子线程一并退出
        t.start()
        basekey = '/node' + '/' + localtype + '-' + localip
        while True:
            result = client.read(basekey)
            for i in result.children:
                if "deploy" in i.key:  # 部署
                    logger.info("-" * 50)
                    logger.info(u"开始任务，任务信息：%s" % str(i.value))
                    deployvalue = str(i.value)
                    deployvalue = eval(deployvalue)  # 把获取的json字符转换成字典
                    pjname = str(deployvalue.get("pjname")).split('_')[0]  # 获取项目名
                    enableweb = int(deployvalue.get("enableweb"))  # 是否启用web
                    hander = deployvalue.get("hander")  # 控制字符
                    agentxy = deployvalue.get("agentxy")  # 代理协议
                    nodem = deployvalue.get("nodem")  # 后端负载服务器，使用|隔开
                    if hander == "remove":  # 控制字符为删除 
                        handermessage = removeproj(pjname)  # 删除项目反向代理
                        chuid = str(i.key).split("deploy-")[1]  # 取uuid
                        key = basekey + "/nginxlog-" + chuid
                        if handermessage:
                            client.set(key, handermessage)
                        else:
                            client.set(key, '项目%s没有开启反向代理' % pjname)
                    else:  # 新增或修改反向代理
                        if enableweb:
                            pjname = "%s-web" % pjname
                        port = deployvalue.get("port")
                        logger.info("=" * 50)
                        logger.info("开始部署项目名%s,端口为%s的项目" %(pjname, port))
                        log = nginxhander(pjname, port, agentxy, nodem)  # 参数为项目名、端口、代理协议、后端代理
                        chuid = str(i.key).split("deploy-")[1]  # 取uuid
                        key = basekey + "/nginxlog-" + chuid
                        if log:  # 如果有返回日志
                            client.set(key, log)
                        else:
                            client.set(key, '项目%s已经在nginx上有部署,并且代理端口也相同，无需重新部署。' % pjname)
                        time.sleep(2)
                        stat, res = commands.getstatusoutput("/usr/sbin/ss -tna | grep %s" % port)  # 端口是否有监听
                        logger.info("项目端口%s监听状态%s" %(port, res))
                        logger.info("项目名%s,端口为%s部署执行完成" % (pjname, port))
                        logger.info("=" * 50)
                    logger.info(u"任务结束，任务信息：%s" % str(i.value))
                    logger.info("-" * 50)
                    client.delete(i.key)  # 删除部署完成的键值
            time.sleep(2)  # 每隔2秒重试一次
    except Exception, e:
        logger.error(u'etcd服务器%s无法连接' % e)
        exit(1)
