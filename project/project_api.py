# coding: utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from project.models import project, project_build, svnauth, mavenpara
import jenkins
import time
from autodeploy.settings import logger, etcdip, etcdport
import etcd
from pjdeploy.pjdeploy_api import initetcd
import uuid


"""在etcd中添加文件复制记录,入参为项目名，rpc源文件，rpc目标文件，web源文件，web目标文件
   删除工作区间目录，是否启用wb项目，svn版本号
"""


def etcdfilecopy(pjname, rpcsourcefile, websourcefile, rpctargetfile, webtargetfile,
                 deletepath, isweb, svnversion):
    k8sjenkins = []  # jenkins结点列表
    key = ""  # 初始键值为空
    result = initetcd()
    if not result:
        logger.error(u'etcd服务器%s无法连接' % etcd)
        return 0
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        basekey = '/node/'
        result = client.read(basekey)  # 读取etcd中/node中所有的信息
        for i in result.children:  # 遍历所有信息，并按类型分别放入不同的列表中
            if "k8sjenkins" in str(i.key):  # 查询是k8sjenkins的键
                k8sjenkins.append(i.key)

        if len(k8sjenkins) > 0:  # 如果存在k8sjenkins节点
            for i in range(len(k8sjenkins)):
                uchar = str(uuid.uuid4())  # uuid,避免重复
                key = k8sjenkins[i] + '/' + "commitfile-" + uchar
                """值规则：项目名，rpc源文件，rpc目标文件，web源文件, web目标文件
                删除工作区间目录，是否启用wb项目，svn版本号"""
                value = '{"pjname":"%s", "rpcsourcefile":"%s", "websourcefile":"%s", \
                "rpctargetfile":"%s", "webtargetfile":"%s", "deletepath":"%s", \
                "isweb":"%s", "svnversion":"%s"}' \
                        % (pjname, rpcsourcefile, websourcefile, rpctargetfile, webtargetfile,
                           deletepath, isweb, svnversion)
                client.set(key, value)
        else:
            logger.info(u"暂时没有jenkins结点")
            return 0
        return 1
    except Exception, e:
        logger.error(u"文件复制键值%s写入etcd失败，错误代码：%s" %(key, e))
        return 0


# 添加项目
def add_project(proname, prodesc, proport, prosvn, certificateid, mavenpara,
                buildtype, username, maillist, scriptlist, enableweb, rpcmemory, webmemory):
    try:
        project.objects.create(Pro_name=proname, Pro_desc=prodesc, Pro_port=proport, svn_ip=prosvn,
                               certificateid=certificateid, mavenpara=mavenpara,buildtype=buildtype,
                               username=username, maillist=maillist, scriptlist=scriptlist,
                               enableweb=enableweb, rpcmemory=rpcmemory, webmemory=webmemory)
        return 1
    except:
        return 0


# 获取项目端口
def get_projectport(pjname):
    try:
        record = project.objects.get(Pro_name=pjname)
        return record.Pro_port
    except:
        return 0


# 获取项目的构建成功的svn版本号
def get_projectsvn(pjname):
    try:
        record = project_build.objects.filter(Pro_name=pjname).filter(success=1).order_by('-builddate').values(
            'svnversion')
        return record
    except:
        return 0


# 获取项目对应svn号的构建成功文件
def get_projectfile(pjname, svnversion):
    try:
        record = project_build.objects.filter(Pro_name=pjname).filter(svnversion=svnversion).filter(success=1).order_by(
            '-builddate').values(
            'file', 'fileweb')[:1]
        return record
    except:
        return 0


# 获取项目数据
def get_project(keyword):
    try:
        if not keyword:
            recordlist = project.objects.all()
        else:
            recordlist = project.objects.filter(Pro_name__icontains=keyword).order_by('id')
        return recordlist
    except:
        return 0


# 更新项目表
def update_project(id, Pro_name, Pro_desc, Pro_port, svn_ip, certificateid, mavenpara,
                   buildtype, username, maillist, scriptlist, enableweb, rpcmemory, webmemory):
    try:
        record = project.objects.get(id=id)
        record.Pro_name = Pro_name
        record.Pro_desc = Pro_desc
        record.Pro_port = Pro_port
        record.svn_ip = svn_ip
        record.certificateid = certificateid
        record.mavenpara = mavenpara
        record.buildtype = buildtype
        record.maillist = maillist
        record.scriptlist = scriptlist
        record.username = username
        record.enableweb = enableweb
        record.rpcmemory = rpcmemory
        record.webmemory = webmemory
        record.save()
        return 1
    except:
        return 0


# 添加构建
def add_project_build(Pro_id, Pro_name, builddate, success,
                      file, svnversion, username, buildlog, buildseq):
    try:
        project_build.objects.create(Pro_id=Pro_id, Pro_name=Pro_name, builddate=builddate,
                                     success=success, file=file, svnversion=svnversion,
                                     username=username, buildlog=buildlog, buildseq=buildseq)
        return 1
    except Exception, e:
        logger.info(u"%s项目添加建构写数据库失败，失败代码：%s" % e)
        return 0


