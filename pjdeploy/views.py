# coding: utf-8
from django.shortcuts import render_to_response
from autodeploy.settings import TITLE, URL, DEFAULT_FROM_EMAIL, DBHOST, message, messageindex, \
    logger, etcdip, etcdport
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.safestring import mark_safe
from project.project_api import get_project, get_projectport, get_projectsvn, get_projectfile
from pjdeploy_api import pjdeploy_table_add, get_onepjdeploy, modify_logpjdeploy, get_pjdeploy, \
    update_pjdeploy, get_pjdeploy_per, pjrollbackadd, modify_pjrollback, get_pjrollback, \
    update_rollback, get_pjrollback_per, get_onerollback, get_nginx, get_node, initetcd
from autodeploy.autodeploy_api import is_login, all_get_one, all_delete_one, try_int
from autodeploy.pagehelper import pagehelper, generatehtml
from project.models import project_build, project
from pjdeploy.kube_api import get_dockerimages, get_kubenamespace
import time
import etcd
import uuid
import re
import threading
import datetime


"""操作etcd函数,传入参数为项目名，rpc项目文件名，端口，是否反向代理，复本数,
   是否启用web，web项目文件名，标志位，new新建，edit为修改,rmemory为rpc容器内存大小
   wmemory为web容器大小,dimages为docker镜像，kubename为名称空间，agentxy为代理协议
   agentm为代理节点，nodem为后端负载节点, agentoper为代理操作，add为添加，remove为移除
   masteroper为master节点操作，add为项目，remove为移除项目
"""


