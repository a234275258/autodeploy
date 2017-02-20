# coding:utf-8
from django.shortcuts import render
from autodeploy.settings import TITLE, ldapconn, basedn, URL, DEFAULT_FROM_EMAIL, DBHOST, message, messageindex, \
    logger
from django.http import HttpResponse, HttpResponseRedirect
from autodeploy.autodeploy_api import check_db, dbcheckuser, get_one, ldap_add, ldap_mpasswrod, \
    ldap_delete, get_alldata, delete_one, try_int, is_login, chartomd5, check_user, add_user, \
    get_username, update_user, userpass_modify, get_resetpass, delete_resetpass, addpercode, \
    get_percode, all_delete_one, all_get_one, update_perone, update_user_per, add_user_per, get_user_per
from autodeploy.pagehelper import pagehelper, generatehtml
import ldap
import time
from django.core.mail import send_mail
from user.models import admin, per_code


# Create your views here.

def login(request):  # 登录页面
    if is_login(request) != 0:  # 如果已登录,直接跳转
        return HttpResponseRedirect('/index/')
    cname = TITLE
    return render(request, 'login.html', locals())


def is_username(username, password, email='test@enjoyfin.com', valid=1, isadmin=0):  # 检测用户并添加用户
    if not check_user(username, time.strftime("%Y-%m-%d %H:%M:%S")):  # 如果用户不否存在
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
            conn.simple_bind_s(udn, password)
            if not check_db():  # 检测数据库是否正常,前提条件是ldap已成功认证
                logger.error(u'数据库%s连接失败' % DBHOST)
                return HttpResponse(message % ('数据库%s连接失败' % DBHOST))
            else:
                is_username(username, password)  # 检测用户并添加用户，这里可以忽略函数返回值
                record = get_one(username)
                if record:
                    request.session['isadmin'] = record.isadmin  # 设置session
                else:
                    request.session['isadmin'] = 0  # 设置session
                request.session['username'] = username  # 设置session
                request.session.set_expiry(3600)
                return HttpResponseRedirect('/index/')
        except Exception, e:
            if 'Invalid' in str(e):
                return HttpResponse(message % '用户名或密码不存在')
            else:
                logger.error(u'连接%s服务器连接失败' % ldapconn)

            result = check_db()  # 检测数据库是否正常

            if not result:
                logger.error(u'数据库%s连接失败' % DBHOST)
                return HttpResponse(message % 'ldap认证与数据库都连接失败')

            temp = chartomd5(password)  # md5加密
            if temp:
                record = dbcheckuser(username, temp)
                if not record:  # ldap连接错误，进行数据库认证
                    return HttpResponse(message % '用户名或密码不存在')
                else:  # 认证通过
                    request.session['isadmin'] = record.isadmin
                    request.session['username'] = username  # 设置session
                    # request.session.set_expiry(3600)  # 已在settings中设置
                    return HttpResponseRedirect('/index/')  # 返回到主页
            else:
                return HttpResponse(message % '密码长度为空')

    elif request.method == "GET":
        return HttpResponse(message % '此网页不支持GET方法')


