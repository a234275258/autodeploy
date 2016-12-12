# coding: utf-8
from pjdeploy.models import pjdeploy, pjrollback


# 添加项目部署
def pjdeploy_table_add(Pro_name, version, comment, Publish_time, replicas, isagent, file, success, username, deploylog):
    try:
        pjdeploy.objects.create(Pro_name=Pro_name, version=version, comment=comment, Publish_time=Publish_time, \
                                replicas=replicas, isagent=isagent, file=file, success=success, username=username, \
                                deploylog=deploylog)
        return 1
    except:
        return 0
