# coding: utf-8
from django.db import models


# Create your models here.

# 项目部署表
class pjdeploy(models.Model):
    Pro_name = models.CharField(max_length=50, blank=False, verbose_name="项目名称")
    version = models.PositiveIntegerField(blank=False, default=0, verbose_name='svn版本号')
    comment = models.CharField(max_length=500, blank=False, verbose_name="发布原因")
    Publish_time = models.DateTimeField(blank=False, verbose_name="部署时间")
    replicas = models.PositiveIntegerField(blank=False, default=0, verbose_name='复本数')
    isagent = models.BooleanField(blank=False, verbose_name='是否反向代理')
    file = models.CharField(max_length=200, blank=False, verbose_name='部署文件')
    success = models.BooleanField(blank=False, verbose_name='是否部署成功0 失败 1 成功 2 部署中')
    username = models.CharField(max_length=50, blank=False, verbose_name="操作用户")
    deploylog = models.TextField(verbose_name='部署日志')

    class Meta:
        db_table = "pjdeploy"
        verbose_name = "项目部署"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Pro_name


# 项目回退表
class pjrollback(models.Model):
    Pro_name = models.CharField(max_length=50, blank=False, verbose_name="项目名称")
    current_version = models.PositiveIntegerField(blank=False, default=0, verbose_name='当前svn版本号')
    old_version = models.PositiveIntegerField(blank=False, default=0, verbose_name='回退svn版本号')
    current_file = models.CharField(max_length=200, blank=False, verbose_name='项目当前文件')
    old_file = models.CharField(max_length=200, blank=False, verbose_name='回退历史文件')
    comment = models.CharField(max_length=500, blank=False, verbose_name="回退原因")
    Publish_time = models.DateTimeField(blank=False, verbose_name="回退时间")
    success = models.BooleanField(blank=False, verbose_name='是否回退成功0 失败 1 成功 2 部署中')
    username = models.CharField(max_length=50, blank=False, verbose_name="操作用户")
    rollbacklog = models.TextField(verbose_name='回退日志')

    class Meta:
        db_table = "pjrollback"
        verbose_name = "项目回退"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Pro_name


