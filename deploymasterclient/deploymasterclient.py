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

warrcmb = config.get('mb', 'warrcmb')  # war复本控制器模板


# 判断模块rc是否存在
def k8scheckrc(pjname):
    try:
        if pjname in '-web':
            command = """kubectl get rc  --all-namespaces | grep '%s'' | awk '{print $1":::"$2}'|head -n1""" % pjname  # 如果是web项目
        else:
            command = """kubectl get rc  --all-namespaces | grep "%s" |
            grep  -v '%s-web' | awk '{print $1":::"$2}'|head -n1 """ % (pjname, pjname)  # 返回名称空间，rc名称，用:::隔开
        stat, res = commands.getstatusoutput(command)
        if res:   # 如果有返回代表有值
            return res
        else:
            return 0
    except Exception, e:
        logger.error("项目%s在master结点获取存在失败,错误代码：%s" % (pjname, e))
        return 0


# 判断模块服务是否存在
def k8scheckse(pjname):
    try:
        if pjname in '-web':
            command = """kubectl get service --all-namespaces | grep '%s'' | awk '{print $1":::"$2}'|head -n1""" % pjname  # 如果是web项目
        else:
            command = """kubectl get service --all-namespaces | grep "%s" |
            grep  -v '%s-web' | awk '{print $1":::"$2}'|head -n1 """ % (pjname, pjname)  # 返回名称空间，rc名称，用:::隔开
        stat, res = commands.getstatusoutput(command)
        if res:   # 如果有返回代表有值
            return res
        else:
            return 0
    except Exception, e:
        logger.error("项目%s在master结点获取存在失败,错误代码：%s" % (pjname, e))
        return 0


# 检测当前复本数,容器镜像，容器内存
def checkrccount(pjname):
    try:
        current_repl = 0  # 当时复本数
        current_images = ""  # 当前镜像
        current_memory = ""  # 当前内存
        stat, res = commands.getstatusoutput(
            "kubectl get rc %s  --namespace=%s  -o yaml | grep 'replicas:' | head -n1 | awk  '{print $NF}' " % (
                pjname, kubename))  # 获取当前复本数
        current_repl = res
        if not current_repl.isdigit():  # 判断复本数是不是为数字
            current_repl = 0
        stat, res = commands.getstatusoutput(
            "kubectl get rc %s  --namespace=%s  -o yaml | grep 'image:' | awk '{print $NF}'" % (
                pjname, kubename))  # 获取当前镜像
        current_images = res
        if '/' in current_images:  # 判断镜像格式是不是正确
            current_images = 0
        stat, res = commands.getstatusoutput(
            "kubectl get rc %s  --namespace=%s-ecos  -o yaml | grep 'memory:' | awk '{print $NF}' |grep -o [0-9]" % (
                pjname, kubename))  # 获取当前内存，单位是G，作比较之前需要统一单位
        current_memory = res
        if not current_memory.isdigit():  # 判断内存是否是数字
            current_memory = 0
        else:
            current_memory = int(current_memory) * 1024  # 转化成M
        return current_repl, current_images, current_memory
    except Exception, e:
        logger.error(u"获取%s项目复本数失败，错误代码%s" % (pjname, e))
        return 0, 0, 0


# 调整rc个数
def scalerc(pjname, replicas):
    try:
        stat, res = commands.getstatusoutput(
            "kubectl scale --replicas=%s rc %s --namespace=%s" % (replicas, pjname, kubename))
        return res
    except Exception, e:
        logger.error(u'项目%s调整复本个数失败，错误代码：%s' % (pjname, e))
        return 0


