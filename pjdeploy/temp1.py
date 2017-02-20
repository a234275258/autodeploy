#!/usr/bin/env python
# coding: utf-8
import etcd
import re
import uuid

etcdip = "10.200.201.205"
etcdport = 4001

try:
    client = etcd.Client(host=etcdip, port=int(etcdport))
    basekey = '/node/'
    logdetail = ""
    result = client.read(basekey)  # 读取etcd中/node中所有的信息
    for i in result.children:  # 遍历所有信息，并按类型分别放入不同的列表中
        print i.key
        if i.dir:
            keya = str(i.key) + "/sdfsdfsd12"
            print keya
            client.set(keya, "fdffdsfdf")
            sonresult = client.read(str(i.key))
            for j in sonresult.children:
                if "log" in j.key:
                    logdetail += "+++++++++++++++++++++++++++++++++++++++++\n"
                    logdetail += str(j.key).split('/')[-1].split('-')[0]
                    logdetail += "\n+++++++++++++++++++++++++++++++++++++++++\n"
                    logdetail += j.value
                    logdetail += "\n=========================================\n"
                    # client.delete(j.key)
            client.delete(keya)
    print logdetail
except Exception, e:
    print "etcd服务器不正常%s" % e
