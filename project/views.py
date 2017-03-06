# coding: utf-8
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.safestring import mark_safe
from autodeploy.settings import TITLE, URL, DEFAULT_FROM_EMAIL, DBHOST, message, messageindex, \
    logger, jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig, PROJECTPATH, jenkinsfileport, \
    jenkinsip, svnurl
from autodeploy.autodeploy_api import is_login, all_get_one, all_delete_one, try_int, checklogin
from project.project_api import add_project, jenkins_tools, get_project, update_project, add_project_build, \
    get_project_build, update_project_build, addsvnuser, get_svnauth, update_svnauth, \
    get_mavenpara, addmavenpara, update_mavenpara, get_mavenhname, get_svnauthname, \
    etcdfilecopy
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
@checklogin
def project_add(request, *args, **kwargs):
    cname = TITLE
    privage = kwargs.get("privage")  # 权限，0为未登录，2为管理员，3为普通用户
    username = kwargs.get("username")
    isadmin = kwargs.get("isadmin")
    if request.method == "GET":
        svnuser = get_svnauth(False)  # svn认证数据
        mavenlist = get_mavenpara(False)  # maven参数列表
        return render_to_response('project/addproject.html', locals())
    else:
        proname = request.POST.get('proname', False)
        prodesc = request.POST.get('prodesc', False)
        proport = request.POST.get('proport', False)
        prosvn = request.POST.get('prosvn', False)
        svnuser = request.POST.get('certificateid', False)

        # 查询这个的目的是给jenkins创建项目用，jenkins必须用certificateid
        certificateid = get_svnauthname(svnuser)
        if not certificateid:
            return HttpResponse(message % 'SVN选择有误或记录不存在')
        certificateid = certificateid.svncode  # 查询到真正的svnid信息

        # 查询这个的目的是给jenkins创建项目用，jenkins必须用maven真实参数
        mavenparaname = request.POST.get('mavenpara', False)
        mavenpara = get_mavenhname(mavenparaname)
        if not mavenpara:
            return HttpResponse(message % 'Maven选择有误或记录不存在')
        mavenpara = mavenpara.paravalue  # 查询到真正的maven信息
        enableweb = request.POST.get('enableweb', False)
        buildtype = request.POST.get('buildtype', False)
        maillist = request.POST.get('maillist', False)
        scriptlist = request.POST.get('scriptlist', False)
        rpcmemory = request.POST.get('rpcmemory', False)
        if enableweb:
            webmemory = request.POST.get('webmemory', False)
        else:
            webmemory = 0
        if not (proname and prodesc and prosvn and buildtype and proport):
            return HttpResponse(message % '提交数据有误')
        if maillist:
            maillist = ',' + maillist
        result = add_project(proname, prodesc, proport, prosvn, svnuser, mavenparaname, buildtype, username, maillist,
                             scriptlist, enableweb, rpcmemory, webmemory)
        jkserver = jenkins_tools(jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig)  # 实例化jenkins_tools类
        jenkinsserver = jkserver.createserver()  # 创建一个jeknins 服务器对象
        if jenkinsserver:
            jkresult = jkserver.createjob(jenkinsserver, proname, prodesc, prosvn, certificateid, mavenpara, maillist,
                                          scriptlist)
        else:
            return HttpResponse(message % '创建失败')
        if result and jkresult:
            localmessage = "添加成功"
        elif result and not jkresult:
            localmessage = "数据库添加成功，后端jenkins添加失败"
        elif not result and jkresult:
            localmessage = "数据库添加失败，后端jenkins添加成功"
        else:
            localmessage = "添加失败"
        svnuser = get_svnauth(False)  # svn认证数据
        mavenlist = get_mavenpara(False)  # maven参数列表
        return render_to_response('project/addproject.html', locals())