# 获取项目外部暴露端口,查询没有返回为0
def getnodport(pjname, currentkube):
    try:
        stat, res = commands.getstatusoutput("kubectl get service %s --namespace=%s" % (
            pjname, currentkube))
        if "Error" in res:
            return 0
        else:
            """(kubectl get service %s --namespace=%s -o yaml | grep -i  'nodePort'| head -n1 | awk '{print $NF}') % (
                pjname, kubename)
                也可以使用这个语名获取"""
            stat, res = commands.getstatusoutput("kubectl describe service %s --namespace=%s \
                      | grep -i 'nodeport' | grep -iv 'type' | awk  '{print $3}' | awk -F '/' '{print $1}'" % (
                pjname, currentkube))
            return res
    except Exception, e:
        logger.error(u'项目%s获取外部端口失败，错误代码：%s' % (pjname, e))
        return "error"


# 模板处理函数,入参为项目名，复本数, 内存大小, 镜像名, 名称空间, 状态，create代表新部署，replace代表替换
def rcmbhander(pjname, replicas, memory, images, names, state, filetype):
    try:
        if filetype == 'jar':  # 如果是jar，选jar模板文件
            rcmbfile = os.path.join(BASE_DIR, rcmb)
        else:
            rcmbfile = os.path.join(BASE_DIR, warrcmb)  # war模板
        rcmbtemp = os.path.join(BASE_DIR, rcmb.split('.')[0] + '-' + pjname + '.yaml')
        shutil.copyfile(rcmbfile, rcmbtemp)  # 复制文件

        f = open(rcmbtemp, 'r+')  # 读取文件内容
        context = f.readlines()
        f.close()
        for i in range(len(context)):
            context[i] = context[i].replace('k8smb1', pjname)  # 替换项目名
            context[i] = context[i].replace('kube-system', names)  # 替换名称空间
            context[i] = context[i].replace('0.0.0.0:5000/test', images)  # 替换镜像
            context[i] = context[i].replace('2048', memory)  # 替换内存大小
            if re.search("replicas", context[i]):
                context[i] = re.sub('[0-9]', str(replicas), context[i])  # 替换复本数

        f = open(rcmbtemp, 'w+')  # 回写文件
        f.writelines(context)
        f.close()
        if state == "create":  # 新建
            stat, res = commands.getstatusoutput("kubectl create -f %s" % rcmbtemp)
        else:  # 替换
            stat, res = commands.getstatusoutput("kubectl replace -f %s" % rcmbtemp)
        os.remove(rcmbtemp)
        logger.info(u"%s复本已经创建，信息为%s" %(pjname, res))
        return res
    except:
        return 0


# 模板处理函数,入参为项目名，项目端口,名称空间
def sembhander(pjname, port, names):
    try:
        sembfile = os.path.join(BASE_DIR, semb)
        sembtemp = os.path.join(BASE_DIR, semb.split('.')[0] + '-' + pjname + '.yaml')
        shutil.copyfile(sembfile, sembtemp)  # 复制文件

        f = open(sembtemp, 'r+')  # 读取文件内容
        context = f.readlines()
        f.close()
        for i in range(len(context)):
            context[i] = context[i].replace('k8smb1', pjname)  # 替换项目名
            context[i] = context[i].replace('kube-system', names)  # 替换名称空间
            if re.search("9999", context[i]):
                context[i] = re.sub('9999', str(port), context[i])  # 替换复本数

        f = open(sembtemp, 'w+')  # 回写文件
        f.writelines(context)
        f.close()
        stat, res = commands.getstatusoutput("kubectl create -f %s" % (sembtemp))
        os.remove(sembtemp)
        logger.info(u"%s服务已经创建，信息为%s" % (pjname, res))
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
            # logger.error(u"线程设置键%s，值%s失败" % (key, value))
            # logger.error("=" * 50)
        time.sleep(5)  # 每隔5秒收集一次


#  删除rc，se,返回删除日志,传参为项目名，名称空间，标志可选为rc或service
def deleterc(pjname, kubename , dflag):
    command = """kubectl delete %s %s --namespace=%s""" % (dflag, pjname, kubename)
    stat, res = commands.getstatusoutput(command)
    if res:
        return res
    else:
        return 0


