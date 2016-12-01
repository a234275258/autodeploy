# coding: utf-8
from django.db import connection
from autodeploy.settings import logger
from autodeploy.settings import DBHOST
from user.models import admin
from autodeploy.settings import ldapconn, basedn, ldappassword, ldapcn
import ldap
import ldap.modlist as modlist
import hashlib


# 检测数据库是否正常
def check_db():
    try:
        conn = connection.cursor()  # 检测数据库是正常
        return 1
    except:
        logger.error(u'连接%s数据库错误' % DBHOST)
        return 0


# 检测用户是否登陆，并判断权限
def is_login(request):
    try:
        username = request.session.get('username', False)
        isadmin = request.session.get('isadmin', False)
    except:
        logger.error(u'连接%s数据库错误' % DBHOST)
        return 0
    if not username:
        return 0
    if not isadmin:  # 普通用户
        return 3
    if username and isadmin:  # 管理员
        return 2


# md5加密
def chartomd5(password):
    if len(password) == 0:
        return 0
    temp = hashlib.md5()
    temp.update(password)
    return temp.hexdigest()



# 从数据库里面验证用户,传入用户名密码，成功返回1，失败返回0
def dbcheckuser(username, password):
    result = admin.objects.filter(username=username, password=password)
    if result:
        return 1
    else:
        return 0


# 从数据中取一条记录
def get_one(username):
    try:
        recordlist = admin.objects.get(username=username)
        return recordlist
    except:
        return 0


# 从数据库中删除一条记录
def delete_one(username):
    try:
        admin.objects.get(username=username).delete()
        return 1
    except:
        return 0


# ldap添加用户,传入用户名密码
def ldap_add(username, password):
    try:
        l = ldap.initialize(ldapconn)
        l.simple_bind(ldapcn, ldappassword)
        udn = "uid=" + username + ',' + basedn
        attrs = {}  # 参数字典
        attrs['objectclass'] = ['posixAccount', 'inetOrgPerson', 'organizationalPerson', 'person']
        attrs['cn'] = username
        attrs['homeDirectory'] = '/home/%s' % username
        attrs['loginShell'] = '/bin/bash'
        attrs['userPassword'] = password
        attrs['sn'] = username
        attrs['uid'] = username
        uid, gid = ldap_search()
        if uid == 0:  # 如果查询出现异常，直接返回
            return 0
        attrs['uidNumber'] = str(uid)
        attrs['gidNumber'] = str(gid)
        ldif = modlist.addModlist(attrs)
        l.add_s(udn, ldif)  # 使用udn值添加帐号
        l.unbind_s()
        return 1
    except:
        return 0


# ldap删除用户,传入用户名
def ldap_delete(username):  # 删除用户
    try:
        l = ldap.initialize(ldapconn)
        l.simple_bind(ldapcn, ldappassword)
        udn = "uid=" + username + ',' + basedn
        l.delete_s(udn)
        l.unbind_s()
        return 1
    except:
        return 0


# ldap搜索所有用户，无传入参数
def ldap_search():  # 查询最大的UID,GID
    try:
        l = ldap.initialize(ldapconn)
        l.simple_bind(ldapcn, ldappassword)
        searchScope = ldap.SCOPE_SUBTREE
        searchFilter = "uid=*"
        resultID = l.search(basedn, searchScope, searchFilter, None)
        result_set = []
        while 1:
            result_type, result_data = l.result(resultID, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
        uidlist = []  # UID列表
        gidlist = []  # GID列表
        for i in result_set:
            uidlist.append(i[0][1]["uidNumber"][0])
            gidlist.append(i[0][1]["gidNumber"][0])
        umax = max(uidlist)  # 目前最大的UID
        gmax = max(gidlist)  # 目前最大的GID
        l.unbind_s()
        return int(umax) + 1, gmax
    except:
        return 0, 0


# ldap修改用户密码
def ldap_mpasswrod(username, password):  # 修改ldap用户密码
    try:
        l = ldap.initialize(ldapconn)
        l.simple_bind_s(ldapcn, ldappassword)
        udn = "uid=" + username + ',' + basedn
        old = {'userPassword': '11111'}
        new = {'userPassword': password}
        ldif = modlist.modifyModlist(old, new)
        l.modify_s(udn, ldif)
        l.unbind()
        return 1
    except:
        return 0


# 获取所有数据
def get_alldata(keyword):
    try:
        if not keyword:
            recordlist = admin.objects.all()
        else:
            recordlist = admin.objects.filter(username__icontains=keyword).order_by('username')
        return recordlist
    except:
        return 0


# 强制转换页码为整数,以免出现页码错误,当出现异常返回为1
def try_int(args):
    try:
        return int(args)
    except:
        return 1
