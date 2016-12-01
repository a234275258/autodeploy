# coding:utf-8
from django.shortcuts import render
from autodeploy.settings import TITLE, ldapconn, basedn
from autodeploy.settings import logger
from django.http import HttpResponse, HttpResponseRedirect
from user.models import check_user, add_user, get_username, update_user
from autodeploy.autodeploy_api import check_db, dbcheckuser, get_one, ldap_add, ldap_mpasswrod, \
    ldap_delete, get_alldata, delete_one, try_int, is_login, chartomd5
from autodeploy.pagehelper import pagehelper, generatehtml
from autodeploy.settings import DBHOST
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
    if is_login(request) != 0:  # 如果已登录,直接跳转
        response = HttpResponseRedirect('/index/')
        return response
    cname = TITLE
    return render(request, 'login.html', locals())


def is_username(username, password, email='test@enjoyfin.com', valid=1, isadmin=0):  # 检测用户并添加用户
    if not check_user(username):  # 如果用户不否存在
        temp = chartomd5(password)
        if temp:
            if add_user(username, temp, email, valid, isadmin):  # 添加用户记录
                return 1
            else:
                return 0
        else:
            return HttpResponse(message % '密码为空')
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
                    logger.error(u'数据库%s连接失败' %DBHOST)
                else:
                    is_username(username, password)  # 检测用户并添加用户，这里可以忽略函数返回值
                    recordlist = get_one(username)
                    if recordlist:
                        request.session['isadmin'] = recordlist.isadmin  # 设置session
                request.session['username'] = username  # 设置session
                request.session.set_expiry(3600)
                return HttpResponseRedirect('/index/')
            except:
                return HttpResponse(message % '用户名或密码不存在')
        except:
            logger.error(u'连接%s服务器连接失败' %ldapconn)
            temp = chartomd5(password)  # md5加密
            if temp:
                if not dbcheckuser(username, temp):  # ldap连接错误，进行数据库认证
                    return HttpResponse(message % '用户名或密码不存在')
            else:
                return HttpResponse(message % '密码长度为空')

            request.session['username'] = username  # 设置session
            request.session.set_expiry(3600)
            return HttpResponseRedirect('/index/')  # 返回到主页

            # return HttpResponse(message % 'ldap服务器连接失败')
        #return HttpResponse(message % '用户名密码错误')  # 如果都没有通过直接返回用户名密码错误
    elif request.method == "GET":
        return HttpResponse(message % '此网页不支持GET方法')


def user_add(request):  # 添加用户
    cname = TITLE
    privlege = is_login(request)
    if privlege == 0:
        return HttpResponseRedirect('/login/')  # 没有登录，返回到主页
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
            logger.error(u"%s ldap添加失败" % username)
        if result and result_ldap:
            message1 = username + '添加成功'
            return render(request, 'adduser.html', {'cname': cname, 'message': message1})
        else:
            message1 = username + '添加失败'
            return render(request, 'adduser.html', {'cname': cname, 'message': message1})
    else:
        if privlege == 2:  # 权限为管理员
            return render(request, 'adduser.html', locals())
        else:
            return HttpResponse(message % '你没有操作此项目的权限')


