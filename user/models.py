# coding:utf-8
from django.db import models
import time


# Create your models here.


class admin(models.Model):
    id = models.AutoField(primary_key=True, null=False, verbose_name="自增ID")  # ID字段
    username = models.CharField(max_length=50, null=False, blank=False, unique=True, verbose_name="用户名")  # 用户名
    password = models.CharField(max_length=32, verbose_name="密码")  # 密码
    email = models.EmailField(verbose_name="邮箱")  # 邮箱
    vaild = models.IntegerField(null=True, default=1, verbose_name="是否有效")  # 帐号是否有效,1为正常，0为锁定
    isadmin = models.IntegerField(null=True, default=0, verbose_name="是否为管理员")  # 权限,1为管理员，0为普通会员
    logincount = models.PositiveIntegerField(null=False, default=0, verbose_name="登陆次数")  # 登录次数
    lastlogin = models.DateTimeField(verbose_name="最后一次登录时间")  # 最后登录时间

    def __str__(self):
        return "%s %s" % (username, password)

    class Meta:
        db_table = 'admin'
        verbose_name = "用户表"


def check_user(username):  # 判断用户是否已存在
    recordlist = admin.objects.filter(username=username)
    if recordlist:
        recordlist = admin.objects.get(username=username)
        recordlist.logincount += 1
        recordlist.save()
        return 1
    else:
        return 0


def add_user(username, password, email='test@enjoyfin.com', vaild=1, isadmin=0):  # 添加用户
    try:
        admin.objects.create(username=username, password=password, email=email, vaild=vaild, isadmin=isadmin, logincount=0,
                             lastlogin=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        return 1
    except:
        return 0


def update_user(username, password, email, vaild, isadmin):  # 更新用户
    try:
        obj = admin.objects.get(username=username)
        if password == '':
            obj.email = email
            obj.vaild = vaild
            obj.password = obj.password
            obj.isadmin = isadmin
        else:
            obj.password = password
            obj.email = email
            obj.vaild = vaild
            obj.isadmin = isadmin
        obj.save()
        return 1
    except:
        return 0


def get_username(username):  # 获取用户数据
    try:
        return admin.objects.get(username=username)
    except:
        return 0