def user_add(request):  # 添加用户
    cname = TITLE
    privlege = is_login(request)
    if privlege == 0:
        return HttpResponseRedirect('/login/')  # 没有登录，返回到主页
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == "POST":
        username = request.POST['username'].encode('utf-8')
        password = request.POST['password'].encode('utf-8')
        email = request.POST['email'].encode('utf-8')
        valid1 = request.POST['extra'].encode('utf-8')
        extra = request.POST.getlist('extra', [])
        valid1 = '0' if '0' in extra else '1'
        send_mail_need = True if '1' in extra else False
        isadmin = request.POST['role'].encode('utf-8')
        if not (username and password and email and (valid1 not in [0, 1]) and (isadmin not in [0, 1])):
            return render(request, 'user/adduser.html', {'cname': cname, 'message': '输入错误，请重新输入'})
        result = is_username(username, password, email, valid1, isadmin)  # 检测用户并添加用户
        result_ldap = ldap_add(username, password)
        if not result_ldap:
            logger.error(u"%s ldap添加失败" % username)
        if result and result_ldap:
            message1 = username + '添加成功'
            if send_mail_need:  # 发送邮件
                msg = u"""尊敬的用户,欢迎使用本系统，以下是您的用户信息：
用户名：%s
密码：%s
登陆地址：%s
恭喜帐号开通成功""" % (username, '******', URL)
                print msg
                send_mail_mod(u"恭喜帐号开通成功", msg, str(email))
            return render(request, 'user/adduser.html', {'cname': cname, 'message': message1, 'username': username, 'isadmin':isadmin})
        else:
            message1 = username + '添加失败'
            return render(request, 'user/adduser.html', {'cname': cname, 'message': message1, 'username': username, 'isadmin':isadmin})
    else:
        if privlege == 2:  # 权限为管理员
            return render(request, 'user/adduser.html', locals())
        else:
            return HttpResponse(message % '你没有操作此项目的权限')