# 用户列表
def user_list(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    if privage == 2:
        keyword = request.GET.get('keyword', '')
        page = request.GET.get('page', '')
        count = 0  # 总记录数
        peritem = 10  # 每页记录数
        if keyword:  # 带搜索的处理
            data = get_alldata(keyword)  # 查询用户名为关键词的记录
            count = data.count()  # 获取总记录数
            if not page:  # 如果没有取到page值
                page = 1
            page = try_int(page)
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('page=', page, totalpage)
        elif not page:
            page = 1
            data = get_alldata(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/user/list/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_alldata(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/user/list/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render(request, 'index.html', locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


def user_edit(request):  # 修改用户
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    currusername = request.session.get('username', False)  # 检测是否登录
    if request.method == 'GET':
        geturl_username = request.GET.get('username', '')  # 获取用户名
        isadmin = request.session.get('isadmin', False)
        if geturl_username and (not isadmin):  # 如果可以取到数据并且不是管理员就拒绝
            return HttpResponse(message % '你没有操作此项目的权限')
        if not geturl_username and (not currusername):
            return HttpResponseRedirect('/index/')  # 没有获取到就返回主页
        else:
            if geturl_username:  # 传参的用户名有效
                userinfo = get_username(geturl_username)  # 取出获取用户信息
            else:
                userinfo = get_username(currusername)   # 取出当前用户信息
            if userinfo:  # 取出用户信息成功
                email = userinfo.email  # 用户邮箱
                currentisadmin = userinfo.isadmin  # 当前用户权限
                if geturl_username:  # 获取参数用户名有效
                    dict1 = {'cname': cname, 'username': geturl_username, 'email': email, 'isadmin': isadmin,
                             'currentisadmin': currentisadmin}
                    return render(request, 'eidtuser.html', dict1)
                else:  # 返回当前用户信息
                    dict1 = {'cname': cname, 'username': currusername, 'email': email, 'isadmin': isadmin,
                             'currentisadmin': currentisadmin}
                    return render(request, 'eidtuser.html', dict1)
            else:
                return HttpResponse(message % '用户不存在')
    else:  # post方法
        username = request.POST['username'].encode('utf-8')
        password = request.POST['password'].encode('utf-8')
        email = request.POST['email'].encode('utf-8')
        valid1 = request.POST['extra'].encode('utf-8')
        try:  # 如果页面不存在权限标签代表不是管理员
            isadmin = request.POST['role'].encode('utf-8')
        except:
            isadmin = 0

        result = 1  # 执行状态
        result_ldap = 0  # ldap执行状态
        if isadmin:  # 如果是管理员就多传一个权限位给生成的页面
            dinfo = {'cname': cname, 'username': username, 'password': password, 'email': email, 'isadmin': isadmin}
        else:
            dinfo = {'cname': cname, 'username': username, 'password': password, 'email': email}
        if password == "GT1aQi1hLvnt8Q":  # 如果密码为这个值代表没有修改过
            if not (username and password and email and (valid1 not in [0, 1])):
                return render(request, 'eidtuser.html', dinfo)
            result = update_user(username, '', email, valid1, isadmin)
        else:
            temp = chartomd5(password)
            if temp != 0:
                result = update_user(username, temp, email, valid1, isadmin)
                result_ldap = ldap_mpasswrod(username, password)  # 修改ldap密码,修改结果请看日志文件
            else:
                return HttpResponse(message, '密码为空')

        if not result_ldap:  # 如果修改ldap密码失败，打印日志
            logger.error(u'%s用户ldap密码修改失败' % username)
        if result and result_ldap:  # 如果ldap跟数据库密码修改成功
            dm = {'message': '更新成功'}
            return render(request, 'eidtuser.html', dict(dinfo.items() + dm.items()))
        dm = {'message': '更新失败'}
        return render(request, 'eidtuser.html', dict(dinfo.items() + dm.items()))



def user_del(request):
    # username = request.session.get('username', False)
    # isadmin = request.session.get('isadmin', False)
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    if privage == 2:
        if request.method == "GET":
            deluser = request.GET.get('username', '')
            if not deluser:
                return HttpResponse(message % '操作错误')
            else:
                result = delete_one(deluser)
                if result:
                    logger.debug(u"删除用户 %s " % deluser)
                    return HttpResponse('删除成功')
                else:
                    return HttpResponse('删除失败')
        elif request.method == "POST":
            username_list = request.POST.get('id', '')
            if not username_list:
                return HttpResponse('没有选中记录')
            username_list1 = username_list.split(',')
            for i in username_list1:
                try:
                    delete_one(i)
                    result = ldap_delete(i)  # ldap删除用户
                    if not result:
                        logger.warning(u"删除ldap用户%s失败" %i)
                except:
                    pass
            return HttpResponse('删除成功')
        else:
            return HttpResponse('错误请求')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# 用户详细信息
def user_detail(request):
    privage = is_login(request)   # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 没有登陆，返回为登录
    username = request.GET.get('username', '')
    if username:  # 如果用户参数不为为空
        recordlist = get_one(username)
        if not recordlist: # 获取记录失败
            return HttpResponse(message, '用户记录获取失败')
        id = recordlist.id
        username = recordlist.username
        email = recordlist.email
        vaild = recordlist.vaild
        logincount = recordlist.logincount
        lastlogin = recordlist.lastlogin
        return render(request, "userdetail.html", locals())
    else:
        response = HttpResponseRedirect('/index/')
        return response
