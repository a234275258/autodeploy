# coding: utf-8
from pjdeploy.models import pjdeploy, pjrollback
from autodeploy.settings import etcdip, etcdport,logger
from django.db import connection
import etcd


def initetcd():  # 检测etcd是否正常
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        basekey = '/node/'  # 从node目录查找
        try:
            client.get(basekey)  # 如果key存在
        except:
            pass
        return 1
    except:
        return 0


# 获取nginx主机名跟ip地址
def get_nginx():
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        basekey = '/node/'
        result = client.read(basekey)
        rlist = []
        for i in result.children:
            if i.dir and "k8sagent" in i.key:  # 读取子值为目录与k8sagent包含在子键名中的键
                cresult = client.read(i.key)
                for j in cresult.children:
                    if "system" in j.key:
                        sysifno = str(j.value)
                        sysifno = eval(sysifno)
                        try:
                            hostinfo = {"hostname":sysifno.get("hostname"), "ip":sysifno.get("ip")}

                        except:
                            hostinfo = {}  # 代表没有机器
                        rlist.append(hostinfo)
        return rlist
    except Exception, e:
        logger.error(u"获取nginx主机、IP信息出错，错误信息：%s" % e)
        return 0


# 获取node结点主机名跟ip地址
def get_node():
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        basekey = '/node/'
        result = client.read(basekey)
        rlist = []
        for i in result.children:
            if i.dir and "k8snode" in i.key:  # 读取子值为目录与k8snode包含在子键名中的键
                cresult = client.read(i.key)
                for j in cresult.children:
                    if "system" in j.key:
                        sysifno = str(j.value)
                        sysifno = eval(sysifno)
                        try:
                            hostinfo = {"hostname": sysifno.get("hostname"), "ip": sysifno.get("ip")}

                        except:
                            hostinfo = {}  # 代表没有机器
                        rlist.append(hostinfo)
        return rlist
    except Exception, e:
        logger.error(u"获取node结点主机、IP信息出错，错误信息：%s" % e)
        return 0


# 添加项目部署
def pjdeploy_table_add(Pro_name, version, comment, Publish_time, replicas, isagent, proport, file, success, username,
                       deploylog, enableweb, replicasweb, fileweb, rmemory, wmemory,
                       dimages, kubename, agentxy, agentm, nodem):
    try:
        pjdeploy.objects.create(Pro_name=Pro_name, version=version, comment=comment, Publish_time=Publish_time,
                                replicas=replicas, isagent=isagent, proport=proport, file=file, success=success,
                                username=username, deploylog=deploylog, enableweb=enableweb,
                                replicasweb=replicasweb, fileweb=fileweb, rmemory=rmemory,
                                wmemory=wmemory, dimages=dimages, kubename=kubename, agentxy=agentxy,
                                agentm=agentm, nodem=nodem)
        return 1
    except:
        return 0


# 添加回退
def pjrollbackadd(Pro_name, current_version, old_version, current_file, old_file, comment,
                  Publish_time, success, rollbacklog, username, enableweb, current_webfile, old_webfile):
    try:
        pjrollback.objects.create(Pro_name=Pro_name, current_version=current_version,
                                  old_version=old_version, current_file=current_file,
                                  old_file=old_file, comment=comment,
                                  Publish_time=Publish_time, success=success,
                                  rollbacklog=rollbacklog, username=username, enableweb=enableweb,
                                  current_webfile=current_webfile, old_webfile=old_webfile)
        return 1
    except:
        return 0


# 根据uuid获取部署记录
def get_onepjdeploy(uchar):
    try:
        recordlist = pjdeploy.objects.filter(deploylog__icontains=uchar)
        return recordlist
    except:
        return 0


# 更新日导
def modify_logpjdeploy(uchar, logdetail):
    try:
        record = pjdeploy.objects.get(deploylog=uchar)
        record.deploylog = logdetail
        record.success = 1  # 代表成功
        record.save()
        return 1
    except:
        return 0


# 根据uuid获取回退记录
def get_onerollback(uchar):
    try:
        recordlist = pjrollback.objects.filter(rollbacklog__icontains=uchar)
        return recordlist
    except:
        return 0

# 更新日导
def modify_pjrollback(uchar, logdetail):
    try:
        record = pjrollback.objects.get(rollbacklog=uchar)
        record.rollbacklog = logdetail
        record.success = 1  # 代表成功
        record.save()
        return 1
    except:
        return 0


# 获取部署数据
def get_pjdeploy(keyword):
    try:
        if not keyword:
            recordlist = pjdeploy.objects.all().order_by('-id')
        else:
            recordlist = pjdeploy.objects.filter(Pro_name__icontains=keyword).order_by('-id')
        return recordlist
    except:
        return 0


# 获取回退数据
def get_pjrollback(keyword):
    try:
        if not keyword:
            recordlist = pjrollback.objects.all().order_by('-id')
        else:
            recordlist = pjrollback.objects.filter(Pro_name__icontains=keyword).order_by('-id')
        return recordlist
    except:
        return 0


# 更新部署表
def update_pjdeploy(id, replicas, isagent, proport, comment, username, uchar, success, \
                    Publish_time, replicasweb, rmemory, wmemory,
                    dimages, kubename, agentxy, agentm, nodem):
    try:
        record = pjdeploy.objects.get(id=id)
        record.replicas = replicas
        record.isagent = isagent
        record.proport = proport
        record.comment = comment
        record.username = username
        record.deploylog = uchar
        record.success = success
        record.Publish_time = Publish_time
        record.replicasweb = replicasweb
        record.rmemory = rmemory
        record.wmemory = wmemory
        record.dimages = dimages
        record.kubename = kubename
        record.agentxy = agentxy
        record.agentm = agentm
        record.nodem = nodem
        record.save()
        return 1
    except:
        return 0


# 更新回退表
def update_rollback(id, comment, username):
    try:
        record = pjrollback.objects.get(id=id)
        record.comment = comment
        record.username = username
        #record.Publish_time = Publish_time
        record.save()
        return 1
    except:
        return 0


# 获取部署表信息
def get_pjdeploy_per():
    try:
        cur = connection.cursor()
        cur.execute(
            "select  Pro_name,file,version,Publish_time,enableweb,fileweb from pjdeploy where id in (select max(id) from pjdeploy group by Pro_name )")
        record = cur.fetchall()
        return record
    except:
        return 0


# 获取回退表中相应项目的最新回退信息
def get_pjrollback_per(Pro_name):
    try:
        cur = connection.cursor()
        cur.execute("select Pro_name, old_version, old_file, Publish_time, old_webfile from pjrollback where id=(select max(id) from pjrollback where Pro_name='%s') and success=1" % Pro_name)
        record = cur.fetchall()
        return record
    except:
        return 0
