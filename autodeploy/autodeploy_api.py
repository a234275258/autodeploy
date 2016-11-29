# coding: utf-8
from django.db import connection
from autodeploy.settings import logger
from autodeploy.settings import DBHOST
from user.models import admin
from autodeploy.settings import ldapconn, basedn, ldappassword, basecn
import ldap

# 检测数据库是否正常
def check_db():
    try:
        conn = connection.cursor()  # 检测数据库是正常
        return 1
    except:
        logger.error('连接'+str(DBHOST)+'数据库错误')
        return 0


# 从数据库里面验证用户,传入用户名密码，成功返回1，失败返回0
def dbcheckuser(username, password):
    result = admin.objects.filter(username=username,password=password)
    if result:
        return 1
    else:
        return 0


# 从数据中取一条记录
def get_one(username):
    recordlist = admin.objects.get(username=username)
    return recordlist


def ldap_add(username, password):
    l = ldap.initialize(ldapconn)
    l.simple_bind(basecn, ldappassword)

    #cn = username + ' ' + username
    attrs = {}
    attrs['objectclass'] = ['person', 'organizationalPerson', 'inetOrgPerson', 'posixAccount']
    attrs['cn'] = username
    attrs['givenName'] = username
    attrs['homeDirectory'] = '/home/%s' % username
    attrs['loginShell'] = '/bin/bash'
    attrs['userPassword'] = '123456'
    attrs['sn'] = username
    attrs['uid'] = username
    #attrs['uidNumber'] = ldap_newuid()
    #attrs['gidNumber'] = ldap_getgid()
    attrs['active'] = 'TRUE'
    ldif = modlist.addModlist(attrs)
    l.add_s(basecn, ldif)
    l.unbind_s()