# 从jenkins服务器获取文件
def getfile(targetfile, localfile):
    ip = jenkinsip
    port = jenkinsfileport
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    localdir = os.path.split(localfile)[0]
    filestat = 0
    if not os.path.exists(localdir):
        try:
            os.makedirs(localdir)
        except:
            logger.error(u'创建%s目录失败', localdir)
    try:
        s.connect((ip, int(port)))
        client_command = "get %s" % targetfile
        s.send(client_command)
        data = s.recv(4096)
        if data == 'ready':
            f = open(localfile, 'wb+')
            while True:
                data = s.recv(4096)
                if data == 'EOF':
                    logger.error(u'文件%s传输完成' % localfile)
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
@checklogin
def project_edit(request, *args, **kwargs):
    cname = TITLE
    privage = kwargs.get("privage")  # 权限，0为未登录，2为管理员，3为普通用户
    username = kwargs.get("username")
    isadmin = kwargs.get("isadmin")
    if request.method == 'GET':
        svnuser = get_svnauth(False)  # svn认证数据
        mavenlist = get_mavenpara(False)  # maven参数列表
        id = request.GET.get('id', False)  # 获取ID
        result = all_get_one('project', id)
        if result:
            proname = result.Pro_name
            prodesc = result.Pro_desc
            proport = result.Pro_port
            svn_ip = result.svn_ip
            certificateid = result.certificateid
            mavenpara = result.mavenpara
            buildtype = result.buildtype
            maillist = result.maillist
            scriptlist = result.scriptlist
            enableweb = result.enableweb
            rpcmemory = result.rpcmemory
            webmemory = result.webmemory
            memlist = [w * 1024 for w in range(1, 11)]  # 容器内存大小列表
            return render_to_response('project/editproj.html', locals())
        else:
            return HttpResponse(messageindex % ('记录不存在', '/project/list/'))
    else:
        id = request.POST.get('id', False)
        proname = request.POST.get('proname', False)
        prodesc = request.POST.get('prodesc', False)
        prosvn = request.POST.get('prosvn', False)
        proport = request.POST.get('proport', False)
        svnuser = request.POST.get('certificateid', False)

        # 查询这个的目的是给jenkins创建项目用，jenkins必须用certificateid
        certificateid = get_svnauthname(svnuser)
        if not certificateid:
            return HttpResponse(message % 'SVN选择有误或记录不存在')
        certificateid = certificateid.svncode  # 查询到真正的svnid信息

        # 查询这个的目的是给jenkins创建项目用，jenkins必须用maven真实参数
        mavenparaname = request.POST.get('mavenpara', False)
        mavenpara = get_mavenhname(mavenparaname)
        if not mavenpara:
            return HttpResponse(message % 'Maven选择有误或记录不存在')
        mavenpara = mavenpara.paravalue  # 查询到真正的maven信息
        enableweb = request.POST.get('enableweb', False)
        buildtype = request.POST.get('buildtype', False)
        maillist = request.POST.get('maillist', False)
        scriptlist = request.POST.get('scriptlist', False)
        rpcmemory = request.POST.get('rpcmemory', False)
        if int(enableweb):
            webmemory = request.POST.get('webmemory', False)
        else:
            webmemory = 0
        if maillist and maillist[0] != ",":
            maillist = ',' + maillist
        if not (proname and prodesc and prosvn and buildtype and proport):
            return HttpResponse(messageindex % ('提交数据有误', '/project/list/'))
        result = update_project(id, proname, prodesc, proport, prosvn, svnuser, mavenparaname, buildtype, username,
                                maillist, scriptlist, enableweb, rpcmemory, webmemory)
        svn_ip = prosvn
        jkserver = jenkins_tools(jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig)
        jserver = jkserver.createserver()
        jkresult = jkserver.editjob(jserver, proname, prodesc, prosvn, certificateid, mavenpara, maillist, scriptlist)
        if result and jkresult:
            localmessage = "更新成功"
        elif result and not jkresult:
            localmessage = "数据库更新成功，后端jenkins更新失败"
        elif not result and jkresult:
            localmessage = "数据库更新失败，后端jenkins更新成功"
        else:
            localmessage = "更新失败"
        svnuser = get_svnauth(False)  # svn认证数据
        mavenlist = get_mavenpara(False)  # maven参数列表
        memlist = [w * 1024 for w in range(1, 11)]  # 容器内存大小列表
        return HttpResponse(messageindex % (localmessage, '/project/edit/?id=%s' % id))
        # return render_to_response('project/editproj.html', locals())


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
def build_project(Pro_name, buildlog, buildtype, isweb):
    pjuuid = buildlog  # 保存uuid,方便打印日志
    jkserver = jenkins_tools(jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig)  # 实例化jenkins_tools类
    jenkinsserver = jkserver.createserver()  # 创建一个jeknins 服务器对象
    if jenkinsserver:  # jenkins服务对像创建成功
        jkresult, relog, reinfo, buildseq = jkserver.bulidjob(jenkinsserver,
                                                              Pro_name)  # 接收返回三个参数，第一个为构建结果，第二个为日志，第三个为信息
        svnversion = reinfo.get('changeSet').get('revisions')[0].get('revision')
        if jkresult:  # 如果构建成功
            if isweb == 1:
                fileweb = str(buildtype.split('.')[0]) + '-web-' + str(
                    time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time()))) + '-' + \
                          str(svnversion) + '.' + str(buildtype.split('.')[1])  # web项目名
                # fileweb = PROJECTPATH + '/' + Pro_name + '/' + fileweb  # 只有使用本机存的时候才用这句
                findweb = "%s-web.jar" % buildtype.split('.')[0]  # web项目搜索码
                #pkgweb = re.search(".*%s.*" % findweb, relog).group(0).split(":")[1].strip()  # 构建生成的web包名
                pkgweb = re.findall(".*Archiving.*%s.*" % findweb, relog)[0].split()[2].strip() # 构建生成的web包名
                logger.info(u"项目%s构建生成的web包名为：%s" % (Pro_name, pkgweb))
            else:
                fileweb = "None"
                pkgweb = "None"

            filename = str(buildtype.split('.')[0]) + '-' + str(
                time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time()))) + '-' + \
                       str(svnversion) + '.' + str(buildtype.split('.')[1])  # rpc项目名
            # filename = PROJECTPATH + '/' + Pro_name + '/' + filename  # 只有使用本机存的时候才用这句
            pkgrpc = re.findall(".*Archiving.*%s.*" % buildtype, relog)[0].split()[2].strip()  # 构建生成的rpc包名
            logger.info(u"项目%s构建生成的rpc包名为：%s" % (Pro_name, pkgrpc))
            deletepath = pkgrpc.split(Pro_name)[0].strip()  # jenkins工作区间目录
            result = etcdfilecopy(Pro_name, pkgrpc, pkgweb, filename, fileweb, deletepath, isweb, svnversion)
            if result:
                logger.info(u"项目%s文件复制信息写入etcd成功" % Pro_name)
            pjname = Pro_name.split("_")[0]  # 取项目名以_号分隔的第一段，svn中是这样存放
            filename = "%s/%s/%s/%s" % (svnurl, pjname, svnversion, filename)  # rpc项目svn的链接地址
            if isweb:  # 如果启用web项目
                fileweb = "%s/%s/%s/%s" % (svnurl, pjname, svnversion, fileweb)  # rpc项目svn的链接地址
            else:
                fileweb = "None"

            # 下面这段只有在使用本地存储构建产物时才需要，把构建产特存到svn中不需要
            # if isweb == 1:
            #     getfile(pkgweb, fileweb)  # 拉取web项目包到本地
            # logger.info(u"开始复制文件到本地，源文件%s，目标文件%s" % (pkgrpc, filename))
            # getfile(pkgrpc, filename)  # 接取构件文件到本地
            # logger.info(u"项目%s文件复制完成，源文件%s，目标文件%s" % (Pro_name, pkgrpc, filename))
            try:
                logger.info(u"项目%s开始更新数据库，参数为：uuid:%s，file:%s，web:%s,svn:%s,seq:%s,log:%s"
                            % (Pro_name, buildlog, filename, fileweb, svnversion, buildseq, relog))
                builddata = project_build.objects.get(buildlog=str(pjuuid))
                logger.info(u"项目%s记录已找到" % Pro_name)
                builddata.success = 1
                builddata.file = str(filename)
                builddata.fileweb = str(fileweb)
                builddata.svnversion = int(svnversion)
                builddata.buildlog = str(relog)
                builddata.buildseq = int(buildseq)
                builddata.save()
                logger.info(u"项目%s更新完成%s" % Pro_name)
            except Exception, e:
                logger.error(u'更新构建记录出错，构建记录uuid：%s，错误代码%s' % (pjuuid, e))
        else:
            try:
                builddata = project_build.objects.get(buildlog=buildlog)
                builddata.success = 0
                builddata.file = 'Nothing'
                builddata.fileweb = 'None'
                builddata.svnversion = svnversion
                builddata.buildlog = relog
                builddata.buildseq = buildseq
                builddata.save()
            except Exception, e:
                logger.error(u'更新构建记录出错，构建记录uuid：%s，错误代码%s' % (pjuuid, e))
    else:
        try:
            builddata = project_build.objects.get(buildlog=buildlog)
            builddata.success = 0
            builddata.file = 'Nothing'
            builddata.fileweb = 'None'
            builddata.svnversion = 0
            builddata.buildlog = 'Nothing'
            builddata.buildseq = 0
            builddata.save()
        except Exception, e:
            logger.error(u'Jenkins服务器出现错误，构建记录uuid：%s，错误代码%s' % (pjuuid, e))


