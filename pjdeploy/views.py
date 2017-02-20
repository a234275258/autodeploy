# coding: utf-8
from django.shortcuts import render_to_response
from autodeploy.settings import TITLE, URL, DEFAULT_FROM_EMAIL, DBHOST, message, messageindex, \
    logger, etcdip, etcdport
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.safestring import mark_safe
from project.project_api import get_project, get_projectport, get_projectsvn, get_projectfile
from pjdeploy_api import pjdeploy_table_add, get_onepjdeploy, modify_logpjdeploy, get_pjdeploy, \
    update_pjdeploy, get_pjdeploy_per, pjrollbackadd, modify_pjrollback, get_pjrollback, \
    update_rollback, get_pjrollback_per, get_onerollback
from autodeploy.autodeploy_api import is_login, all_get_one, all_delete_one, try_int
from autodeploy.pagehelper import pagehelper, generatehtml
from project.models import project_build
import time
import etcd
import uuid
import re
import threading
import datetime


# Create your views here.

def initetcd():  # 检测etcd是否正常
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        basekey = '/node/'  # 从node目录查找
        try:
            client.get(basekey)  # 如果key存在
        except:
            pass
        return 1
    except:
        return 0


# 操作etcd函数,传入参数为项目名，文件名，端口，是否反向代理，复本数
def opetcd(proname, filename, port, isagent, replics, uchar):
    k8snode = []  # node结点列表
    k8smaster = []  # k8smaster列表
    k8sagent = []  # k8sagent列表
    iplist = []  # ip列表,用作日志收集
    result = initetcd()  # 判断etcd是否正常
    if not result:
        logger.error(u'etcd服务器%s无法连接' % etcd)
        return 0
    try:
        client = etcd.Client(host=etcdip, port=int(etcdport))
        basekey = '/node/'
        result = client.read(basekey)  # 读取etcd中/node中所有的信息
        for i in result.children:  # 遍历所有信息，并按类型分别放入不同的列表中
            if re.search("k8snode", i.key):
                k8snode.append(i.key)
                iplist.append(str(i.key).split('-')[1])

            if str(replics) != "":   # 如果复本数不为空才执行，为空为回退
                if re.search("k8smaster", i.key):
                    k8smaster.append(i.key)
                    iplist.append(str(i.key).split('-')[1])

            if str(isagent) != "":  # 如果复本数不为空才执行，为空为回退
                if re.search("k8sagent", i.key):
                    k8sagent.append(i.key)
                    iplist.append(str(i.key).split('-')[1])

        if len(k8snode) > 0:
            for i in range(len(k8snode)):
                key = k8snode[i] + '/' + "deploy-" + uchar
                value = '{"pjname":"%s", "file":"%s"}' % (proname, filename)
                client.set(key, value)
        else:
            logger.info(u"暂时没有node结点")

        if str(replics) != "":  # 如果复本数不为空才执行，为空为回退
            if len(k8smaster) > 0:
                for i in range(len(k8smaster)):
                    key = k8smaster[i] + '/' + "deploy-" + uchar
                    value = '{"pjname":"%s", "port":"%s", "replics":"%s", "isagent":"%s"}' % (
                        proname, port, replics, isagent)
                    client.set(key, value)
            else:
                logger.info(u"暂时没有master结点")

        if str(isagent) != "":  # 如果复本数不为空才执行，为空为回退
            if len(k8sagent) > 0:
                if isagent == 1:
                    for i in range(len(k8sagent)):
                        key = k8sagent[i] + '/' + "deploy-" + uchar
                        value = '{"pjname":"%s", "port":"%s"}' % (proname, port)
                        client.set(key, value)

            else:
                logger.info(u"暂时没有反向代理结点")
    except Exception, e:
        logger.error(u'etcd服务器%s无法连接' % e)
    finally:
        k8snode = []
        k8smaster = []
        k8sagent = []
    return iplist


