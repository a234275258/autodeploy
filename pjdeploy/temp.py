#!/usr/bin/env python
# coding: utf-8
import etcd
import re
import uuid

etcdip = "10.200.201.205"
etcdport = 4001


# 操作etcd函数,传入参数为项目名，文件名，端口，是否反向代理，复本数
def opetcd(proname, filename, port, isagent, replics):
    k8snode = []  # node结点列表
    k8smaster = []  # k8smaster列表
    k8sagent = []  # k8sagent列表
    result = initetcd()  # 判断etcd是否正常
    if not result:
        # logger.error(u'etcd服务器%s无法连接' % etcd)
        print "etcd服务器无法连接"
        return 0
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        basekey = '/node/'
        result = client.read(basekey)  # 读取etcd中/node中所有的信息
        for i in result.children:  # 遍历所有信息，并按类型分别放入不同的列表中
            if re.search("k8snode", i.key):
                k8snode.append(i.key)

            if re.search("k8smaster", i.key):
                k8smaster.append(i.key)

            if re.search("k8sagent", i.key):
                k8sagent.append(i.key)

        uchar = str(uuid.uuid4())  # uuid,避免重复
        if len(k8snode) > 0:
            for i in range(len(k8snode)):
                key = k8snode[i] + '/' + "deploy-" + uchar
                value = '{"pjname":"%s", "file":"%s"}' % (proname, filename)
                client.set(key, value)
        else:
            print "暂时没有node结点"

        if len(k8smaster) > 0:
            for i in range(len(k8smaster)):
                key = k8smaster[i] + '/' + "deploy-" + uchar
                value = '{"pjname":"%s", "port":"%s", "replics":"%s", "isagent":"%s"}' %(proname, port, replics, isagent)
                client.set(key, value)
        else:
            print "暂时没有master结点"

        if len(k8sagent) > 0:
            if isagent == 1:
                for i in range(len(k8sagent)):
                    key = k8sagent[i] + '/' + "deploy-" + uchar
                    value = '{"pjname":"%s", "port":"%s"}' % (proname, port)
                    client.set(key, value)
        else:
            print "暂时没有反向代理结点"
    except Exception, e:
        # logger.error(u'etcd服务器%s无法连接' % e)
        print "错误"
        exit(1)
    finally:
        k8snode = []
        k8smaster = []
        k8sagent = []


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


if __name__ == "__main__":
    opetcd('qrpuy', '/Users/chenyanghong/autodeploy/data/qrp-1/qrp-2017-01-26-11-25-29-13120.jar', 9099, 1, 3)