def opetcd(proname, filename, port, isagent, replics, uchar, enableweb, filewebname, replicsweb,
           state, rmemory, wmemory, dimages, kubename, agentxy, agentm, nodem, agentoper, masteroper):
    k8snode = []  # node结点列表
    k8smaster = []  # k8smaster列表
    k8sagent = []  # k8sagent列表
    iplist = []  # ip列表,用作日志收集
    filetype = str(filename).split('.')[-1]  # 取得需要部署的类型，这个决定是部署jar包还是war包
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

            if str(replics) != "":  # 如果复本数不为空才执行，为空为回退,回退只要处理node结点
                if re.search("k8smaster", i.key):
                    k8smaster.append(i.key)
                    iplist.append(str(i.key).split('-')[1])

            if str(isagent) != "":  # 如果复本数不为空才执行，为空为回退,回退只要处理node结点
                if re.search("k8sagent", i.key):
                    k8sagent.append(i.key)
                    iplist.append(str(i.key).split('-')[1])

        if len(k8snode) > 0 and state != "edit":  # 只有新加部署和回退的时候才操作
            for i in range(len(k8snode)):
                key = k8snode[i] + '/' + "deploy-" + uchar
                """值规则：项目名，rpc文件名，是否启用web项目，web项目文件名"""
                value = '{"pjname":"%s", "file":"%s", "enableweb":"%s", "fileweb":"%s","filetype":"%s"}' \
                        % (proname, filename, enableweb, filewebname, filetype)
                client.set(key, value)
        else:
            logger.info(u"暂时没有node结点")

        if str(replics) != "":  # 如果复本数不为空才执行，为空为回退
            if len(k8smaster) > 0:
                for i in range(len(k8smaster)):
                    key = k8smaster[i] + '/' + "deploy-" + uchar
                    """值规则：项目名，端口，rpc复本，是否启用代理，是否启用web项目，web复本，如果web项目不启用，而又启
                        用了代理，那么rpc也要创建服务,rmemory与wmemory为容器内存限制,可使用 replace或先删除rc再创建
                        rc的方式进行更新,dimages为镜像，kubename为名称空间,客户端操作前要判断是不是有handler这个
                        键值，如果有就执行相应的操作，filetype代理部署的类型，取值为jar|war"""
                    if masteroper == "add":
                        value = '{"pjname":"%s", "port":"%s", "replics":"%s", "isagent":"%s", \
                                "enableweb":"%s", "replicsweb":"%s", "rmemory":"%s", "wmemory":"%s", \
                                "dimages":"%s","kubename":"%s","handler":"%s","filetype":"%s"}' \
                                % (proname, port, replics, isagent, enableweb,
                                   replicsweb, rmemory, wmemory, dimages, kubename, masteroper, filetype)
                    else:
                        value = '{"pjname":"%s", "port":"%s", "replics":"%s", "isagent":"%s", \
                        "enableweb":"%s", "replicsweb":"%s", "rmemory":"%s", "wmemory":"%s", \
                        "dimages":"%s","kubename":"%s","handler":"%s","filetype":"%s"}' \
                                % (proname, port, replics, isagent, enableweb,
                                   replicsweb, rmemory, wmemory, dimages, kubename, masteroper, filetype)
                    client.set(key, value)
            else:
                logger.info(u"暂时没有master结点")

        if str(isagent) != "":  # 如果复本数不为空才执行，为空为回退
            if len(k8sagent) > 0:
                if isagent == 1:
                    for i in range(len(k8sagent)):
                        if agentm in str(k8sagent[i]):  # 只对匹配的nginx进行设直
                            key = k8sagent[i] + '/' + "deploy-" + uchar
                            """值规则：项目名，端口号，如果项目名存在已端口一至，不进行操作，如果不同先替换原来的配
                            置文件，进行重新加载，如果新加就直接新建,如果有启用web，配置文件就加上web
                            agentxy为代理协议，nodem为后端负载主机，客户端操作前要判断是不是有handler这个
                            键值，如果有就执行相应的操作"""
                            if agentoper == "add":
                                value = '{"pjname":"%s", "port":"%s", "enableweb":"%s", "agentxy":"%s",\
                                 "nodem":"%s","handler":"%s"}' \
                                        % (proname, port, enableweb, agentxy, nodem, agentoper)
                            else:
                                value = '{"pjname":"%s", "port":"%s", "enableweb":"%s",\
                                        "agentxy":"%s", "nodem":"%s", "handler":"%s"}' \
                                        % (proname, port, enableweb, agentxy, nodem, agentoper)
                            client.set(key, value)
                else:  # 如果不需要反向代理，直接写删除
                    value = '{"pjname":"%s","handler":"remove"}' % proname
                    client.set(key, value)
            else:
                logger.info(u"暂时没有反向代理结点")
    except Exception, e:
        logger.error(u'etcd服务器%s无法连接' % e)
    finally:
        k8snode = []
        k8smaster = []
        k8sagent = []
    return iplist  # 返回IP列表，用于收集日志的线程确定收集哪些日志


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
            pjinfo =project.objects.filter(Pro_name=pjname)[0]
            port = pjinfo.Pro_port
            enableweb = pjinfo.enableweb
            rmemory = pjinfo.rpcmemory
            wmemory = pjinfo.webmemory
        else:
            port = '查询端口出错，请手动输入'
            enableweb = "查询web失败，请手动输入"
            rmemory = "查询容器内存失败，请手动输入"
            wmemory = "查询容器内存失败，请手动输入"
        svnlist = get_projectsvn(pjname)
        svnlist = list(svnlist)
        svnlist = svndistinct(svnlist)  # 去重
        svnlisttemp = ""
        filerpc = "None"   # rpc文件
        fileweb = "None"   # web文件
        if not svnlist:
            svnlisttemp = "项目没有成功构建记录"
        else:
            buildinfo = project_build.objects.filter(Pro_name=pjname). \
                filter(svnversion=int(svnlist[0])).filter(success='1').order_by('-id')[0]
            filerpc = buildinfo.file  # rpc文件
            fileweb = buildinfo.fileweb  # web文件
            for i in range(len(svnlist)):
                if i == len(svnlist) - 1:
                    svnlisttemp += str(svnlist[i])
                else:
                    svnlisttemp = svnlisttemp + str(svnlist[i]) + ":"
        return HttpResponse("%s==%s==%s==%s==%s==%s==%s" % (svnlisttemp, port, enableweb, rmemory, wmemory, filerpc, fileweb))


def svndistinct(svnlist):  # svn版本号去重，传入svn版本列表
    svnlist = map(lambda x: x.get('svnversion'), svnlist)
    svntemplist = []
    for i in svnlist:  # 遍历整个列表
        if i not in svntemplist:  # 如果不在svntemplist中就添加，达到去重目的
            svntemplist.append(i)
    return svntemplist