def totallog(modules, uchar, iplist):  # 收集日志
    try:
        time.sleep(60)  # 暂停60秒，如果单次部署时间长可以加长，如180秒
        if modules == "pjdeploy":  # 如果是项目部署
            record = get_onepjdeploy(uchar)  # 到部署表中取记录
        else:
            record = get_onerollback(uchar)  # 到回退表中取记录
        if not record:
            return 0
        client = etcd.Client(host=etcdip, port=int(etcdport))
        basekey = '/node/'
        logdetail = ""
        logger.info(u'uuid号%s在etcd中的次数为%s' % (uchar, len(iplist)))
        result = client.read(basekey)  # 读取etcd中/node中所有的信息
        for i in result.children:  # 遍历所有信息，并按类型分别放入不同的列表中
            if i.dir and str(i.key).split('-')[1] in iplist:
                sonresult = client.read(str(i.key))
                for j in sonresult.children:  # 组装日志
                    if "log" in str(j.key) and uchar in str(j.key):
                        logdetail += "+++++++++++++++++++++++++++++++++++++++++\n"
                        logdetail += str(j.key).split('/')[-1].split('-')[0]
                        logdetail += "\n+++++++++++++++++++++++++++++++++++++++++\n"
                        logdetail += j.value
                        logdetail += "\n=========================================\n"
                        try:
                            client.delete(j.key)
                        except:
                            pass
        if modules == "pjdeploy":
            modify_logpjdeploy(uchar, logdetail)
        else:
            modify_pjrollback(uchar, logdetail)
        logger.info(u'uuid为%s的日志为%s' % (uchar, logdetail))
    except Exception, e:
        logger.info(u"日志汇总出现异常,%s" % e)


def getport(request):  # 执行ajax请求
    if request.method == 'POST':
        pjname = request.POST.get('pjname', False)
        if pjname:
            port = get_projectport(pjname)
        else:
            port = '查询端口出错，请手动输入'
        svnlist = get_projectsvn(pjname)
        svnlist = list(svnlist)
        svnlist = svndistinct(svnlist)  # 去重
        svnlisttemp = ""
        if not svnlist:
            svnlisttemp = "项目没有成功构建记录"
        else:
            for i in range(len(svnlist)):
                if i == len(svnlist) - 1:
                    svnlisttemp += str(svnlist[i])
                else:
                    svnlisttemp = svnlisttemp + str(svnlist[i]) + ":"
        return HttpResponse("%s-%s" % (svnlisttemp, port))


def svndistinct(svnlist):  # svn版本号去重，传入svn版本列表
    svnlist = map(lambda x: x.get('svnversion'), svnlist)
    svntemplist = []
    for i in svnlist:  # 遍历整个列表
        if i not in svntemplist:  # 如果不在svntemplist中就添加，达到去重目的
            svntemplist.append(i)
    return svntemplist


def pjdeploy_add(request):  # 添加部署
    global message
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == "GET":
        projectdata = get_project(False)
        pjname = ""
        for i in projectdata:
            pjname = i.Pro_name
            break
        port = get_projectport(pjname)  # 获取第一个项目端口，让网页一加载就把端口读出来
        svnlist = get_projectsvn(pjname)
        svnlist = list(svnlist)
        svnlist = svndistinct(svnlist)  # 去重
        return render_to_response('pjdeploy/adddeploy.html', locals())
    else:  # POST方法
        Pro_name = request.POST.get('Pro_name', False)
        version = request.POST.get('version', False)
        comment = request.POST.get('comment', False)
        replicas = request.POST.get('replicas', False)
        isagent = request.POST.get('isagent', False)
        proport = request.POST.get('proport', False)
        if not (Pro_name and version and comment and replicas and isagent and proport):
            return HttpResponse(message % '获取数据有误')
        if project_build.objects.filter(Pro_name=Pro_name).filter(svnversion=version).exists():  # 如果数据库中有数据
            build = project_build.objects.filter(Pro_name=Pro_name).order_by('-id')[0]
            if build.success != 1:
                return HttpResponse(message % '你所选的版本号没有成功构建的记录，请重新构建再部署')
        else:
            return HttpResponse(message % '请重新构建再部署')
        deployfile = project_build.objects.filter(Pro_name=Pro_name).filter(svnversion=version).filter(success='1') \
            .order_by('-id')[0].file  # 部署文件
        Publish_time = time.strftime('%Y-%m-%d %H:%M:%S')  # 取当前时间
        success = 2
        uchar = str(uuid.uuid4())  # uuid,避免重复
        if '是' in isagent:
            # agent = 1
            isagent = 1
        else:
            # agent = 0
            isagent = 0
        result = pjdeploy_table_add(Pro_name, version, comment, Publish_time, replicas, isagent, proport, deployfile,
                                    success,
                                    username, uchar)
        if result:
            localmessage = "项目部署添加成功，请在部署列表中查看是否成功"
            iplist = opetcd(Pro_name, deployfile, proport, isagent, replicas, uchar)  # 数据库入库成功，开始写入etcd
            time.sleep(3)  # 暂停3秒
            t = threading.Thread(target=totallog, args=('pjdeploy', uchar, iplist,))  # 启动多线程
            t.start()
            time.sleep(1)
        else:
            localmessage = "项目部署添加失败"
        projectdata = get_project(False)
        pjname = ""
        for i in projectdata:
            pjname = i.Pro_name
            break
        port = get_projectport(pjname)  # 获取第一个项目端口，让网页一加载就把端口读出来
        svnlist = get_projectsvn(pjname)
        svnlist = list(svnlist)
        svnlist = svndistinct(svnlist)  # 去重
        return render_to_response('pjdeploy/adddeploy.html', locals())


