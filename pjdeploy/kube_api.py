# coding: utf-8
from pjdeploy.models import dockerimages, kubenamespace


# 添加docker镜像
def adddockerimages(dname, durl):
    try:
        dockerimages.objects.create(dname=dname, durl=durl)
        return 1
    except:
        return 0


# 根据dname查询docker镜像地址，id
def get_dockerimages(keyword):
    try:
        if not keyword:
            recordlist = dockerimages.objects.all()
        else:
            recordlist = dockerimages.objects.filter(dname__icontains=keyword).order_by('id')
        return recordlist
    except:
        return 0


# 更新docker镜像表
def update_dockerimages(id, dname, durl):
    try:
        record = dockerimages.objects.get(id=id)
        record.dname = dname
        record.durl = durl
        record.save()
        return 1
    except:
        return 0


# 添加kube名称
def addkubenamespace(kname, kvalue):
    try:
        kubenamespace.objects.create(kname=kname, kvalue=kvalue)
        return 1
    except:
        return 0


# 根据描述查询kube名称
def get_kubenamespace(keyword):
    try:
        if not keyword:
            recordlist = kubenamespace.objects.all()
        else:
            recordlist = kubenamespace.objects.filter(kname__icontains=keyword).order_by('id')
        return recordlist
    except:
        return 0


# 更新docker镜像表
def update_kubenamespace(id, kname, kvalue):
    try:
        record = dockerimages.objects.get(id=id)
        record.kname = kname
        record.kvalue = kvalue
        record.save()
        return 1
    except:
        return 0