def pjdeploy_add(request):  # 添加部署
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == "GET":  # get方法准备数据
        projectdata = get_project(False)
        HttpResponse(u"记录数：%s" % projectdata.count())
        pjname = ""
        if not projectdata.count():
            return HttpResponse(messageindex % ('还没有项目，请先添加构建', '/project/add/'))
        else:
            for i in projectdata:
                pjname = i.Pro_name
                break
            pjinfo = project.objects.filter(Pro_name=pjname)[0]  # 查看项目是否启用web工程
            port = pjinfo.Pro_port  # 获取第一个项目端口，让网页一加载就把端口读出来
            svnlisttemp = get_projectsvn(pjname)
            svnlist = list(svnlisttemp)
            svnlist = svndistinct(svnlist)  # 去重
            if len(svnlist):  # 取第一条svn信息相对应的文件
                buildinfo = project_build.objects.filter(Pro_name=pjname).\
                    filter(svnversion=int(svnlist[0])).filter(success='1').order_by('-id')[0]
                filerpc = buildinfo.file    # rpc文件
                fileweb = buildinfo.fileweb  # web文件
            enableweb = pjinfo.enableweb   # 是否启用web
            nginxlist = get_nginx()  # 获取nginx节点列表
            nodelist = get_node()  # 获取node节点列表
            dockerlist = get_dockerimages(False)  # 获取docker列表
            kubelist = get_kubenamespace(False)  # 获取kube名称列表
            rmemory = pjinfo.rpcmemory
            wmemory = pjinfo.webmemory
            memlist = [x*1024 for x in range(1, 11)]  # 生成内存列表
            replist = [x for x in range(1, 6)]
        return render_to_response('pjdeploy/adddeploy.html', locals())
    else:  # POST方法
        Pro_name = request.POST.get('Pro_name', False)
        version = request.POST.get('version', False)
        comment = request.POST.get('comment', False)
        replicas = request.POST.get('replicas', False)
        isagent = request.POST.get('isagent', False)
        proport = request.POST.get('proport', False)
        rmemory = request.POST.get('rmemory', False)
        enableweb = request.POST.get('enableweb', False)
        if "是" in enableweb:  # 判断是否启用
            enableweb = 1
        else:
            enableweb = 0
        if enableweb:
            replicasweb = request.POST.get('replicasweb', False)
            wmemory = request.POST.get('wmemory', False)
        else:
            replicasweb = 0
            wmemory = 0

        dimages = int(request.POST.get('dimages', False))  # docker镜像
        kubename = int(request.POST.get('kubename', False))  # 名称空间
        if isagent:
            agentxy = request.POST.get('agentxy', False)  # 代理协议
            agentm = request.POST.get('agentm', False)  # 代理节点
            nodem = request.POST.getlist('nodem', False)  # 后端负载节点
            if not nodem:
                return HttpResponse(message % '提交数据有误')
            nodemtemp = ""
            for i in range(len(nodem)):  # 拼接字符串,把多个IP拼接成以|分隔的字符串
                if i == (len(nodem) - 1):
                    nodemtemp = nodemtemp + nodem[i]
                else:
                    nodemtemp = nodemtemp + nodem[i] + '|'
            nodem = nodemtemp
        else:
            agentxy = "None"
            agentm = "None"
            nodem = "None"

        if not (Pro_name and version and comment and replicas and isagent
                and dimages and kubename and agentxy
                and agentm and nodem and proport and rmemory):
            return HttpResponse(message % '获取数据有误')
        if project_build.objects.filter(Pro_name=Pro_name).filter(svnversion=version).exists():  # 如果数据库中有数据
            build = project_build.objects.filter(Pro_name=Pro_name).order_by('-id')[0]
            if build.success != 1:
                return HttpResponse(message % '你所选的版本号没有成功构建的记录，请重新构建再部署')
        else:
            return HttpResponse(message % '请重新构建再部署')
        # deployfile = project_build.objects.filter(Pro_name=Pro_name).filter(svnversion=version).filter(success='1') \
        #     .order_by('-id')[0].file  # 部署rpc项目文件
        #
        # if enableweb:  # 如果项目启用web项目
        #     deploywebfile = \
        #         project_build.objects.filter(Pro_name=Pro_name).filter(svnversion=version).filter(success='1').order_by(
        #             '-id')[0].fileweb  # 部署web项目文件
        # else:
        #     deploywebfile = "None"
        filerpc = request.POST.get('filerpc', False)  # 部署rpc项目文件
        if enableweb:
            fileweb = request.POST.get('fileweb', False)  # 部署web项目文件
        else:
            fileweb = "None"
        Publish_time = time.strftime('%Y-%m-%d %H:%M:%S')  # 取当前时间
        success = 2
        uchar = str(uuid.uuid4())  # uuid,避免重复
        if '是' in isagent:
            isagent = 1
        else:
            isagent = 0

        # 添加部署记录
        result = pjdeploy_table_add(Pro_name, version, comment, Publish_time, replicas,
                                    isagent, proport, filerpc, success, username, uchar,
                                    enableweb, replicasweb, fileweb, rmemory, wmemory,
                                    dimages, kubename, agentxy, agentm, nodem)
        dimagesurl = all_get_one("dockerimages", dimages)
        dimagesurl = dimagesurl.durl  # 取docker镜像的地址,写etcd用
        kubenamevalue = all_get_one("kubenamespace", kubename)
        kubenamevalue = kubenamevalue.kvalue  # 取名称空间值,写etcd用

        if result:
            localmessage = "项目%s部署添加成功，请在部署列表中查看是否成功" % Pro_name
            iplist = opetcd(Pro_name, filerpc, proport, isagent, replicas, uchar, enableweb,
                            fileweb, replicasweb, 'new', rmemory, wmemory,
                            dimagesurl, kubenamevalue, agentxy, agentm, nodem, "add", "add")  # 数据库入库成功，开始写入etcd
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
        nginxlist = get_nginx()  # 获取nginx节点列表
        nodelist = get_node()  # 获取node节点列表
        dockerlist = get_dockerimages(False)  # 获取docker列表
        kubelist = get_kubenamespace(False)  # 获取kube名称列表
        replist = [x for x in range(1, 6)]
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
        replicasweb = result.replicasweb
        rmemory = result.rmemory
        wmemory = result.wmemory
        isagent = result.isagent
        pjfile = result.file  # 改名避免与系统关键字冲突
        fileweb = result.fileweb
        enableweb = result.enableweb
        success = result.success
        dusername = result.username  # 改名避免冲突
        proport = get_projectport(Pro_name)
        dimages = int(result.dimages)
        kubename = int(result.kubename)
        agentxy = result.agentxy
        agentm = result.agentm
        nodem = result.nodem.split('|')  # 把现有项目的后端主机负载列表使用|号分隔
        nginxlist = get_nginx()  # 获取nginx主机列表
        nodelist = get_node()  # 获取node主机列表
        for i in nodem:  # 用于生成多选负载主机列表
            for j in nodelist:
                if j.has_key("selected"):  # 判断键值是否已在字典中，还可以使用in
                    continue
                if str(i) == str(j.get("ip")):  # 如果i在跟j的键ip的值相等
                    j["selected"] = "1"
                    break
        memlist = [i * 1024 for i in range(1, 11)]  # 内存列表
        dockerlist = get_dockerimages(False)  # 获取docker镜像列表
        kubelist = get_kubenamespace(False)  # 获取名称空间列表
        replist = [x for x in range(1, 6)]  # 生成复本列表
        if result:
            return render_to_response('pjdeploy/editdeploy.html', locals())
        else:
            return HttpResponse(messageindex % ('记录不存在', '/project/list/'))
    else:
        id = request.POST.get('id', False)
        Pro_name = request.POST.get('Pro_name', False)
        replicas = request.POST.get('replicas', False)
        replicasweb = request.POST.get('replicasweb', False)
        rmemory = request.POST.get('rmemory', False)
        wmemory = request.POST.get('wmemory', False)
        isagent = request.POST.get('isagent', False)
        proport = request.POST.get('proport', False)
        comment = request.POST.get('comment', False)
        pjfile = request.POST.get('pjfile', False)
        version = request.POST.get('version', False)
        filewebname = request.POST.get('fileweb', False)
        memlist = [i * 1024 for i in range(1, 11)]  # 内存列表
        dusername = username
        if '是' in isagent:
            isagent = 1
        else:
            isagent = 0
        if not (replicas and str(isagent) in "01" and proport and len(comment) and str(replicasweb).isdigit()):
            return HttpResponse(messageindex % ('提交数据有误', '/pjdeploy/list/'))

        dimages = int(request.POST.get('dimages', False))  # docker镜像
        kubename = int(request.POST.get('kubename', False))  # 名称空间
        if isagent:
            agentxy = request.POST.get('agentxy', False)  # 代理协议
            agentm = request.POST.get('agentm', False)  # 代理节点
            nodem = request.POST.getlist('nodem', False)  # 后端负载节点
            if not nodem:
                return HttpResponse(message % '提交数据有误')
            nodemtemp = ""
            for i in range(len(nodem)):  # 拼接字符串,把多个IP拼接成以|分隔的字符串
                if i == (len(nodem) - 1):
                    nodemtemp = nodemtemp + nodem[i]
                else:
                    nodemtemp = nodemtemp + nodem[i] + '|'
            nodem = nodemtemp
        else:
            agentxy = "None"
            agentm = "None"
            nodem = "None"

        olddata = all_get_one('pjdeploy', id)  # 获取原始记录用于对比
        oldreplicas, oldisagent, oldproport = "", "", ""
        olddimages, oldkubename, oldagentxy, oldagentm, oldnodem = "", "", "", "", ""
        if olddata:  # 获取修改前的记录，以便跟现有提交的数据做比对，如果相同就不执行后端操作
            oldreplicas = olddata.replicas
            oldisagent = olddata.isagent
            oldproport = get_projectport(Pro_name)
            enableweb = olddata.enableweb
            oldreplicasweb = olddata.replicasweb
            oldrmemory = olddata.rmemory
            oldwmemory = olddata.wmemory
            olddimages = olddata.dimages
            oldkubename = olddata.kubename
            oldagentxy = olddata.agentxy
            oldagentm = olddata.agentm
            oldnodem = olddata.nodem
        else:
            return HttpResponse(messageindex % ('修改数据失败', '/pjdeploy/list/'))
        """下面语句段判断数据是否有变，没有变就不提交"""

        if enableweb:  # 开启web项目的情况
            if str(oldreplicasweb) == str(replicasweb) and str(oldreplicas) == str(replicas) \
                    and str(oldisagent) == str(isagent) and str(oldproport) == str(proport) \
                    and str(oldrmemory) == str(rmemory) and str(oldwmemory) == str(wmemory) \
                    and str(olddimages) == str(dimages) and str(oldkubename) == str(kubename) \
                    and str(oldagentxy) == str(agentxy) and str(oldagentm) == str(agentm) \
                    and str(oldnodem) == str(nodem) and str(oldagentxy) == str(agentxy) \
                    and str(oldagentm) == str(agentm) and str(oldnodem) == str(nodem):
                return HttpResponseRedirect("/pjdeploy/edit/?id=%s" % id)  # 如果数据没有修改直接返回
        else:
            if str(oldreplicas) == str(replicas) and str(oldisagent) == str(isagent) \
                    and str(oldproport) == str(proport) and str(oldrmemory) == str(rmemory) \
                    and str(olddimages) == str(dimages) and str(oldkubename) == str(kubename) \
                    and str(oldagentxy) == str(agentxy) and str(oldagentm) == str(agentm) \
                    and str(oldnodem) == str(nodem):
                return HttpResponseRedirect("/pjdeploy/edit/?id=%s" % id)  # 如果数据没有修改直接返回

        Publish_time = time.strftime('%Y-%m-%d %H:%M:%S')  # 取当前时间
        Publish_time = datetime.datetime.strptime(str(Publish_time), '%Y-%m-%d %H:%M:%S')  # 把字符型转成datetime型
        success = 2
        uchar = str(uuid.uuid4())  # uuid,避免重复
        result = update_pjdeploy(id, replicas, isagent, proport, comment, username, uchar,
                                 success, Publish_time, replicasweb, rmemory, wmemory,
                                 dimages, kubename, agentxy, agentm, nodem)
        dimagesurl = all_get_one("dockerimages", dimages)
        dimagesurl = dimagesurl.durl  # 取docker镜像的地址,写etcd用
        kubenamevalue = all_get_one("kubenamespace", kubename)
        kubenamevalue = kubenamevalue.kvalue  # 取名称空间值,写etcd用
        if result:
            localmessage = "项目%s部署修改成功，请在部署列表中查看是否成功" % Pro_name
            if oldisagent == '1' and str(oldisagent) != str(isagent):  # 如果以前开启反向代理现在又关闭
                iplist = opetcd(Pro_name, pjfile, proport, isagent, replicas, uchar, enableweb, filewebname,
                                replicasweb, 'edit', rmemory, wmemory,
                                dimagesurl, kubenamevalue, agentxy, agentm, nodem, "remove",
                                "remove")  # 数据库入库成功，开始写入etcd
            else:
                iplist = opetcd(Pro_name, pjfile, proport, isagent, replicas, uchar, enableweb, filewebname,
                                replicasweb, 'edit', rmemory, wmemory,
                                dimagesurl, kubenamevalue, agentxy, agentm, nodem, "add", "add")  # 数据库入库成功，开始写入etcd

            time.sleep(3)  # 暂停3秒
            t = threading.Thread(target=totallog, args=('pjdeploy', uchar, iplist,))  # 启动多线程
            t.start()
            time.sleep(1)
        else:
            localmessage = "项目部署修改失败"
        nginxlist = get_nginx()  # 获取nginx主机列表
        nodelist = get_node()  # 获取node主机列表
        for i in nodem.split('|'):  # 用于生成多选负载主机列表
            for j in nodelist:
                if j.has_key("selected"):  # 判断键值是否已在字典中，还可以使用in
                    continue
                if str(i) == str(j.get("ip")):  # 如果i在跟j的键ip的值相等
                    j["selected"] = "1"
                    break
        dockerlist = get_dockerimages(False)  # 获取docker镜像列表
        kubelist = get_kubenamespace(False)  # 获取kube名称列表
        replist = [x for x in range(1, 6)]  # 生成复本列表
        return render_to_response('pjdeploy/editdeploy.html', locals())


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
        current_file = ""  # 当前rpc文件
        current_webfile = ""  # 当前web文件
        enableweb = ""  # 是否启用web
        deploydate = ""  # 最新部署时间
        rolldate = ""  # 最新回退时间
        rollrecord = get_pjrollback_per(pjname)  # 获取回退记录
        for i in record:  # 获取当前部署项目名称的版本号、文件
            if pjname in i:
                current_version = i[2]
                current_file = i[1]
                deploydate = i[3]
                enableweb = i[4]
                current_webfile = i[5]
                break
        if rollrecord:  # 如果回退有值
            rolldate = rollrecord[0][3]
            if rolldate > deploydate:  # 如果最新回退时间大于最新部署时间，则使用回退表中的当前版本跟文件
                current_version = rollrecord[0][1]
                current_file = rollrecord[0][2]
                current_webfile = rollrecord[0][4]
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
        old_file = list(old_file)  # 注意，这个取数据需先转换成列表，再出列表索引取字典值
        if old_file:
            old_webfile = old_file[0].get('fileweb')
            old_file = old_file[0].get('file')
        else:
            old_file = "获取版本号%s文件失败" % svnlist[0]
            old_webfile = "获取版本号%sweb文件失败" % svnlist[0]
        """返回字符串，格式为项目的svn列表，当前版本号，当前rpc文件，当前rpc的回退文件，当前web项目文件，当前web项目
        的回退文件，是否开启web，全部以=号分隔"""
        return HttpResponse("%s=%s=%s=%s=%s=%s=%s" % (svnlisttemp, current_version, current_file,
                                                      old_file, current_webfile, old_webfile, enableweb))


