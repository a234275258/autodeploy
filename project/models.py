# coding: utf-8
from django.db import models


# Create your models here.

# 项目表
class project(models.Model):
    Pro_name = models.CharField(max_length=20, unique=True, blank=False, verbose_name='项目名')
    Pro_desc = models.CharField(max_length=200, blank=False, verbose_name='项目描述')
    svn_ip = models.CharField(max_length=255, blank=False, verbose_name='svnIP地址')
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
    success = models.BooleanField(blank=False, verbose_name='是否构建成功')
    file = models.CharField(max_length=200, blank=False, verbose_name='项目构建文件')
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
