# coding: utf-8
from django.db import models


# Create your models here.

# 项目表
class project(models.Model):
    Pro_name = models.CharField(max_length=20, blank=False, verbose_name='项目名')
    Pro_desc = models.CharField(max_length=200, blank=False, verbose_name='项目描述')
    svn_ip = models.CharField(max_length=255, blank=False, verbose_name='svnIP地址')
    buildtype = models.CharField(max_length=30, blank=False, verbose_name='构建产物')
    username = models.CharField(max_length=50, blank=False, verbose_name='新建用户')

    def __unicode__(self):
        return u'%s' % self.Pro_name

    class Meta:
        db_table = 'project'
        verbose_name = '项目表'
        verbose_name_plural = verbose_name

# 项目构建记录表
class project_build(models.Model):
    Pro_id = models.ForeignKey(project)
    builddate = models.DateTimeField(blank=False, verbose_name='构建日期')
    success = models.BooleanField(blank=False, verbose_name='是否构建成功')
    file = models.CharField(max_length=30, blank=False, verbose_name='项目构建文件')
    username = models.CharField(max_length=50, blank=False, verbose_name='构建用户')

    def __unicode__(self):
        return u'%s' % self.Pro_id

    class Meta:
        db_table = 'project_build'
        verbose_name = '项目构建表'
        verbose_name_plural = verbose_name