def getoldfile(request):  # 执行ajax请求，返回历史rpc文件,web文件，并以|号分隔
    if request.method == 'POST':
        pjname = request.POST.get('pjname', False)  # 获取项目名
        svn = request.POST.get('svn', False)  # 获取项目名
        old_file = get_projectfile(pjname, svn)  # 取文件
        old_file = list(old_file)  # 注意，这个取数据需先转换成列表，再出列表索引取字典值
        if old_file:
            old_webfile = old_file[0].get('fileweb')  # 要放在第一行，不然对像值会改变
            old_file = old_file[0].get('file')
        else:
            old_file = "获取版本号%s文件失败" % svn
            old_webfile = "获取版本号%sweb项目文件失败" % svn
        return HttpResponse("%s|%s" % (old_file, old_webfile))  # 返回获取到的文件名


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
        pjlist = map(lambda x: x[0], record)  # 获取项目目名称
        current_version = ""
        current_file = ""
        current_webfile = ""
        enableweb = ""
        deploydate = ""  # 最新部署时间
        rolldate = ""  # 最新回退时间

        rollrecord = get_pjrollback_per(pjlist[0])  # 获取回退记录

        for i in record:  # 获取第一个记录的 当前部署项目名称的版本号、文件
            if pjlist[0] in i:
                current_version = i[2]
                current_file = i[1]
                deploydate = i[3]
                enableweb = i[4]
                current_webfile = i[5]
                break

        if rollrecord:  # 如果回退有值
            rolldate = rollrecord[0][3]
            if rolldate > deploydate:  # 如果最新回退时间大于最新部署时间，则使用回退表中的当前版本跟文件,web工程文件
                current_version = rollrecord[0][1]
                current_file = rollrecord[0][2]
                current_webfile = rollrecord[0][4]

        svnlist = get_projectsvn(pjlist[0])
        svnlist = list(svnlist)
        svnlist = svndistinct(svnlist)
        if not svnlist:
            return HttpResponse(message % '获取svn版本信息失败')
        old_file = get_projectfile(pjlist[0], svnlist[0])  # 取文件
        old_file = list(old_file)  # 注意，这个取数据需先转换成列表，再出列表索引取字典值
        old_webfile = old_file[0].get('fileweb')
        old_file = old_file[0].get('file')
        return render_to_response("pjdeploy/addpjrollback.html", locals())
    else:  # POST方法
        Pro_name = request.POST.get('Pro_name', False)
        current_version = request.POST.get('current_version', False)
        old_version = request.POST.get('old_version', False)
        current_file = request.POST.get('current_file', False)
        old_file = request.POST.get('old_file', False)
        current_webfile = request.POST.get('current_webfile', False)
        old_webfile = request.POST.get('old_webfile', False)
        enableweb = request.POST.get('enableweb', False)
        enableweb = 1 if "是" in enableweb else 0
        comment = request.POST.get('comment', False)
        if not (Pro_name and current_version and old_version
                and current_file and old_file and comment and current_webfile and old_webfile):
            return HttpResponse(message % '获取数据有误')
        Publish_time = time.strftime('%Y-%m-%d %H:%M:%S')  # 取当前时间
        success = 2
        uchar = str(uuid.uuid4())  # uuid,避免重复
        if old_version == current_version:
            return HttpResponse(messageindex % ('两次svn版本相同,请重新设置', '/pjdeploy/rollbackadd/'))
        result = pjrollbackadd(Pro_name, current_version, old_version, current_file, old_file,
                               comment, Publish_time, success, uchar, username, enableweb,
                               current_webfile, old_webfile)
        if result:
            localmessage = "项目%s回退添加成功，请在回退列表中查看是否成功" % Pro_name
            iplist = opetcd(Pro_name, old_file, "", "", "", uchar, enableweb,
                            old_webfile, "", "rollback", "", "", "",
                            "", "", "", "", "", "")  # 数据库入库成功，开始写入etcd
            time.sleep(3)  # 暂停3秒
            t = threading.Thread(target=totallog, args=('pjrollback', uchar, iplist,))  # 启动多线程
            t.start()
            time.sleep(1)
        else:
            localmessage = "项目%s回退添加失败" % Pro_name
        record = get_pjdeploy_per()
        if not record:
            return HttpResponse(message % '获取部署信息失败')
        pjlist = map(lambda x: x[0], record)  # 获取取目名称
        current_version = ""
        current_file = ""
        current_webfile = ""
        enableweb = ""
        for i in record:  # 获取第一个记录的  获取当前部署项目名称的版本号、文件
            if pjlist[0] in i:
                current_version = i[2]
                current_file = i[1]
                enableweb = i[4]
                current_webfile = i[5]
                break
        svnlist = get_projectsvn(pjlist[0])
        svnlist = list(svnlist)
        svnlist = svndistinct(svnlist)
        if not svnlist:
            return HttpResponse(message % '获取svn版本信息失败')
        old_file = get_projectfile(pjlist[0], svnlist[0])  # 取文件
        old_file = list(old_file)  # 注意，这个取数据需先转换成列表，再出列表索引取字典值
        old_webfile = old_file[0].get('fileweb')
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
        enableweb = result.enableweb
        current_webfile = result.current_webfile
        old_webfile = result.old_webfile
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
        result = update_rollback(id, comment, Publish_time, username)
        if result:
            localmessage = "回退信息修改成功"
        else:
            localmessage = "回退信息修改失败"
        return render_to_response('pjdeploy/editpjrollback.html', locals())


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