"""项目不存在，新部署,入参为项目名，端口,复本数，rpc内存大小，是否启用web，,web复本数，web项目内存大小，
镜像，名称空间，基键值,etcd键值名,部署类型，是否启用反向代理，etcd client实例，没有返回值，所有异常都已在模块中处理"""


def newdeploy(pjname, port, replics, rmemory, enableweb, replicsweb, wmemory, dimages,
              kubename, basekey, key, filetype, isagent, client):
    # 开始处理rpc项目
    rpcmessage = rcmbhander(pjname, replics, rmemory, dimages, kubename, 'create', filetype)  # 部署rc
    chuid = str(key).split("deploy-")[1]  # 取uuid
    key = basekey + "/rclog-" + chuid
    if not rpcmessage:
        rpcmessage = ('项目%s 在master节点部署失败，请检查master节点设置！' % pjname)

    # 开始处理web项目
    webmessage = ""
    if enableweb:  # 有web项目需要部署
        webmessage = rcmbhander("%s-web" % pjname, replicsweb, wmemory, dimages,
                                kubename, 'create', filetype)  # 部署web-rc
        if not webmessage:
            webmessage = ('项目%s 在master节点部署失败，请检查master节点设置！' % "%s-web" % pjname)
    client.set(key, '[ %s ]==[ %s ]' % (rpcmessage, webmessage))  # 设置键值

    key = basekey + "/selog-" + chuid  # 服务的日志的键名
    if isagent:
        if enableweb:  # web项目启用
            log = sembhander("%s-web" % pjname, port, kubename)  # 如果启用外部访问端口,又有web项目，部署services
            if log:  # 如果有返回日志
                client.set(key, log)
            else:
                client.set(key, '项目%s 在master节点部署service失败，请检查master节点设置！' % "%s-web" % pjname)
        else:  # rpc项目，没有启用web项目，但又启用了反向代理，为rpc项目建立服务
            log = sembhander(pjname, port, kubename)  # 如果启用外部访问端口,rpc项目，部署services
            if log:  # 如果有返回日志
                client.set(key, log)
            else:
                client.set(key, '项目%s 在master节点部署service失败，请检查master节点设置！' % pjname)
    else:  # 不需要反向代理
        client.set(key, '项目%s 不需要创建服务！' % pjname)


"""已在存项目重新部署，入参为项目名，端口,复本数，rpc内存大小，是否启用web，,web复本数，web项目内存大小，
镜像，名称空间，基键值,etcd键值名,部署类型，是否启用反向代理，etcd client实例，resultrpc为rpc是否有rc,
resultweb检测web是否有rc，servicerpc检测rpc是否有服务，serviceweb检测web是否有服务没有返回值，
所有异常都已在模块中处理"""


