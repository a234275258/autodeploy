# coding: utf-8
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
from project.models import project, project_build
import jenkins


# 添加项目
def add_project(proname, prodesc, prosvn, certificateid, mavenpara, buildtype, username):
    try:
        project.objects.create(Pro_name=proname, Pro_desc=prodesc, svn_ip=prosvn, certificateid=certificateid, \
                               mavenpara=mavenpara, buildtype=buildtype, username=username)
        return 1
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
def update_project(id, Pro_name, Pro_desc, svn_ip, certificateid, mavenpara, buildtype, username):
    try:
        record = project.objects.get(id=id)
        record.Pro_name = Pro_name
        record.Pro_desc = Pro_desc
        record.svn_ip = svn_ip
        record.certificateid = certificateid
        record.mavenpara = mavenpara
        record.buildtype = buildtype
        record.username = username
        record.save()
        return 1
    except:
        return 0


# 添加构建
def add_project_build(Pro_id, Pro_name, builddate, success, file, svnversion, username, buildlog, buildseq):
    try:
        project_build.objects.create(Pro_id=Pro_id, Pro_name=Pro_name, builddate=builddate, success=success,\
                                     file=file, svnversion=svnversion, username=username, buildlog=buildlog, buildseq=buildseq)
        return 1
    except:
        return 0


# 获取构建的数据
def get_project_build(keyword):
    try:
        if not keyword:
            recordlist = project_build.objects.all()
        else:
            recordlist = project_build.objects.filter(Pro_name__icontains=keyword).order_by('id')
        return recordlist
    except:
        return 0


# 更新构建表
def update_project_build(id, Pro_id,  Pro_name, builddate, success, file, svnversion, username, buildseq):
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
    def createjob(self, server, jobname, desc, svnip, verifyid, mavenpara):
        try:
            server.create_job(jobname, self.config % (u'%s' % desc, svnip, verifyid, mavenpara))
            return 1
        except:
            return 0

    # 构建项目
    def bulidjob(self, server, jobname):
        try:
            try:
                last_build_number = server.get_job_info(jobname)['lastBuild']['number']
            except:
                last_build_number = 0
            server.build_job(jobname)
            while True:
                try:
                    curr_build_number = server.get_job_info(jobname)['lastBuild']['number']
                except:
                    curr_build_number = 1
                if curr_build_number > last_build_number:
                    if not server.get_build_info(jobname, curr_build_number)['building']:  # 构建完成
                        buildlog = server.get_build_console_output(jobname, curr_build_number)  # 获取构建日志
                        if server.get_build_info(jobname, curr_build_number)['result']:  # 构建结果
                            build_info = server.get_build_info(jobname, curr_build_number)
                            return 1, buildlog, build_info, curr_build_number
                        else:
                            return 0, buildlog, 0, curr_build_number
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
    def editjob(self, server, jobname, desc, svnip, verifyid, mavenpara):
        try:
            server.reconfig_job(jobname, self.config % (desc, svnip, verifyid, mavenpara))
            return 1
        except:
            return 0
