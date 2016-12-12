#!/bin/usr/env python
# coding: utf-8

import SocketServer
import time
import os
from autodeploy.settings import logger, localipaddr, localport, PROJECTPATH

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # 程序目录
ip = localipaddr
port = localport
dpath = PROJECTPATH


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


if __name__ == "__main__":
    if not os.path.exists(dpath):
        os.makedirs(dpath)
    s = SocketServer.ThreadingTCPServer((ip, int(port)), MyTcpServer)
    try:
        s.serve_forever()
    except Exception, e:
        logger.error(e)
    finally:
        logger.error(u"程序退出")