def olddeploy(pjname, port, replics, rmemory, enableweb, replicsweb, wmemory, dimages,
              kubename, basekey, key, filetype, isagent, client,
              resultrpc, resultweb, servicerpc, serviceweb):
    chuid = str(key).split("deploy-")[1]  # 取uuid
    key = basekey + "/rclog-" + chuid  # 键名称
    rpcmessage = ""  # rpc项目部署日志
    webmessage = ""  # web项目部署日志
    # 处理rpc项目
    if resultrpc:  # 确保resultrpc不为0, 为0的话代表没有rpc rc需要重新部署
        current_kubename = str(resultrpc).strip().split(":::")[0]  # rpc项目当前名称空间
        current_repl, current_image, current_memory = checkrccount(pjname)  # 检测项目的当前复本数,内存，镜像
        if int(current_memory) == int(rmemory) and current_image.strip() == dimages.strip() \
                and int(current_repl) == int(replics) and current_kubename == str(kubename):  # 如果当前内存，镜像，副本数都相同
            rpcmessage = ('项目%s rc复本数，内存，镜像,名称空间均与现有相同，并且没有改变动！' % pjname)
        elif int(current_memory) == int(rmemory) and current_image.strip() == dimages.strip() \
                and current_kubename == str(kubename) and int(current_repl) != int(replics):  # 如果当前内存，镜像相同,只有复本数不同
            rpcmessage = scalerc(pjname, replics)  # 调整rc个数
            if not rpcmessage:
                rpcmessage = ('项目%s 在master节点重新调整复本数失败，想要调成复本：%s个！' % (pjname, replicsweb))
        else:  # 重新部署
            rcdellog = deleterc(pjname, current_kubename, "rc")  # 删除rc
            rpcmessage = rcmbhander(pjname, replics, rmemory, dimages, kubename, 'create', filetype)  # 部署rc
            if rcdellog:
                rpcmessage = "%s==%s" % (rcdellog, rpcmessage)  # 拼接日志
            if not rpcmessage:
                rpcmessage = ('项目%s 在master节点重新部署失败，请检查master节点设置！' % pjname)
    else:  # 重新部署
        rpcmessage = rcmbhander(pjname, replics, rmemory, dimages, kubename, 'create', filetype)  # 部署rc
        if not rpcmessage:
            rpcmessage = ('项目%s 在master节点重新部署失败，请检查master节点设置！' % pjname)

    # 处理web项目
    if enableweb:
        if resultweb:  # 确保resultweb不为0, 为0的话代表没有rpc rc需要重新部署
            current_kubename = str(resultweb).strip().split(":::")[0]  # web项目当前名称空间
            current_repl, current_image, current_memory = checkrccount("%s-web" % pjname)  # 检测web项目
            if int(current_memory) == int(wmemory) and current_image.strip() == dimages.strip() \
                    and current_kubename == str(kubename) and int(current_repl) == int(replicsweb):  # 如果当前项目的内存，镜像，复本数都一样
                webmessage = ('项目%s 不需要部署重新部署，内存，镜像，复本数都与当前一致！' % "%s-web" % pjname)
            elif int(current_memory) == int(wmemory) and current_image.strip() == dimages.strip() \
                    and current_kubename == str(kubename) and int(current_repl) != int(replicsweb):  # 如果当前内存，镜像相同,只有复本数不同
                webmessage = scalerc("%s-web" % pjname, replicsweb)  # 调整rc个数
                if not webmessage:
                    webmessage = ('项目%s 在master节点重新调整复本数失败，想要调成复本：%s个！' % ("%s-web" % pjname, replicsweb))
            else:  # 重新部署
                rcdellog = deleterc("%s-web" % pjname, current_kubename, "rc")  # 删除rc
                webmessage = rcmbhander("%s-web" % pjname, replicsweb, wmemory, dimages,
                                        kubename, 'create', filetype)  # 部署web-rc
                if rcdellog:
                    webmessage = "%s==%s" % (rcdellog, webmessage)  # 拼接日志
        else:
            # 重新部署
            webmessage = rcmbhander("%s-web" % pjname, replicsweb, wmemory, dimages, kubename, 'create', filetype)  # 部署rc
            if not webmessage:
                webmessage = ('项目%s 在master节点重新部署失败，请检查master节点设置！' % "%s-web" % pjname)
    else:
        webmessage = ('项目%s 不需要部署web项目！' % pjname)
    client.set(key, '[ %s ]==[ %s ]' % (rpcmessage, webmessage))  # 设置键值

    # 处理service
    key = basekey + "/selog-" + chuid   # 服务日志键值
    if isagent:

        if enableweb:  # web项目
            if servicerpc == 0 and serviceweb == 0:  # 原来没有rpc服务且web没有服务
                log = sembhander("%s-web" % pjname, port, kubename)  # 如果启用外部访问端口,又有web项目，部署services
                if log:  # 如果有返回日志
                    client.set(key, "项目%s部署服务日志:%s" % ("%s-web" % pjname, log))
                else:
                    client.set(key, "%s项目创建服务失败,端口%s" % ("%s-web" % pjname, port))
            elif servicerpc and serviceweb == 0:  # rpc的service存在，先删除rpc，再创建web
                current_kubename = str(servicerpc).strip().split(":::")[0]  # rpc项目服务当前名称空间
                rcdellog = deleterc(pjname, current_kubename, "service")  # 删除se
                log = sembhander("%s-web" % pjname, port, kubename)  #部署web项目，services
                if log:  # 如果有返回日志
                    client.set(key, "项目%s删除服务日志:%s,重新部署日志:%s" % (pjname, rcdellog, log))
                else:
                    client.set(key, "项目%s创建服务失败,端口%s" % ("%s-web" % pjname, port))
            else:  # web项目服务已存在
                current_kubename = str(serviceweb).strip().split(":::")[0]  #  web项目服务当前名称空间
                oldport = int(getnodport("%s-web" % pjname, current_kubename))  # 查询web端口
                if int(oldport) == int(port):  # 原端口跟现有端口相同
                    client.set(key, '项目%s 原端口%s,现端口%s相同，不需要部署' % ("%s-web" % pjname, oldport, port))
                else:  # 重新创建服务
                    rcdellog = deleterc("%s-web" % pjname, current_kubename, "service")  # 删除现有se
                    time.sleep(1)
                    log = sembhander("%s-web" % pjname, port, kubename)  # 如果启用外部访问端口,又有web项目，部署services
                    if log:  # 如果有返回日志
                        client.set(key, "项目%s删除服务日志:%s,重新部署日志:%s" % ("%s-web" % pjname, rcdellog, log))
                    else:
                        client.set(key, "项目%s创建服务失败,端口%s" % ("%s-web" % pjname, port))

        else:  # 没有web服务要部署
            if servicerpc == 0 and serviceweb == 0:  # 原来没有rpc服务且web没有服务
                log = sembhander(pjname, port, kubename)  # 部署rpc项目服务
                if log:  # 如果有返回日志
                    client.set(key, "项目%s重新部署日志:%s" % (pjname, log))
                else:
                    client.set(key, "%s项目创建服务失败,端口%s" % (pjname, port))
            elif servicerpc == 0 and serviceweb:   # rpc不存在web存在，先删除web再部rpc
                current_kubename = str(serviceweb).strip().split(":::")[0]  # rpc项目服务当前名称空间
                webdellog = deleterc("%s-web" % pjname, current_kubename, "service")  # 删除web se
                log = sembhander(pjname, port, kubename)  # 部署rpc项目服务
                if log:  # 如果有返回日志
                    client.set(key, "项目%s删除服务日志:%s,重新部署日志:%s" % ("%s-web" % pjname,webdellog, log))
                else:
                    client.set(key, "%s项目创建服务失败,端口%s" % ("%s-web" % pjname, port))
            else:  # 本身就存在rpc项目服务
                current_kubename = str(servicerpc).strip().split(":::")[0]  # rpc项目服务当前名称空间
                oldport = int(getnodport(pjname, current_kubename))  # 查询rpc端口
                if int(oldport) == int(port):  # 原端口跟现有端口相同
                    client.set(key, '项目%s 原端口%s,现端口%s相同，不需要部署' % (pjname, oldport, port))
                else:  # 重新创建服务
                    rcdellog = deleterc(pjname, current_kubename, "service")  # 删除现有se
                    time.sleep(1)
                    log = sembhander(pjname, port, kubename)  # 部署 rpc services
                    if log:  # 如果有返回日志
                        client.set(key, "项目%s删除服务日志:%s,重新部署日志:%s" % (pjname, rcdellog, log))
                    else:
                        client.set(key, "项目%s创建服务失败,端口%s" % (pjname, port))

    else:  # 不需要反向代理
        clearlog = ""  # 清除以前服务日志
        if servicerpc:  # rpc项目先前有服务
            current_kubename = str(servicerpc).strip().split(":::")[0]  # rpc项目服务当前名称空间
            rcdellog = deleterc(pjname, current_kubename, "service")  # 删除现有se
            clearlog = "%s%s" % (clearlog, rcdellog)  # 日志拼接

        if serviceweb:  # web项目先前有服务
            current_kubename = str(serviceweb).strip().split(":::")[0]  # rpc项目服务当前名称空间
            rcdellog = deleterc("%s-web" % pjname, current_kubename, "service")  # 删除现有se
            clearlog = "%s%s" % (clearlog, rcdellog)  # 日志拼接

        if not clearlog:  # 如果清除日志为空，代表以前都没有rpc服务与web服务
            clearlog = "项目%s不需要启用反向代理，原本没有创建过服务，不需要删除服务！" % pjname
            client.set(key, '%s' % clearlog)
        else:
            client.set(key, '项目%s不需要启用反向代理,原有服务已被删除，日志为：%s！' % (pjname, clearlog))


