# coding: utf-8
from project.models import project, project_build


# 添加项目
def add_project(proname, prodesc, prosvn, buildtype):
    try:
        project.objects.create(Pro_name=proname, Pro_desc=prodesc, svn_ip=prosvn, buildtype=buildtype)
        return 1
    except:
        return 0
