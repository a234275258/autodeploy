# coding:utf-8
from django.shortcuts import render
from autodeploy.settings import TITLE, ldapconn, basedn
from autodeploy.settings import logger
from django.http import HttpResponse, HttpResponseRedirect
from user.models import check_user, add_user, get_username, update_user
from autodeploy.autodeploy_api import check_db, dbcheckuser, get_one, ldap_add, ldap_mpasswrod, ldap_search, ldap_delete
import ldap
import hashlib

# Create your views here.


# window.history.go(-1),也可以使用window.history.back()
message = '''
    <script>alert("%s"); </script>
    <script language="javascript">
        window.history.back();
    </script>
'''


def login(request):  # 登录页面
    if request.session.get('username', False):  # 如果已登录,直接跳转
        response = HttpResponseRedirect('/index/')
        return response
    cname = TITLE
    return render(request, 'login.html', locals())


def is_username(username, password, email='test@enjoyfin.com', valid=1, isadmin=0):  # 检测用户并添加用户
    if not check_user(username):  # 如果用户不否存在
        temp = hashlib.md5()
        temp.update(password)
        if add_user(username, temp.hexdigest(), email, valid, isadmin):  # 添加用户记录
            return 0
        else:
            return 0
    else:
        return 1


def checklogin(request):  # 登录检测
    if request.method == "POST":
        username = request.POST['username'].encode('utf-8')
        password = request.POST['password'].encode('utf-8')
        try:
            udn = "uid=" + username + "," + basedn
            conn = ldap.initialize(ldapconn)
            try:
                conn.simple_bind_s(udn, password)
                if not check_db():  # 检测数据库是否正常,前提条件是ldap已成功认证
                    return HttpResponse(message % '数据库连接失败')
                is_username(username, password)  # 检测用户并添加用户，这里可以忽略函数返回值
                recordlist = get_one(username)
                if recordlist:
                    request.session['isadmin'] = recordlist.isadmin  # 设置session
                request.session['username'] = username  # 设置session
                request.session.set_expiry(3600)
                response = HttpResponseRedirect('/index/')
                return response
            except:
                return HttpResponse(message % '用户名或密码不存在')
        except:
            logger.error('连接' + ldapconn + '服务器连接失败')
            temp = hashlib.md5()
            temp.update(password)
            if not dbcheckuser(username, temp.hexdigest()):  # ldap连接错误，进行数据库认证
                return HttpResponse(message % '用户名或密码不存在')

            request.session['username'] = username  # 设置session
            request.session.set_expiry(3600)
            response = HttpResponseRedirect('/index/')
            return response

            #return HttpResponse(message % 'ldap服务器连接失败')
        return HttpResponse(message % '用户名密码错误')  # 如果都没有通过直接返回用户名密码错误
    elif request.method == "GET":
        return HttpResponse(message % '此网页不支持GET方法')


def user_add(request):  # 添加用户
    cname = TITLE
    if request.method == "POST":
        username = request.POST['username'].encode('utf-8')
        password = request.POST['password'].encode('utf-8')
        email = request.POST['email'].encode('utf-8')
        valid1 = request.POST['extra'].encode('utf-8')
        isadmin = request.POST['role'].encode('utf-8')
        if not (username and password and email and (valid1 not in [0, 1]) and (isadmin not in [0, 1])):
            return render(request, 'adduser.html', {'cname': cname, 'message': '输入错误，请重新输入'})
        result = is_username(username, password, email, valid1, isadmin)  # 检测用户并添加用户
        result_ldap = ldap_add(username, password)
        if not result_ldap:
            logger.error(username + "ldap添加失败")
        if result and result_ldap:
            message1 = username + '添加成功'
            return render(request, 'adduser.html', {'cname': cname, 'message': message1})
        else:
            message1 = username + '添加失败'
            return render(request, 'adduser.html', {'cname': cname, 'message': message1})

    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if username and isadmin:
        return render(request, 'adduser.html', locals())
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


def user_list():
    pass


def user_edit(request):  # 修改用户
    cname = TITLE
    currusername = request.session.get('username', False)  # 检测是否登录
    if not currusername:
        response = HttpResponseRedirect('/login/')  # 没有登录就返回
        return response

    if request.method == 'GET':
        geturl_username = request.GET.get('username', '')  # 获取用户名
        isadmin = request.session.get('isadmin', False)
        if geturl_username and (not isadmin):   # 如果可以取到数据并且不是管理员就拒绝
            return HttpResponse(message % '你没有操作此项目的权限')

        if not geturl_username and (not currusername):
            response = HttpResponseRedirect('/index/')  # 没有获取到就返回主页
            return response
        else:
            if geturl_username:
                userinfo = get_username(geturl_username)
            else:
                userinfo = get_username(currusername)
            if userinfo:
                email = userinfo.email
                currentisadmin = userinfo.isadmin
                if geturl_username:
                    dict1 = {'cname': cname, 'username': geturl_username, 'email': email, 'isadmin': isadmin, 'currentisadmin': currentisadmin}
                    return render(request, 'eidtuser.html', dict1)
                else:
                    dict1 = {'cname': cname, 'username': currusername, 'email': email, 'isadmin': isadmin, 'currentisadmin': currentisadmin}
                    return render(request, 'eidtuser.html', dict1)
            else:
                return HttpResponse(message % '用户不存在')
    else:  # post方法
        username = request.POST['username'].encode('utf-8')
        password = request.POST['password'].encode('utf-8')
        email = request.POST['email'].encode('utf-8')
        valid1 = request.POST['extra'].encode('utf-8')
        try:    # 如果页面不存在权限标签代表不是管理员
            isadmin = request.POST['role'].encode('utf-8')
        except:
            isadmin = 0

        result = 1  # 执行状态
        result_ldap = 0  #ldap执行状态
        if isadmin:    # 如果是管理员就多传一个权限位给生成的页面
            dinfo = {'cname': cname, 'username': username, 'password': password, 'email': email, 'isadmin': isadmin}
        else:
            dinfo = {'cname': cname, 'username': username, 'password': password, 'email': email}
        if password == "GT1aQi1hLvnt8Q":  # 如果密码为这个值代表没有修改过
            if not (username and password and email and (valid1 not in [0, 1])):
                return render(request, 'eidtuser.html', dinfo)
            result = update_user(username, '', email, valid1, isadmin)
        else:
            temp = hashlib.md5()
            temp.update(password)
            result = update_user(username, temp.hexdigest(), email, valid1, isadmin)
            result_ldap = ldap_mpasswrod(username, password)  # 修改ldap密码,修改结果请看日志文件

        if not result_ldap:
            logger.error(username + '用户ldap密码修改失败')
        if result and result_ldap:
            dm = {'message': '更新成功'}
            return render(request, 'eidtuser.html', dict(dinfo.items() + dm.items()))
        else:
            dm = {'message': '更新失败'}
            return render(request, 'eidtuser.html', dict(dinfo.items() + dm.items()))


def user_del():
    pass


# 用户详细信息
def user_detail(request):
    username = request.GET.get('username', '')
    if username:
        recordlist = get_one(username)
        id = recordlist.id
        username =  recordlist.username
        email = recordlist.email
        vaild = recordlist.vaild
        logincount = recordlist.logincount
        lastlogin = recordlist.lastlogin
        return render(request, "userdetail.html", locals())
    else:
        response = HttpResponseRedirect('/index/')
        return response

