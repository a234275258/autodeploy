# coding: utf-8
from django.db import connection
from autodeploy.settings import logger
from autodeploy.settings import DBHOST
from user.models import admin, per_code, user_per, user_chpass
from autodeploy.settings import ldapconn, basedn, ldappassword, ldapcn
import ldap
import ldap.modlist as modlist
import hashlib
import uuid
import time


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


# 从数据库里面验证用户,传入用户名密码，成功返回记录，失败返回0
def dbcheckuser(username, password):
    result = admin.objects.filter(username=username, password=password)
    return result if result else 0


# 从数据中取一条记录
def get_one(username):
    try:
        record = admin.objects.get(username=username)
        return record
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
        udn = "uid=" + str(username) + ',' + basedn
        old = {'userPassword': '11111'}
        new = {'userPassword': str(password)}
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
        admin.objects.create(username=username, password=password, email=email, vaild=vaild, isadmin=isadmin,
                             logincount=0,
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


# 原生sql查询转换成字典
def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
        ]


# 重设密码表
def userpass_modify(username):
    if get_one(username):
        passuuid = str(uuid.uuid4()).replace('-', '')  # 生成uuid
        try:
            user_chpass.objects.create(username=username, passuuid=passuuid,
                                       ctime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            return passuuid
        except:
            return 0
    return 0


# 查询重置密码表
def get_resetpass(username, passuuid):
    try:
        record = user_chpass.objects.get(username=username, passuuid=passuuid)
        return record
    except:
        return 0


# 删除重置密码记录
def delete_resetpass(username, passuuid):
    try:
        user_chpass.objects.get(username=username, passuuid=passuuid).delete()
        return 1
    except:
        return 0


# 添加权限代码
def addpercode(pcode, pname):
    try:
        per_code.objects.create(Per_code=pcode, Per_name=pname)
        return 1
    except:
        return 0


# 获取权限代码表所有数据
def get_percode(keyword):
    try:
        if not keyword:
            recordlist = per_code.objects.all()
        else:
            recordlist = per_code.objects.filter(Per_name__icontains=keyword).order_by('Per_code')
        return recordlist
    except:
        return 0


# 从表中删除一条记录，传参为表名，id
def all_delete_one(tbname, id):
    try:
        id = try_int(id)
        eval(tbname).objects.get(id=id).delete()
        return 1
    except:
        return 0


# 从表中取一条记录，传参为表名，id
def all_get_one(tbname, id):
    try:
        record = eval(tbname).objects.get(id=id)
        return record
    except:
        return 0

# 更新权限代码表
def update_perone(id, pcode, pname):
    try:
        record = per_code.objects.get(id=id)
        record.Per_code = pcode
        record.Per_name = pname
        record.save()
        return 1
    except:
        return 0
