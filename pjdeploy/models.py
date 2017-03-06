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
    rmemory = models.PositiveIntegerField(blank=False, default=0, verbose_name='rpc项目内存大小')
    isagent = models.PositiveSmallIntegerField(blank=False, verbose_name='是否反向代理')
    proport = models.PositiveIntegerField(blank=False, default=0, verbose_name='项目端口')
    file = models.CharField(max_length=200, blank=False, verbose_name='部署rpc项目文件')
    enableweb = models.PositiveSmallIntegerField(blank=False, verbose_name='是否启用web项目')
    replicasweb = models.PositiveIntegerField(blank=False, default=0, verbose_name='web项目复本数')
    wmemory = models.PositiveIntegerField(blank=False, default=0, verbose_name='web项目内存大小')
    fileweb = models.CharField(max_length=200, blank=False, verbose_name='部署web项目文件')
    dimages = models.CharField(max_length=200, blank=False, verbose_name='docker镜像')
    kubename = models.CharField(max_length=80, blank=False, verbose_name='kubenetes名称空间')
    agentxy = models.CharField(max_length=20, blank=False, verbose_name='反向代理协议')
    agentm = models.CharField(max_length=200, blank=False, verbose_name='反向代理机器')
    nodem = models.CharField(max_length=200, blank=False, verbose_name='后端负载机器')
    success = models.PositiveSmallIntegerField(blank=False, verbose_name='是否部署成功 1 成功 2 部署中')
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
    current_file = models.CharField(max_length=200, blank=False, verbose_name='rpc项目当前文件')
    old_file = models.CharField(max_length=200, blank=False, verbose_name='rpc回退历史文件')
    enableweb = models.PositiveSmallIntegerField(blank=False, verbose_name='是否启用web项目')
    current_webfile = models.CharField(max_length=200, blank=False, verbose_name='web项目当前文件')
    old_webfile = models.CharField(max_length=200, blank=False, verbose_name='web回退历史文件')
    comment = models.CharField(max_length=500, blank=False, verbose_name="回退原因")
    Publish_time = models.DateTimeField(blank=False, verbose_name="回退时间")
    success = models.PositiveSmallIntegerField(blank=False, verbose_name='1 成功 2 部署中')
    username = models.CharField(max_length=50, blank=False, verbose_name="操作用户")
    rollbacklog = models.TextField(verbose_name='回退日志')

    class Meta:
        db_table = "pjrollback"
        verbose_name = "项目回退"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Pro_name


# docker镜像表
class dockerimages(models.Model):
    dname = models.CharField(max_length=50, unique=True, blank=False, verbose_name="镜像名称")
    durl = models.CharField(max_length=200, unique=True, blank=False, verbose_name="镜像路径")

    class Meta:
        db_table = "dockerimages"
        verbose_name = "docker镜像"
        verbose_name_plural = verbose_name


# kubernetes名称空间
class kubenamespace(models.Model):
    kname = models.CharField(max_length=50, unique=True, blank=False, verbose_name="空间名称")
    kvalue = models.CharField(max_length=200, blank=False, verbose_name="空间名称")

    class Meta:
        db_table = "kubenamespace"
        verbose_name = "kubernetes名称空间"
        verbose_name_plural = verbose_name

