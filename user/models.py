# coding:utf-8
from django.db import models


# Create your models here.

# 用户表
class admin(models.Model):
    id = models.AutoField(primary_key=True, null=False, verbose_name="自增ID")  # ID字段
    username = models.CharField(max_length=50, null=False, blank=False, unique=True, verbose_name="用户名")  # 用户名
    password = models.CharField(max_length=32, verbose_name="密码")  # 密码
    email = models.EmailField(verbose_name="邮箱")  # 邮箱
    vaild = models.IntegerField(null=True, default=1, verbose_name="是否有效")  # 帐号是否有效,1为正常，0为锁定
    isadmin = models.IntegerField(null=True, default=0, verbose_name="是否为管理员")  # 权限,1为管理员，0为普通会员
    logincount = models.PositiveIntegerField(null=False, default=0, verbose_name="登陆次数")  # 登录次数
    lastlogin = models.DateTimeField(verbose_name="最后一次登录时间")  # 最后登录时间

    def __unicode__(self):
        return "%s %s" % (self.username, self.password)

    class Meta:
        db_table = 'admin'
        verbose_name = "用户表"
        verbose_name_plural = verbose_name


# 用户权限表
class user_per(models.Model):
    Per_user = models.CharField(max_length=50, blank=False, verbose_name='用户名')
    Per_code = models.CharField(max_length=5, blank=False, verbose_name="权限代码")
    comment = models.CharField(max_length=255, blank=True, null=True, verbose_name='备注')

    def __unicode__(self):
        return "%s" % (self.Per_user)

    class Meta:
        db_table = 'user_per'
        verbose_name = "用户权限表"
        verbose_name_plural = verbose_name


# 权限代码表
class per_code(models.Model):
    Per_code = models.CharField(max_length=5, blank=False, verbose_name="权限代码")
    Per_name = models.CharField(max_length=50, blank=False, verbose_name="权限名")

    class Meta:
        db_table = "per_code"
        verbose_name = "权限代码表"
        verbose_name_plural = verbose_name

# 重置密码表
class user_chpass(models.Model):
    username = models.CharField(max_length=50, blank=False, verbose_name='用户名')
    passuuid = models.CharField(max_length=32, blank=False, verbose_name='uuid')
    ctime = models.DateTimeField(blank=False, verbose_name='更改时间')

    class Meta:
        db_table = 'user_chpass'
        verbose_name = "重置密码表"
        verbose_name_plural = verbose_name