if __name__ == "__main__":
    if not os.path.exists("/usr/bin/kubectl"):
        logger.error(u'kubernetes未安装' % etcd)
        exit(1)
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
                if "deploy" in i.key:  # 部署
                    deployvalue = str(i.value)
                    logger.info("=" * 50)
                    logger.info(u"开始部署%s项目" % deployvalue)
                    deployvalue = eval(deployvalue)  # 把获取的json字符转换成字典
                    pjname = str(deployvalue.get("pjname")).split('_')[0]  # 把项目名用_分隔，并使用最前段
                    port = deployvalue.get("port")
                    replics = deployvalue.get('replics')  # rpc复本数
                    replicsweb = deployvalue.get('replicsweb')  # web复本数
                    rmemory = deployvalue.get('rmemory')  # rpc项目内存大小
                    wmemory = deployvalue.get('wmemory')  # web项目内存大小
                    enableweb = int(deployvalue.get('enableweb'))  # 是否启用web项目
                    isagent = int(deployvalue.get('isagent'))  # 是否反向代理
                    hander = deployvalue.get("hander")  # 控制字符
                    kubename = deployvalue.get("kubename")  # 名称空间
                    dimages = deployvalue.get("dimages")  # docker镜像
                    filetype = deployvalue.get("filetype")  # 部署类型，jar或war

                    resultrpc = k8scheckrc(pjname)    # 检测rpc项目是否存在，如果存在返回其名称空间，rc名称
                    resultweb = k8scheckrc("%s-web" % pjname)  # 检测web项目是否存在，如果存在返回其名称空间，rc名称

                    servicerpc = k8scheckse(pjname) # 检测rpc服务是否存在，如果存在返回其名称空间，服务名称
                    serviceweb = k8scheckse("%s-web" % pjname)  # 检测web项目是否存在，如果存在返回其名称空间，服务名称
                    if str(hander) == "remove":  # 处理动作为删除
                        log = deleterc(pjname)  # 删除rc,se
                        chuid = str(i.key).split("deploy-")[1]  # 取uuid
                        key = basekey + "/rclog-" + chuid
                        if log:
                            client.set(key, log)
                        else:
                            client.set(key, '%s模块没有运行' % pjname)  # 设置键值
                    else:  # 添加操作
                        if resultrpc == 0 and resultweb == 0 and servicerpc == 0 and serviceweb == 0:  # 如果项目不存在
                            newdeploy(pjname, port, replics, rmemory, enableweb, replicsweb, wmemory,
                                      dimages, kubename, basekey, i.key, filetype, isagent, client)
                        else:  # 项目存在的情况处理 =======
                            olddeploy(pjname, port, replics, rmemory, enableweb, replicsweb, wmemory,
                                      dimages, kubename, basekey, i.key, filetype, isagent, client,
                                      resultrpc, resultweb, servicerpc, serviceweb)
                    logger.info(u"完成部署%s项目" % deployvalue)
                    logger.info("=" * 50)
                    client.delete(i.key)  # 删除部署完成的键值
            time.sleep(2)  # 每隔2秒重试一次
    except Exception, e:
        logger.error(u'etcd服务器%s无法连接' % e)
        exit(1)
