# coding: utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.safestring import mark_safe
from autodeploy.settings import TITLE, URL, DEFAULT_FROM_EMAIL, DBHOST, message, messageindex, \
    logger, jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig, PROJECTPATH, jenkinsfileport, \
    jenkinsip
from autodeploy.autodeploy_api import is_login, all_get_one, all_delete_one, try_int
from project.project_api import add_project, jenkins_tools, get_project, update_project, add_project_build, \
    get_project_build, update_project_build
from autodeploy.pagehelper import pagehelper, generatehtml
from project.models import project, project_build
import threading
import time
import uuid
import re
import socket
import os


# Create your views here.

# 新建项目
def project_add(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == "GET":
        return render_to_response('project/addproject.html', locals())
    else:
        proname = request.POST.get('proname', False)
        prodesc = request.POST.get('prodesc', False)
        prosvn = request.POST.get('prosvn', False)
        certificateid = request.POST.get('certificateid', False)
        mavenpara = request.POST.get('mavenpara', False)
        buildtype = request.POST.get('buildtype', False)
        if not (proname and prodesc and prosvn and buildtype):
            return HttpResponse(message % '提交数据有误')
        result = add_project(proname, prodesc, prosvn, certificateid, mavenpara, buildtype, username)
        jkserver = jenkins_tools(jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig)  # 实例化jenkins_tools类
        jenkinsserver = jkserver.createserver()  # 创建一个jeknins 服务器对象
        if jenkinsserver:
            jkresult = jkserver.createjob(jenkinsserver, proname, prodesc, prosvn, certificateid, mavenpara)
        else:
            return HttpResponse(message % '创建失败')
        if request and jkresult:
            message = "项目添加成功"
        else:
            message = "项目添加失败"
        return render_to_response('project/addproject.html', locals())

# 从jenkins服务器获取文件
def getfile(targetfile, localfile):
    ip = jenkinsip
    port = jenkinsfileport
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    localdir = os.path.split(localfile)[0]
    filestat =0
    if not os.path.exists(localdir):
        try:
            os.makedirs(localdir)
        except:
            logger.error(u'创建%s目录失败', localdir)
    try:
        s.connect((ip, int(port)))
        client_command = "get %s" %targetfile
        s.send(client_command)
        data = s.recv(4096)
        if data == 'ready':
            f = open(localfile, 'wb+')
            while True:
                data = s.recv(4096)
                if data == 'EOF':
                    logger.error(u'文件%s传输完成' %localfile)
                    break
                f.write(data)
            f.close()
        filestat = 1
    except:
        logger.error(u'下载%s文件%s失败' % (ip, targetfile))
    finally:
        s.close()
        return filestat


# 修改项目
def project_edit(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == 'GET':
        id = request.GET.get('id', False)  # 获取ID
        result = all_get_one('project', id)
        if result:
            Pro_name = result.Pro_name
            Pro_desc = result.Pro_desc
            svn_ip = result.svn_ip
            certificateid = result.certificateid
            mavenpara = result.mavenpara
            buildtype = result.buildtype
            return render_to_response('project/editproj.html', locals())
        else:
            return HttpResponse(messageindex % ('记录不存在', '/project/list/'))
    else:
        id = request.POST.get('id', False)
        proname = request.POST.get('proname', False)
        prodesc = request.POST.get('prodesc', False)
        prosvn = request.POST.get('prosvn', False)
        certificateid = request.POST.get('certificateid', False)
        mavenpara = request.POST.get('mavenpara', False)
        buildtype = request.POST.get('buildtype', False)
        if not (proname and prodesc and prosvn and buildtype):
            return HttpResponse(messageindex % ('提交数据有误', '/project/list/'))
        result = update_project(id, proname, prodesc, prosvn, certificateid, mavenpara, buildtype, username)
        Pro_name = proname
        Pro_desc = prodesc
        svn_ip = prosvn
        jkserver = jenkins_tools(jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig)
        jserver = jkserver.createserver()
        jkresult = jkserver.editjob(jserver, proname, prodesc, prosvn, certificateid, mavenpara)
        if result and jkresult:
            message = "更新成功"
        else:
            message = "更新失败"
        return render_to_response('project/editproj.html', locals())
    return HttpResponse(message % '你没有操作此项目的权限')


# 项目列表
def project_list(request):
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
            data = get_project(keyword)  # 查询权限说明为关键词的记录
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
            data = get_project(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/project/list/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_project(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/project/list/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render_to_response('project/projlist.html', locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


# 删除项目
def project_del(request):
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
                record = project.objects.get(id=id)
                projname = record.Pro_name
                result = all_delete_one('project', id)
                jkserver = jenkins_tools(jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig)
                jserver = jkserver.createserver()
                jresult = jkserver.deletejob(jserver, projname)
                if result and jresult:
                    return HttpResponse('项目删除成功')
                else:
                    return HttpResponse('项目删除失败')
        elif request.method == "POST":
            per_list = request.POST.get('id', '')
            if not per_list:
                return HttpResponse('没有选中记录')
            per_list1 = per_list.split(',')
            for i in per_list1:
                record = project.objects.get(id=i)
                projname = record.Pro_name
                jkserver = jenkins_tools(jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig)
                jserver = jkserver.createserver()
                jkserver.deletejob(jserver, projname)
                all_delete_one('project', i)
            return HttpResponse('项目删除成功')
        else:
            return HttpResponse('项目删除失败')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')

# 构建项目
def build_project(Pro_name, buildlog, buildtype):
    jkserver = jenkins_tools(jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig)  # 实例化jenkins_tools类
    jenkinsserver = jkserver.createserver()  # 创建一个jeknins 服务器对象
    if jenkinsserver:
        jkresult, relog, reinfo, buildseq = jkserver.bulidjob(jenkinsserver, Pro_name)   # 接收返回三个参数，第一个为构建结果，第二个为日志，第三个为信息
        if jkresult: # 如果构建成功
            svnversion = reinfo.get('changeSet').get('revisions')[0].get('revision')
            filename = str(buildtype.split('.')[0]) + '-' + str(time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time()))) + \
                       str(svnversion) + '.' + str(buildtype.split('.')[1])
            filename = PROJECTPATH + '/' + Pro_name + '/' + filename
            pkg = re.search(".*%s.*" % buildtype, relog).group(0).split(":")[1]   # 构建生成的包名
            getfile(pkg, filename)  # 接取构件文件到本地
            try:
                builddata =project_build.objects.get(buildlog=buildlog)
                builddata.success = 1
                builddata.file = filename
                builddata.svnversion = svnversion
                builddata.buildlog = relog
                builddata.buildseq = buildseq
                builddata.save()
            except:
                pass
        else:
            try:
                builddata = project_build.objects.get(buildlog=buildlog)
                builddata.success = 0
                builddata.file = 'Nothing'
                builddata.svnversion = svnversion
                builddata.buildlog = relog
                builddata.buildseq = buildseq
                builddata.save()
            except:
                pass
    else:
        try:
            builddata = project_build.objects.get(buildlog=buildlog)
            builddata.success = 0
            builddata.file = 'Nothing'
            builddata.svnversion = 0
            builddata.buildlog = 'Nothing'
            builddata.buildseq = 0
            builddata.save()
        except:
            pass

# 构建项目
def project_buildadd(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == "GET":
        projectdata = get_project(False)
        if projectdata:
            return render_to_response('project/addbuild.html', locals())
        else:
            return HttpResponse(message % '获取数据失败')
    else:
        Pro_id = request.POST.get('Pro_id', False)
        if not (Pro_id):
            return HttpResponse(message % '提交数据有误')
        projectdata = all_get_one('project', Pro_id)
        Pro_name = projectdata.Pro_name     # 项目名

        # 检测是否项目刚提交构建
        try:
            if  project_build.objects.filter(Pro_name=Pro_name).exists():
                record = project_build.objects.filter(Pro_name=Pro_name).order_by('-id')[0]
                oldtime = time.mktime(time.strptime(str(record.builddate), "%Y-%m-%d %H:%M:%S"))
                timelag = time.time() - oldtime
                if timelag <= 300:
                    projectdata = get_project(False)
                    message = '本项目上一次构建还没有完成，请过5分钟再试'
                    return render_to_response('project/addbuild.html', locals())
        except:
            pass
        buildtype = projectdata.buildtype   # 构建类型
        buildtime = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        buildlog = str(uuid.uuid4())
        result = add_project_build(Pro_id, Pro_name, buildtime, 0, "", 0, username, buildlog, 0)
        t = threading.Thread(target=build_project, args=(Pro_name, buildlog, buildtype))  # 启动多线程
        t.start()
        time.sleep(2)
        if request:
            message = "项目构建添加成功，请在构建列表中查看是否成功"
        else:
            message = "项目添加失败"
        projectdata = get_project(False)
        return render_to_response('project/addbuild.html', locals())


# 构建修改
def project_buildedit(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == 'GET':
        id = request.GET.get('id', False)  # 获取ID
        result = all_get_one('project_build', id)
        if result:
            Pro_id = result.Pro_id
            Pro_name = result.Pro_name
            builddate = result.builddate
            builddate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.mktime(time.strptime(str(builddate), "%Y-%m-%d %H:%M:%S"))))
            success = result.success
            file = result.file
            svnversion = result.svnversion
            username = result.username
            buildseq = result.buildseq
            return render_to_response('project/editbuild.html', locals())
        else:
            return HttpResponse(messageindex % ('记录不存在', '/project/buildlist/'))
    else:
        id = request.POST.get('id', False)
        Pro_id = request.POST.get('Pro_id', False)
        Pro_name = request.POST.get('Pro_name', False)
        builddate = request.POST.get('builddate', False)
        success = request.POST.get('success', False)
        if success == u"成功":
            success = 1
        else:
            success = 0
        file = request.POST.get('file', False)
        svnversion = request.POST.get('svnversion', False)
        username = request.POST.get('username', False)
        buildseq = request.POST.get('buildseq', False)
        if not (Pro_name and builddate and (success in [0 ,1]) and file and svnversion and username and buildseq):
            return HttpResponse(messageindex % ('提交数据有误', '/project/buildlist/'))
        result = update_project_build(id, Pro_id, Pro_name, builddate, success, file, svnversion, username, buildseq )
        if result:
            message = "更新成功"
        else:
            message = "更新失败"
        builddate = time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.localtime(time.mktime(time.strptime(str(builddate), "%Y-%m-%d %H:%M:%S"))))
        return render_to_response('project/editbuild.html', locals())


# 构建列表
def project_buildlist(request):
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
            data = get_project_build(keyword)  # 查询权限说明为关键词的记录
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
            data = get_project_build(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/project/buildlist/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_project_build(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/project/buildlist/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render_to_response('project/buildlist.html', locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


# 构建删除
def project_builddel(request):
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
                result = all_delete_one('project_build', id)
                if result:
                    return HttpResponse('项目删除成功')
                else:
                    return HttpResponse('项目删除失败')
        elif request.method == "POST":
            per_list = request.POST.get('id', '')
            if not per_list:
                return HttpResponse('没有选中记录')
            per_list1 = per_list.split(',')
            for i in per_list1:
                all_delete_one('project_build', i)
            return HttpResponse('项目删除成功')
        else:
            return HttpResponse('项目删除失败')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')

# 查看构建日志
def project_buildlog(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    id = request.GET.get('id', False)
    if not id:
        return HttpResponse(message % '获取数据错误')
    record = all_get_one('project_build', id)
    if record:
        buildlog = re.sub('\n', '<br>', record.buildlog)
        buildlog = mark_safe(buildlog)
        buildseq = record.buildseq
        Pro_name = record.Pro_name
        return render_to_response('project/buildlog.html', locals())
    else:
        return HttpResponse(message % '获取数据错误')


