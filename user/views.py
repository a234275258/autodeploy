# coding:utf-8
from django.shortcuts import render
from autodeploy.settings import TITLE, ldapconn, basedn
from autodeploy.settings import logger
from django.http import HttpResponse, HttpResponseRedirect
from user.models import check_user, add_user, get_username, update_user
from autodeploy.autodeploy_api import check_db
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


def is_username(username, password, email='test@enjoyfin.com', valid=1):  # 检测用户并添加用户
    if not check_user(username):  # 如果用户不否存在
        temp = hashlib.md5()
        temp.update(password)
        if add_user(username, temp.hexdigest(), email, valid):  # 添加用户记录
            return "添加成功"
        else:
            return "添加失败"
    else:
        return "用户已存在"


def checklogin(request):  # 登录检测
    if request.method == "POST":
        try:
            username = request.POST['username'].encode('utf-8')
            password = request.POST['password'].encode('utf-8')
            udn = "uid=" + username + "," + basedn
            conn = ldap.initialize(ldapconn)
            try:
                conn.simple_bind_s(udn, password)
            except:
                return HttpResponse(message % '用户名或密码不存在')
            if check_db():
                is_username(username, password)  # 检测用户并添加用户，这里可以忽略函数返回值
                request.session['username'] = username  # 设置session
                request.session.set_expiry(3600)
                response = HttpResponseRedirect('/index/')
                return response
            else:
                return HttpResponse(message % '数据库连接失败')
        except:
            logger.error('连接'+ldapconn+'服务器连接失败')
            return HttpResponse(message % 'ldap服务器连接失败')
        return HttpResponse(message % '用户名密码错误')
    elif request.method == "GET":
        return HttpResponse(message % '此网页不支持GET方法')


def user_add(request):  # 添加用户
    cname = TITLE
    if request.method == "POST":
        username = request.POST['username'].encode('utf-8')
        password = request.POST['password'].encode('utf-8')
        email = request.POST['email'].encode('utf-8')
        valid1 = request.POST['extra'].encode('utf-8')
        if not (username and password and email and (valid1 not in [0, 1])):
            return render(request, 'adduser.html', {'cname': cname, 'message': '输入错误，请重新输入'})
        result = is_username(username, password, email, valid1)  # 检测用户并添加用户
        message1 = username + result
        return render(request, 'adduser.html', {'cname': cname, 'message': message1})

    username = request.session.get('username', False)
    if username:
        return render(request, 'adduser.html', locals())


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
        if not geturl_username:
            response = HttpResponseRedirect('/index/')  # 没有获取到就返回主页
            return response
        else:
            userinfo = get_username(geturl_username)
            if userinfo:
                email = userinfo.email
                return render(request, 'eidtuser.html', {'cname': cname, 'username': geturl_username, 'email': email})
            else:
                return HttpResponse(message % '用户不存在')
    else:  # post方法
        username = request.POST['username'].encode('utf-8')
        password = request.POST['password'].encode('utf-8')
        email = request.POST['email'].encode('utf-8')
        valid1 = request.POST['extra'].encode('utf-8')
        result = 1  # 执行状态
        dinfo = {'cname': cname, 'username': username, 'password': password, 'email': email}
        if password == "GT1aQi1hLvnt8Q":  # 如果密码为这个值代表没有修改过
            if not (username and password and email and (valid1 not in [0, 1])):
                return render(request, 'eidtuser.html', dinfo)
            result = update_user(username, '', email, valid1)
        else:
            result = update_user(username, password, email, valid1)
        if result:
            dm = {'message': '更新成功'}
            return render(request, 'eidtuser.html', dict(dinfo.items() + dm.items()))
        else:
            dm = {'message': '更新失败'}
            return render(request, 'eidtuser.html', dict(dinfo.items() + dm.items()))


def user_del():
    pass


def user_detail():
    pass