# 构建项目
@checklogin
def project_buildadd(request, *args, **kwargs):
    cname = TITLE
    privage = kwargs.get("privage")  # 权限，0为未登录，2为管理员，3为普通用户
    username = kwargs.get("username")
    isadmin = kwargs.get("isadmin")
    if request.method == "GET":
        projectdata = get_project(False)
        if projectdata:
            return render_to_response('project/addbuild.html', locals())
        else:
            return HttpResponse(messageindex % ('获取数据失败,请先添加项目', '/project/add/'))
    else:
        Pro_id = request.POST.get('Pro_id', False)
        if not (Pro_id):
            return HttpResponse(messageindex % ('提交数据有误', '/project/buildadd/'))
        projectdata = all_get_one('project', Pro_id)
        Pro_name = projectdata.Pro_name  # 项目名
        isweb = projectdata.enableweb  # 是否启用web

        # 检测是否项目刚提交构建
        try:
            if project_build.objects.filter(Pro_name=Pro_name).exists():
                record = project_build.objects.filter(Pro_name=Pro_name).order_by('-id')[0]
                oldtime = time.mktime(time.strptime(str(record.builddate), "%Y-%m-%d %H:%M:%S"))
                timelag = time.time() - oldtime
                if timelag <= 180:  # 同一个项目180秒内只许构建一次
                    projectdata = get_project(False)
                    localmessage = '项目%s上一次构建还没有完成，请过3分钟再试' % Pro_name
                    return render_to_response('project/addbuild.html', locals())
        except:
            pass
        buildtype = projectdata.buildtype  # 构建类型
        buildtime = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        buildlog = str(uuid.uuid4())
        result = add_project_build(Pro_id, Pro_name, buildtime, 2, "", 0, username, buildlog, 0)
        t = threading.Thread(target=build_project, args=(Pro_name, buildlog, buildtype, isweb,))  # 启动多线程
        t.start()
        time.sleep(2)
        if request:
            localmessage = "项目%s构建添加成功，请在构建列表中查看是否成功" % Pro_name
        else:
            localmessage = "项目%s添加失败" % Pro_name
        projectdata = get_project(False)
        return render_to_response('project/addbuild.html', locals())


