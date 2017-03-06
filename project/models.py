# coding: utf-8
from django.db import models


# Create your models here.

# 项目表
class project(models.Model):
    Pro_name = models.CharField(max_length=20, unique=True, blank=False, verbose_name='项目名')
    Pro_desc = models.CharField(max_length=200, blank=False, verbose_name='项目描述')
    Pro_port = models.CharField(max_length=5, blank=True, verbose_name='项目外部访问端口')
    svn_ip = models.CharField(max_length=255, blank=False, verbose_name='svnIP地址')
    rpcmemory = models.PositiveIntegerField(blank=False, verbose_name='rpc项目容器内存大小')
    enableweb = models.SmallIntegerField(blank=False, verbose_name='是否启用web项目')
    webmemory = models.PositiveIntegerField(blank=False, verbose_name='web项目容器内存大小')
    certificateid = models.CharField(max_length=50, blank=True, verbose_name='认证编号')
    mavenpara = models.CharField(max_length=200, blank=True, verbose_name='maven参数')
    buildtype = models.CharField(max_length=30, blank=True, verbose_name='构建产物')
    maillist = models.CharField(max_length=500, blank=True, verbose_name='邮件列表')
    scriptlist = models.CharField(max_length=500, blank=True, verbose_name='执行脚本')
    username = models.CharField(max_length=50, blank=True, verbose_name='新建用户')

    def __unicode__(self):
        return u'%s' % self.Pro_name

    class Meta:
        db_table = 'project'
        verbose_name = '项目表'
        verbose_name_plural = verbose_name


# 项目构建记录表
class project_build(models.Model):
    Pro_id = models.PositiveIntegerField(blank=False, verbose_name='项目ID')
    Pro_name = models.CharField(max_length=20, unique=True, blank=False, verbose_name='项目名')
    builddate = models.DateTimeField(blank=False, verbose_name='构建日期')
    success = models.PositiveSmallIntegerField(blank=False, verbose_name='是否构建成功0 失败 1 成功 2 构建中')
    file = models.CharField(max_length=200, blank=False, verbose_name='项目构建文件')
    fileweb = models.CharField(max_length=200, blank=False, verbose_name='web项目构建文件')
    svnversion = models.PositiveIntegerField(blank=False, default=0, verbose_name='svn版本号')
    username = models.CharField(max_length=50, blank=False, verbose_name='构建用户')
    buildlog = models.TextField(verbose_name='构建日志')
    buildseq = models.PositiveIntegerField(verbose_name='构建序号')

    def __unicode__(self):
        return u'%s' % self.Pro_id

    class Meta:
        db_table = 'project_build'
        verbose_name = '项目构建表'
        verbose_name_plural = verbose_name


# svn认证表
class svnauth(models.Model):
    svnuser = models.CharField(max_length=30, unique=True, blank=False, verbose_name='svn用户名')
    svncode = models.CharField(max_length=200, blank=False, verbose_name='认证代码')

    def __unicode__(self):
        return u'%s' % self.svnuser

    class Meta:
        db_table = 'svnauth'
        verbose_name = 'svn认证表'
        verbose_name_plural = verbose_name


# maven参数表
class mavenpara(models.Model):
    paraname = models.CharField(max_length=30, unique=True, blank=False, verbose_name='maven参数名')
    paravalue = models.CharField(max_length=200, blank=False, verbose_name='maven参数值')

    def __unicode__(self):
        return u'%s' % self.paraname

    class Meta:
        db_table = 'mavenpara'
        verbose_name = 'maven参数表'
        verbose_name_plural = verbose_name
