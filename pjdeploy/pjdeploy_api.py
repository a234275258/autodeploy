# coding: utf-8
from pjdeploy.models import pjdeploy, pjrollback
from django.db import connection


# 添加项目部署
def pjdeploy_table_add(Pro_name, version, comment, Publish_time, replicas, isagent, proport, file, success, username,
                       deploylog):
    try:
        pjdeploy.objects.create(Pro_name=Pro_name, version=version, comment=comment, Publish_time=Publish_time, \
                                replicas=replicas, isagent=isagent, proport=proport, file=file, success=success,
                                username=username, \
                                deploylog=deploylog)
        return 1
    except:
        return 0


# 添加回退
def pjrollbackadd(Pro_name, current_version, old_version, current_file, old_file, comment, Publish_time, success,
                  rollbacklog, username):
    try:
        pjrollback.objects.create(Pro_name=Pro_name, current_version=current_version, \
                                  old_version=old_version, current_file=current_file, \
                                  old_file=old_file, comment=comment, \
                                  Publish_time=Publish_time, success=success, rollbacklog=rollbacklog, username=username)
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
            recordlist = pjdeploy.objects.all()
        else:
            recordlist = pjdeploy.objects.filter(Pro_name__icontains=keyword).order_by('id')
        return recordlist
    except:
        return 0


# 获取回退数据
def get_pjrollback(keyword):
    try:
        if not keyword:
            recordlist = pjrollback.objects.all()
        else:
            recordlist = pjrollback.objects.filter(Pro_name__icontains=keyword).order_by('id')
        return recordlist
    except:
        return 0


# 更新部署表
def update_pjdeploy(id, replicas, isagent, proport, comment, username, uchar, success, Publish_time):
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
            "select  Pro_name,file,version,Publish_time from pjdeploy where id in (select max(id) from pjdeploy group by Pro_name )")
        record = cur.fetchall()
        return record
    except:
        return 0


# 获取回退表中相应项目的最新回退信息
def get_pjrollback_per(Pro_name):
    try:
        cur = connection.cursor()
        cur.execute("select Pro_name, old_version, old_file, Publish_time from pjrollback where id=(select max(id) from pjrollback where Pro_name='%s') and success=1" % Pro_name)
        record = cur.fetchall()
        return record
    except:
        return 0