# 用户列表
def user_list(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
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
        return render(request, 'user/userlist.html', locals())
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
                userinfo = get_username(currusername)  # 取出当前用户信息
            if userinfo:  # 取出用户信息成功
                email = userinfo.email  # 用户邮箱
                currentisadmin = userinfo.isadmin  # 当前用户权限
                if geturl_username:  # 获取参数用户名有效
                    dict1 = {'cname': cname, 'username': geturl_username, 'email': email, 'isadmin': isadmin,
                             'currentisadmin': currentisadmin}
                    return render(request, 'user/eidtuser.html', dict1)
                else:  # 返回当前用户信息
                    dict1 = {'cname': cname, 'username': currusername, 'email': email, 'isadmin': isadmin,
                             'currentisadmin': currentisadmin}
                    return render(request, 'user/eidtuser.html', dict1)
            else:
                return HttpResponse(message % '用户不存在')
    else:  # post方法
        username = request.POST['username'].encode('utf-8')
        password = request.POST['password'].encode('utf-8')
        email = request.POST['email'].encode('utf-8')
        # valid1 = request.POST['extra'].encode('utf-8')
        extra = request.POST.getlist('extra', [])
        valid1 = '0' if '0' in extra else '1'
        send_mail_need = True if '1' in extra else False
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
                return render(request, 'user/eidtuser.html', dinfo)
            result = update_user(username, '', email, valid1, isadmin)
        else:
            temp = chartomd5(password)
            if temp != 0:
                result = update_user(username, temp, email, valid1, isadmin)
                result_ldap = ldap_mpasswrod(username, password)  # 修改ldap密码,修改结果请看日志文件
            else:
                return HttpResponse(message % '密码为空')

        if password != "GT1aQi1hLvnt8Q":   # 密码没有修改不对ldap进行判断
            if not result_ldap:  # 如果修改ldap密码失败，打印日志
                logger.error(u'%s用户ldap密码修改失败' % username)

        if password != "GT1aQi1hLvnt8Q":  # 密码没有修改不对ldap进行判断
            if result and result_ldap:  # 如果ldap跟数据库密码修改成功
                if send_mail_need:  # 发送邮件
                    msg = u"""用户名：%s
密码：%s
登陆地址: %s
帐号资料修改成功""" % (username, '******', URL)
                    send_mail_mod(u"帐号资料修改成功", msg, str(email))
                dm = {'message': '更新成功'}
                return render(request, 'user/eidtuser.html', dict(dinfo.items() + dm.items()))
        else:
            if result:
                dm = {'message': '更新成功'}
                return render(request, 'user/eidtuser.html', dict(dinfo.items() + dm.items()))
        dm = {'message': '更新失败'}
        return render(request, 'user/eidtuser.html', dict(dinfo.items() + dm.items()))


def user_del(request):
    # username = request.session.get('username', False)
    # isadmin = request.session.get('isadmin', False)
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
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
                        logger.warning(u"删除ldap用户%s失败" % i)
                except:
                    pass
            return HttpResponse('删除成功')
        else:
            return HttpResponse('错误请求')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# 用户详细信息
def user_detail(request):
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 没有登陆，返回为登录
    username = request.GET.get('username', '')
    isadmin = request.session.get('isadmin', False)
    if username:  # 如果用户参数不为为空
        recordlist = get_one(username)
        if not recordlist:  # 获取记录失败
            return HttpResponse(message % '用户记录获取失败')
        id = recordlist.id
        username = recordlist.username
        email = recordlist.email
        vaild = recordlist.vaild
        logincount = recordlist.logincount
        lastlogin = recordlist.lastlogin
        return render(request, "user/userdetail.html", locals())
    else:
        response = HttpResponseRedirect('/index/')
        return response


def user_mail_send(request):  # 发送邮件
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 没有登陆，返回为登录
    username = request.GET.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if not username:
        return HttpResponse('操作失败')
    record = get_one(username)
    if not record:
        return HttpResponse('操作失败')
    useremail = record.email
    passuuid = userpass_modify(username)
    if not passuuid:
        return HttpResponse('操作失败')
    msg = u"""用户名：%s
    重设密码：%s/user/forget/?username=%s&passuuid=%s
如忘记密码请点击重设密码链接修改密码
    """ % (username, URL, username, passuuid)
    try:
        send_mail(u'邮件发送', msg.strip(), DEFAULT_FROM_EMAIL, [useremail], fail_silently=False)
    except IndexError:
        return HttpResponse('操作失败')
    return HttpResponse('发送成功')


# 忘记密码
def forget(request):
    cname = TITLE
    if request.method == "GET":
        username = request.GET.get('username', False)
        passuuid = request.GET.get('passuuid', False)
        if not (username and passuuid):  # 没有加任何参数
            return render(request, 'user/forget.html', locals())
        else:
            record = get_resetpass(username, passuuid)
            if record:
                ctime = time.mktime(time.strptime(str(record.ctime), "%Y-%m-%d %H:%M:%S"))  # 日期时间转时间戳
                if int(time.time()) - int(ctime) > 600:
                    return HttpResponse(message % '链接已超时，请使用忘记密码重新发送')
                return render(request, 'user/reset_password.html', locals())
            else:
                return HttpResponse(messageindex % ('链接有误', '/index/'))
    else:
        username = request.POST.get('username', False)
        email = request.POST.get('email', False)
        if not (username and email):  # 如果没有输入相关信息
            return HttpResponse(message % '输入信息有误')
        else:
            record = get_one(username)
            if (not record) or (record.email != email):  # 如果用户名管理没有输入
                return HttpResponse(message % '输入信息有误')
            else:
                record = get_one(username)
                if not record:
                    return HttpResponse(message % '重置密码失败')
                useremail = record.email
                passuuid = userpass_modify(username)  # 添加一条重置记录
                if not passuuid:
                    return HttpResponse(message % '重置密码失败')
                msg = u"""
                用户名：%s
                重设密码：%s/user/forget/?username=%s&passuuid=%s
                如忘记密码请点击重设密码链接修改密码
                """ % (username, URL, username, passuuid)
                try:
                    send_mail(u'邮件发送', msg, DEFAULT_FROM_EMAIL, [useremail], fail_silently=False)
                except IndexError:
                    return HttpResponse(message % '重置密码失败')
                return HttpResponse(messageindex % ('重置密码邮件发送成功', '/index/'))


# 重置密码
def reset_password(request):
    cname = TITLE
    if request.method == "GET":
        username = request.GET.get('username', False)
        passuuid = request.GET.get('passuuid', False)
        if username and passuuid:
            record = get_resetpass(username, passuuid)
            if record:
                render(request, 'user/reset_password.html', locals())
            return HttpResponse(messageindex % ('链接信息有误', '/index/'))
        else:
            return HttpResponse(messageindex % ('链接信息有误', '/index/'))
    else:
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        username = request.POST.get('username')
        passuuid = request.POST.get('passuuid')
        if password != password_confirm:
            return HttpResponse(message % '密码不匹配')
        else:
            record = get_one(username)
            result = False
            result_ldap = False
            if not get_resetpass(str(username), str(passuuid)):
                return HttpResponse(messageindex % ('链接错误', '/index/'))
            if record:
                temp = chartomd5(password)
                if temp != 0:
                    result = update_user(username, temp, record.email, record.vaild, record.isadmin)
                    result_ldap = ldap_mpasswrod(username, password)  # 修改ldap密码,修改结果请看日志文件
                else:
                    return HttpResponse(message % '密码为空')
                if not result_ldap:  # 如果修改ldap密码失败，打印日志
                    logger.error(u'%s用户ldap密码修改失败' % username)
                if result and result_ldap:  # 如果ldap跟数据库密码修改成功
                    delete_resetpass(username, passuuid)  # 删除重置密码记录，删除成功与否不作判断
                    return HttpResponse(messageindex % ('密码修改成功', '/index/'))
                return HttpResponse(messageindex % ('密码修改失败', '/index/'))
            else:
                return HttpResponse(messageindex % ('密码修改失败', '/index/'))


# 发送邮件模块
def send_mail_mod(subject, msg, mailto):
    try:
        send_mail(u'%s' % subject, msg, DEFAULT_FROM_EMAIL, [mailto], fail_silently=False)
    except IndexError:
        return 0
    return 1


# 权限添加
def privilege_add(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if privage == 2:
        if request.method == 'GET':
            return render(request, 'user/percodeadd.html', locals())
        else:
            pcode = request.POST.get('pcode', False)
            pname = request.POST.get('pname', False)
            if not (pcode and pname):
                return HttpResponse(message % '输入有误')
            else:
                result = addpercode(pcode, pname)
                if result:
                    message = "添加成功"
                else:
                    message = "添加失败"
                return render(request, 'user/percodeadd.html', locals())
    else:
        return HttpResponse(message % '你没有模块权限')


# 权限列表
def privilege_list(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if privage == 2:
        keyword = request.GET.get('keyword', '')
        page = request.GET.get('page', '')
        count = 0  # 总记录数
        peritem = 10  # 每页记录数
        if keyword:  # 带搜索的处理
            data = get_percode(keyword)  # 查询权限说明为关键词的记录
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
            data = get_percode(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/privilege/list/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_percode(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/privilege/list/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render(request, 'user/perlist.html', locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


# 删除权限代码
def privilege_del(request):
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if privage == 2:
        if request.method == "GET":
            id = request.GET.get('id', '')
            if not id:
                return HttpResponse(message % '操作错误')
            else:
                result = all_delete_one('per_code', id)
                if result:
                    return HttpResponse('权限删除成功')
                else:
                    return HttpResponse('删除失败')
        elif request.method == "POST":
            per_list = request.POST.get('id', '')
            if not per_list:
                return HttpResponse('没有选中记录')
            per_list1 = per_list.split(',')
            for i in per_list1:
                all_delete_one('per_code', i)
            return HttpResponse('删除成功')
        else:
            return HttpResponse('错误请求')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# 编辑权限代码
def privilege_edit(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == 'GET':
        id = request.GET.get('id', '')  # 获取用户名
        result = all_get_one('per_code', id)
        if result:
            pcode = result.Per_code
            pname = result.Per_name
            return render(request, 'user/editper.html', locals())
        else:
            return HttpResponse(message % '记录不存在')
    else:
        id = request.POST['id'].encode('utf-8')
        pcode = request.POST['pcode'].encode('utf-8')
        pname = request.POST['pname'].encode('utf-8')
        result = update_perone(id, pcode, pname)
        if result:
            message = "更新成功"
        else:
            message = "更新失败"
        return render(request, 'user/editper.html', locals())
    return HttpResponse(message % '你没有操作此项目的权限')


# 授权
def privilege_grant(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if privage == 2:
        if request.method == 'GET':
            try:
                user = admin.objects.all().values('username')  # 获取用户数据
                percode = per_code.objects.all().values('Per_code', 'Per_name')  # 获取权限数据
            except:
                return HttpResponse(message % '获取数据失败')
            return render(request, 'user/grantadd.html', locals())
        else:
            user = request.POST.get('puser', False)
            pcode = request.POST.get('pcode', False)
            comment = request.POST.get('comment', "")
            if not (user and pcode):
                return HttpResponse(messageindex % ('输入有误', '/index/'))
            else:
                result = add_user_per(user, pcode, comment)
                if result:
                    message = "添加成功"
                else:
                    message = "添加失败"
                try:
                    user = admin.objects.all().values('username')  # 获取用户数据
                    percode = per_code.objects.all().values('Per_code', 'Per_name')  # 获取权限数据
                except:
                    return HttpResponse(messageindex % ('输入有误', '/index/'))
                return render(request, 'user/grantadd.html', locals())
    else:
        return HttpResponse(message % '你没有模块权限')


# 权限列表
def privilege_grantlist(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if privage == 2:
        keyword = request.GET.get('keyword', '')
        page = request.GET.get('page', '')
        count = 0  # 总记录数
        peritem = 10  # 每页记录数
        if keyword:  # 带搜索的处理
            count, data = get_user_per(keyword)  # 查询权限说明为关键词的记录
            #count = data.count()  # 获取总记录数
            if not count:
                return HttpResponse(messageindex % ('目前还没有授权记录，请添加', '/privilege/grant/'))
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
            count, data = get_user_per(False)  # 获取所有记录
            if not count:
                return HttpResponse(messageindex % ('目前还没有授权记录，请添加', '/privilege/grant/'))
            #count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/privilege/grantlist/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            count, data = get_user_per(False)  # 获取所有记录
            if not count:
                return HttpResponse(messageindex % ('目前还没有授权记录，请添加', '/privilege/grant/'))
            #count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/privilege/grantlist/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render(request, 'user/grantlist.html', locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


# 权限删除
def privilege_grantdel(request):
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if privage == 2:
        if request.method == "GET":
            id = request.GET.get('id', '')
            if not id:
                return HttpResponse(message % '操作错误')
            else:
                result = all_delete_one('user_per', id)
                if result:
                    return HttpResponse('权限删除成功')
                else:
                    return HttpResponse('删除失败')
        elif request.method == "POST":
            per_list = request.POST.get('id', '')
            if not per_list:
                return HttpResponse('没有选中记录')
            per_list1 = per_list.split(',')
            for i in per_list1:
                all_delete_one('user_per', i)
            return HttpResponse('删除成功')
        else:
            return HttpResponse('错误请求')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# 权限编辑
def privilege_grantedit(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == 'GET':
        id = request.GET.get('id', '')  # 获取用户名
        result = all_get_one('user_per', id)
        if result:
            peruser = result.Per_user
            pname = result.Per_code
            comment = result.comment
            try:
                percode = per_code.objects.all().values('Per_code', 'Per_name')  # 获取权限数据
            except:
                return HttpResponse(message % '获取数据失败')
            return render(request, 'user/editgrant.html', locals())
        else:
            return HttpResponse(message % '获取数据失败')
    else:
        id = request.POST['id'].encode('utf-8')
        peruser = request.POST['user'].encode('utf-8')
        pcode = request.POST['pcode'].encode('utf-8')
        comment = request.POST['comment'].encode('utf-8')
        result = update_user_per(id, peruser, pcode, comment)
        if result:
            message = "更新成功"
        else:
            message = "更新失败"
        try:
            percode = per_code.objects.all().values('Per_code', 'Per_name')  # 获取权限数据
        except:
            return HttpResponse(message % '获取数据失败')
        return render(request, 'user/editgrant.html', locals())