def pjdeploy_list(request):  # 部署列表
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
            data = get_pjdeploy(keyword)  # 查询权限说明为关键词的记录
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
            data = get_pjdeploy(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/pjdeploy/list/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_pjdeploy(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/pjdeploy/list/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render_to_response('pjdeploy/deploylist.html', locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


# 查看构建日志
def deploylog(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    id = request.GET.get('id', False)
    if not id:
        return HttpResponse(message % '获取数据错误')
    record = all_get_one('pjdeploy', id)
    if record:
        deploylogstr = re.sub('\n', '<br>', record.deploylog)
        deploylogstr = mark_safe(deploylogstr)
        svnversion = record.version
        Pro_name = record.Pro_name
        return render_to_response('pjdeploy/deploylog.html', locals())
    else:
        return HttpResponse(message % '获取数据错误')


def pjdeploy_edit(request):  # 编辑部署记录
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == 'GET':
        id = request.GET.get('id', False)  # 获取ID
        result = all_get_one('pjdeploy', id)
        Pro_name = result.Pro_name
        version = result.version
        comment = result.comment
        Publish_time = result.Publish_time
        replicas = result.replicas
        isagent = result.isagent
        pjfile = result.file  # 改名避免与系统关键字冲突
        success = result.success
        dusername = result.username  # 改名避免冲突
        proport = get_projectport(Pro_name)
        if result:
            return render_to_response('pjdeploy/editdeploy.html', locals())
        else:
            return HttpResponse(messageindex % ('记录不存在', '/project/list/'))
    else:
        id = request.POST.get('id', False)
        Pro_name = request.POST.get('Pro_name', False)
        replicas = request.POST.get('replicas', False)
        isagent = request.POST.get('isagent', False)
        proport = request.POST.get('proport', False)
        comment = request.POST.get('comment', False)
        pjfile = request.POST.get('pjfile', False)
        version = request.POST.get('version', False)
        dusername = username
        if '是' in isagent:
            isagent = 1
        else:
            isagent = 0
        if not (replicas and str(isagent) in "01" and proport and len(comment)):
            return HttpResponse(messageindex % ('提交数据有误', '/pjdeploy/list/'))
        olddata = all_get_one('pjdeploy', id)  # 获取原始记录用于对比
        oldreplicas, oldisagent, oldproport = "", "", ""
        if olddata:
            oldreplicas = olddata.replicas
            oldisagent = olddata.isagent
            oldproport = get_projectport(Pro_name)
        else:
            return HttpResponse(messageindex % ('修改数据失败', '/pjdeploy/list/'))
        if str(oldreplicas) == str(replicas) and str(oldisagent) == str(isagent) and str(oldproport) == str(proport):
            return HttpResponseRedirect("/pjdeploy/edit/?id=%s" % id)  # 如果数据没有修改直接返回
        Publish_time = time.strftime('%Y-%m-%d %H:%M:%S')  # 取当前时间
        Publish_time = datetime.datetime.strptime(str(Publish_time), '%Y-%m-%d %H:%M:%S')  # 把字符型转成datetime型
        success = 2
        uchar = str(uuid.uuid4())  # uuid,避免重复
        result = update_pjdeploy(id, replicas, isagent, proport, comment, username, uchar, success, Publish_time)
        if result:
            localmessage = "项目部署添加成功，请在部署列表中查看是否成功"
            iplist = opetcd(Pro_name, pjfile, proport, isagent, replicas, uchar)  # 数据库入库成功，开始写入etcd
            time.sleep(3)  # 暂停3秒
            t = threading.Thread(target=totallog, args=('pjdeploy', uchar, iplist,))  # 启动多线程
            t.start()
            time.sleep(1)
        else:
            localmessage = "项目部署添加失败"
        return render_to_response('pjdeploy/editdeploy.html', locals())
    return HttpResponse(message % '你没有操作此项目的权限')


def pjdeploy_del(request):  # 删除部署记录
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
                result = all_delete_one('pjdeploy', id)
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
                all_delete_one('pjdeploy', i)
            return HttpResponse('项目删除成功')
        else:
            return HttpResponse('项目删除失败')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


def getsvnfile(request):  # 执行ajax请求
    if request.method == 'POST':
        pjname = request.POST.get('pjname', False)  # 获取项目名
        record = get_pjdeploy_per()  # 获取所有项目最后一次部署信息
        current_version = ""  # 当前svn号
        current_file = ""   # 当前文件
        deploydate = ""  # 最新部署时间
        rolldate = ""    # 最新回退时间
        rollrecord = get_pjrollback_per(pjname)  # 获取回退记录
        for i in record:  # 获取当前部署项目名称的版本号、文件
            if pjname in i:
                current_version = i[2]
                current_file = i[1]
                deploydate = i[3]
                break
        if rollrecord:  # 如果回退有值
            rolldate = rollrecord[0][3]
            if rolldate > deploydate:  # 如果最新回退时间大于最新部署时间，则使用回退表中的当前版本跟文件
                current_version = rollrecord[0][1]
                current_file = rollrecord[0][2]
        svnlist = get_projectsvn(pjname)  # 获取项目所有svn版本列表
        svnlist = list(svnlist)  # 转换成列表
        svnlist = svndistinct(svnlist)  # 去重
        svnlisttemp = ""
        if not svnlist:
            svnlisttemp = "项目没有成功构建记录"
        else:
            for i in range(len(svnlist)):
                if i == len(svnlist) - 1:
                    svnlisttemp += str(svnlist[i])
                else:
                    svnlisttemp = svnlisttemp + str(svnlist[i]) + ":"
        old_file = get_projectfile(pjname, svnlist[0])  # 取文件
        old_file = list(old_file)   # 注意，这个取数据需先转换成列表，再出列表索引取字典值
        if old_file:
            old_file = old_file[0].get('file')
        else:
            old_file = "获取版本号%s文件失败" % svn
        return HttpResponse("%s=%s=%s=%s" % (svnlisttemp, current_version, current_file, old_file))  #返回以-分隔的字符串


def getoldfile(request):  # 执行ajax请求，返回历史文件
    if request.method == 'POST':
        pjname = request.POST.get('pjname', False)  # 获取项目名
        svn = request.POST.get('svn', False)  # 获取项目名
        old_file = get_projectfile(pjname, svn)  # 取文件
        old_file = list(old_file)   # 注意，这个取数据需先转换成列表，再出列表索引取字典值
        if old_file:
            old_file = old_file[0].get('file')
        else:
            old_file = "获取版本号%s文件失败" % svn
        return HttpResponse("%s" % old_file)  # 返回获取到的文件名


# 查看回退日志
def pjdeploy_rollbacklog(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')  # 未登录直接返回
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    id = request.GET.get('id', False)
    if not id:
        return HttpResponse(message % '获取数据错误')
    record = all_get_one('pjrollback', id)
    if record:
        current_version = record.current_version
        old_version = record.old_version
        rollbacklogstr = re.sub('\n', '<br>', record.rollbacklog)
        rollbacklogstr = mark_safe(rollbacklogstr)
        Pro_name = record.Pro_name
        return render_to_response('pjdeploy/rollbacklog.html', locals())
    else:
        return HttpResponse(message % '获取数据错误')


def pjdeploy_rollbackadd(request):  # 添加回退
    global message
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == "GET":
        record = get_pjdeploy_per()  # 获取部署信息
        if not record:
            return HttpResponse(message % '获取部署信息失败')
        pjlist = map(lambda x: x[0], record)   # 获取取目名称
        current_version = ""
        current_file = ""
        deploydate = ""  # 最新部署时间
        rolldate = ""    # 最新回退时间

        rollrecord = get_pjrollback_per(pjlist[0])  # 获取回退记录

        for i in record:  # 获取当前部署项目名称的版本号、文件
            if pjlist[0] in i:
                current_version = i[2]
                current_file = i[1]
                deploydate = i[3]
                break

        if rollrecord:  # 如果回退有值
            rolldate = rollrecord[0][3]
            if rolldate > deploydate:  # 如果最新回退时间大于最新部署时间，则使用回退表中的当前版本跟文件
                current_version = rollrecord[0][1]
                current_file = rollrecord[0][2]

        svnlist = get_projectsvn(pjlist[0])
        svnlist = list(svnlist)
        svnlist = svndistinct(svnlist)
        if not svnlist:
            return HttpResponse(message % '获取svn版本信息失败')
        old_file = get_projectfile(pjlist[0], svnlist[0])  # 取文件
        old_file = list(old_file)   # 注意，这个取数据需先转换成列表，再出列表索引取字典值
        old_file = old_file[0].get('file')
        return render_to_response("pjdeploy/addpjrollback.html", locals())
    else:  # POST方法
        Pro_name = request.POST.get('Pro_name', False)
        current_version = request.POST.get('current_version', False)
        old_version = request.POST.get('old_version', False)
        current_file = request.POST.get('current_file', False)
        old_file = request.POST.get('old_file', False)
        comment = request.POST.get('comment', False)
        if not (Pro_name and current_version and old_version and current_file and old_file and comment):
            return HttpResponse(message % '获取数据有误')
        Publish_time = time.strftime('%Y-%m-%d %H:%M:%S')  # 取当前时间
        success = 2
        uchar = str(uuid.uuid4())  # uuid,避免重复
        if old_version == current_version:
            return HttpResponse(messageindex % ('两次svn版本相同,请重新设置', '/pjdeploy/rollbackadd/'))
        result = pjrollbackadd(Pro_name, current_version, old_version, current_file, old_file, comment, Publish_time, success, uchar, username)
        if result:
            localmessage = "项目回退添加成功，请在回退列表中查看是否成功"
            iplist = opetcd(Pro_name, old_file, "", "", "", uchar)  # 数据库入库成功，开始写入etcd
            time.sleep(3)  # 暂停3秒
            t = threading.Thread(target=totallog, args=('pjrollback', uchar, iplist,))  # 启动多线程
            t.start()
            time.sleep(1)
        else:
            localmessage = "项目回退添加失败"
        record = get_pjdeploy_per()
        if not record:
            return HttpResponse(message % '获取部署信息失败')
        pjlist = map(lambda x: x[0], record)  # 获取取目名称
        current_version = ""
        current_file = ""
        for i in record:  # 获取当前部署项目名称的版本号、文件
            if pjlist[0] in i:
                current_version = i[2]
                current_file = i[1]
                break
        svnlist = get_projectsvn(pjlist[0])
        svnlist = list(svnlist)
        svnlist = svndistinct(svnlist)
        if not svnlist:
            return HttpResponse(message % '获取svn版本信息失败')
        old_file = get_projectfile(pjlist[0], svnlist[0])  # 取文件
        old_file = list(old_file)  # 注意，这个取数据需先转换成列表，再出列表索引取字典值
        old_file = old_file[0].get('file')
        return render_to_response('pjdeploy/addpjrollback.html', locals())


def pjdeploy_rollbacklist(request):  # 回退记录列表
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
            data = get_pjrollback(keyword)  # 查询权限说明为关键词的记录
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
            data = get_pjrollback(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/pjdeploy/rollbacklist/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_pjrollback(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/pjdeploy/rollbacklist/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render_to_response('pjdeploy/rollbacklist.html', locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


def pjdeploy_rollbackedit(request):  # 编辑回退记录
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == 'GET':
        id = request.GET.get('id', False)  # 获取ID
        result = all_get_one('pjrollback', id)
        Pro_name = result.Pro_name
        current_version = result.current_version
        old_version = result.old_version
        current_file = result.current_file
        old_file = result.old_file
        comment = result.comment
        Publish_time = result.Publish_time
        success = result.success
        dusername = result.username  # 改名避免冲突
        if result:
            return render_to_response('pjdeploy/editpjrollback.html', locals())
        else:
            return HttpResponse(messageindex % ('记录不存在', '/project/rollbacklist/'))
    else:
        id = request.POST.get('id', False)
        comment = request.POST.get('comment', False)
        Publish_time = time.strftime('%Y-%m-%d %H:%M:%S')  # 取当前时间
        Publish_time = datetime.datetime.strptime(str(Publish_time), '%Y-%m-%d %H:%M:%S')  # 把字符型转成datetime型
        dusername = username
        Pro_name = request.POST.get('Pro_name', False)
        current_version = request.POST.get('current_version', False)
        old_version = request.POST.get('old_version', False)
        current_file = request.POST.get('current_file', False)
        old_file = request.POST.get('old_file', False)
        success = request.POST.get('success', False)

        if not (len(comment)):
            return HttpResponse(messageindex % ('提交数据有误', '/pjdeploy/rollbacklist/'))
        result = update_rollback(id,  comment, Publish_time, username)
        if result:
            localmessage = "回退信息修改成功"
        else:
            localmessage = "回退信息修改失败"
        return render_to_response('pjdeploy/editpjrollback.html', locals())
    return HttpResponse(message % '你没有操作此项目的权限')


def pjdeploy_rollbackdel(request):  # 删除回退记录
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
                result = all_delete_one('pjrollback', id)
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
                all_delete_one('pjrollback', i)
            return HttpResponse('项目删除成功')
        else:
            return HttpResponse('项目删除失败')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')