# 构建修改
@checklogin
def project_buildedit(request, *args, **kwargs):
    cname = TITLE
    privage = kwargs.get("privage")  # 权限，0为未登录，2为管理员，3为普通用户
    username = kwargs.get("username")
    isadmin = kwargs.get("isadmin")
    if request.method == 'GET':
        id = request.GET.get('id', False)  # 获取ID
        result = all_get_one('project_build', id)
        if result:
            Pro_id = result.Pro_id
            Pro_name = result.Pro_name
            builddate = result.builddate
            builddate = time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.localtime(time.mktime(time.strptime(str(builddate), "%Y-%m-%d %H:%M:%S"))))
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
        if not (Pro_name and builddate and (success in [0, 1]) and file and svnversion and username and buildseq):
            return HttpResponse(messageindex % ('提交数据有误', '/project/buildlist/'))
        result = update_project_build(id, Pro_id, Pro_name, builddate, success, file, svnversion, username, buildseq)
        if result:
            localmessage = "更新成功"
        else:
            localmessage = "更新失败"
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


# svn用户添加
@checklogin
def svnuser_add(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == 'GET':
            return render_to_response("project/jenkinssvnadd.html", locals())
        else:
            svnuser = request.POST.get('svnuser', False)
            svncode = request.POST.get('svncode', False)
            if not (svnuser and svncode):
                return HttpResponse(message % '输入有误')
            else:
                result = addsvnuser(svnuser, svncode)
                if result:
                    localmessage = "添加成功"
                else:
                    localmessage = "添加失败"
                return render_to_response("project/jenkinssvnadd.html", locals())
    else:
        return HttpResponse(message % '你没有模块权限')


# svn用户列表
@checklogin
def svnuser_list(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        keyword = request.GET.get('keyword', '')
        page = request.GET.get('page', '')
        count = 0  # 总记录数
        peritem = 10  # 每页记录数
        if keyword:  # 带搜索的处理
            data = get_svnauth(keyword)  # 查询权限说明为关键词的记录
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
            data = get_svnauth(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/project/svnlist/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_svnauth(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/project/svnlist/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render_to_response("project/jenkinssvnlist.html", locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


# svn用户编辑
@checklogin
def svnuser_edit(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == 'GET':
            id = request.GET.get('id', '')  # 获取用户名
            result = all_get_one('svnauth', id)
            if result:
                svnuser = result.svnuser
                svncode = result.svncode
                return render_to_response("project/jenkinssvnedit.html", locals())
            else:
                return HttpResponse(message % '记录不存在')
        else:
            id = request.POST['id'].encode('utf-8')
            svnuser = request.POST['svnuser'].encode('utf-8')
            svncode = request.POST['svncode'].encode('utf-8')
            result = update_svnauth(id, svnuser, svncode)
            if result:
                localmessage = "更新成功"
            else:
                localmessage = "更新失败"
            return render_to_response("project/jenkinssvnedit.html", locals())
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# svn用户删除
@checklogin
def svnuser_del(request, *args, **kwargs):
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == "GET":
            id = request.GET.get('id', '')
            if not id:
                return HttpResponse(message % '操作错误')
            else:
                result = all_delete_one('svnauth', id)
                if result:
                    return HttpResponse('svn认证删除成功')
                else:
                    return HttpResponse('删除失败')
        elif request.method == "POST":
            svn_list = request.POST.get('id', '')
            if not svn_list:
                return HttpResponse('没有选中记录')
            svn_list1 = svn_list.split(',')
            for i in svn_list1:
                all_delete_one('svnauth', i)
            return HttpResponse('删除成功')
        else:
            return HttpResponse('错误请求')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# maven参数添加
@checklogin
def mavenpara_add(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == 'GET':
            return render_to_response("project/mavenparaadd.html", locals())
        else:
            paraname = request.POST.get('paraname', False)
            paravalue = request.POST.get('paravalue', False)
            if not (paraname and paravalue):
                return HttpResponse(message % '输入有误')
            else:
                result = addmavenpara(paraname, paravalue)
                if result:
                    localmessage = "添加成功"
                else:
                    localmessage = "添加失败"
                return render_to_response("project/mavenparaadd.html", locals())
    else:
        return HttpResponse(message % '你没有模块权限')


# maven参数列表
@checklogin
def mavenpara_list(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        keyword = request.GET.get('keyword', '')
        page = request.GET.get('page', '')
        count = 0  # 总记录数
        peritem = 10  # 每页记录数
        if keyword:  # 带搜索的处理
            data = get_mavenpara(keyword)  # 查询权限说明为关键词的记录
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
            data = get_mavenpara(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/project/mavenlist/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_mavenpara(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/project/mavenlist/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render_to_response("project/mavenparalist.html", locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


# maven参数编辑
@checklogin
def mavenpara_edit(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == 'GET':
            id = request.GET.get('id', '')  # 获取用户名
            result = all_get_one('mavenpara', id)
            if result:
                paraname = result.paraname
                paravalue = result.paravalue
                return render_to_response("project/mavenparaedit.html", locals())
            else:
                return HttpResponse(message % '记录不存在')
        else:
            id = request.POST['id'].encode('utf-8')
            paraname = request.POST['paraname'].encode('utf-8')
            paravalue = request.POST['paravalue'].encode('utf-8')
            result = update_mavenpara(id, paraname, paravalue)
            if result:
                localmessage = "更新成功"
            else:
                localmessage = "更新失败"
            return render_to_response("project/mavenparaedit.html", locals())
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# maven参数删除
@checklogin
def mavenpara_del(request, *args, **kwargs):
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == "GET":
            id = request.GET.get('id', '')
            if not id:
                return HttpResponse(message % '操作错误')
            else:
                result = all_delete_one('mavenpara', id)
                if result:
                    return HttpResponse('Maven参数删除成功')
                else:
                    return HttpResponse('删除失败')
        elif request.method == "POST":
            maven_list = request.POST.get('id', '')
            if not maven_list:
                return HttpResponse('没有选中记录')
            maven_list1 = maven_list.split(',')
            for i in maven_list1:
                all_delete_one('mavenpara', i)
            return HttpResponse('删除成功')
        else:
            return HttpResponse('错误请求')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')