# 获取构建的数据
def get_project_build(keyword):
    try:
        if not keyword:
            recordlist = project_build.objects.all().order_by('-id')
        else:
            recordlist = project_build.objects.filter(Pro_name__icontains=keyword).order_by('-id')
        return recordlist
    except:
        return 0


# 更新构建表
def update_project_build(id, Pro_id, Pro_name, builddate, success, file, svnversion, username, buildseq):
    try:
        record = project_build.objects.get(id=id)
        record.Pro_id = Pro_id
        record.Pro_name = Pro_name
        record.builddate = builddate
        record.success = success
        record.file = file
        record.svnversion = svnversion
        record.username = username
        record.buildseq = buildseq
        record.save()
        return 1
    except:
        return 0


# 添加svn用户
def addsvnuser(svnuser, svncode):
    try:
        svnauth.objects.create(svnuser=svnuser, svncode=svncode)
        return 1
    except:
        return 0


# 获取svn认证表所有数据
def get_svnauth(keyword):
    try:
        if not keyword:
            recordlist = svnauth.objects.all()
        else:
            recordlist = svnauth.objects.filter(svnuser__icontains=keyword).order_by('svnuser')
        return recordlist
    except:
        return 0


# 根据svncode查询svn名称，id
def get_svnauthname(keyword):
    try:
        if not keyword:
            return 0
        else:
            recordlist = svnauth.objects.get(svnuser=keyword)
        return recordlist
    except:
        return 0


# 更新svn认证表
def update_svnauth(id, svnuser, svncode):
    try:
        record = svnauth.objects.get(id=id)
        record.svnuser = svnuser
        record.svncode = svncode
        record.save()
        return 1
    except:
        return 0


# 添加maven参数表
def addmavenpara(paraname, paravalue):
    try:
        mavenpara.objects.create(paraname=paraname, paravalue=paravalue)
        return 1
    except:
        return 0


# 获取maven参数表所有数据
def get_mavenpara(keyword):
    try:
        if not keyword:
            recordlist = mavenpara.objects.all()
        else:
            recordlist = mavenpara.objects.filter(paraname__icontains=keyword).order_by('paraname')
        return recordlist
    except:
        return 0


# 根据paraname查询maven参数名，id
def get_mavenhname(keyword):
    try:
        if not keyword:
            return 0
        else:
            recordlist = mavenpara.objects.get(paraname=keyword)
        return recordlist
    except:
        return 0


# 更新maven参数表表
def update_mavenpara(id, paraname, paravalue):
    try:
        record = mavenpara.objects.get(id=id)
        record.paraname = paraname
        record.paravalue = paravalue
        record.save()
        return 1
    except:
        return 0


# 定义jenkins类
class jenkins_tools(object):
    # 构造函数
    def __init__(self, url, username, password, config):
        self.url = url
        self.username = username
        self.password = password
        self.config = config

    # 创建jenkins服务器
    def createserver(self):
        try:
            server = jenkins.Jenkins(self.url, self.username, self.password)
            return server
        except:
            return 0

    # 创建一个job， 传入jenkins实例，项目名，描述，svn信息，验证信息
    def createjob(self, server, jobname, desc, svnip, verifyid, mavenpara, maillist, scriptlist):
        try:
            server.create_job(jobname, self.config % (u'%s' % desc, svnip, verifyid, mavenpara, maillist, scriptlist))
            return 1
        except Exception, e:
            logger.error(u'%s' % e)
            return 0

    # 构建项目
    def bulidjob(self, server, jobname):
        try:
            curr_build_number = 0  # 当前构建序列初始为0
            try:
                tempdi = server.get_job_info(jobname)  # 获取项目的信息
                if "number" in tempdi["lastBuild"]:
                    last_build_number = int(tempdi['lastBuild']['number'])  # 如果从来没有构建过
                else:
                    last_build_number = 0
            except:
                last_build_number = 0
            server.build_job(jobname)  # 开始构建
            while True:  # 检测本次构建是否完成
                while True:
                    try:
                        time.sleep(1)
                        tempdi = server.get_job_info(jobname)
                        if "number" in tempdi["lastBuild"]:
                            curr_build_number = int(tempdi['lastBuild']['number'])
                            if curr_build_number > last_build_number:
                                break  # 如果已完成则退出循环
                    except:
                        pass
                if not server.get_build_info(jobname, curr_build_number)['building']:  # 构建完成
                    buildlog = server.get_build_console_output(jobname, curr_build_number)  # 获取构建日志
                    if str(server.get_build_info(jobname, curr_build_number)['result']) == "SUCCESS":  # 构建结果
                        build_info = server.get_build_info(jobname, curr_build_number)
                        return 1, buildlog, build_info, curr_build_number
                    else:
                        build_info = server.get_build_info(jobname, curr_build_number)
                        return 0, buildlog, build_info, curr_build_number
        except:
            return 0, 0, 0, 0

    # 删除项目
    def deletejob(self, server, jobname):
        try:
            server.delete_job(jobname)
            return 1
        except:
            return 0

    # 修改项目
    def editjob(self, server, jobname, desc, svnip, verifyid, mavenpara, maillist, scriptlist):
        try:
            server.reconfig_job(jobname, self.config % (desc, svnip, verifyid, mavenpara, maillist, scriptlist))
            return 1
        except:
            return 0
