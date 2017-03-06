# coding: utf-8
from django.shortcuts import render_to_response
from autodeploy.settings import TITLE, URL, DEFAULT_FROM_EMAIL, DBHOST, message, messageindex, \
    logger, etcdip, etcdport
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.safestring import mark_safe
from autodeploy.autodeploy_api import checklogin, all_get_one, all_delete_one, try_int
from pjdeploy.kube_api import adddockerimages, get_dockerimages, update_dockerimages, addkubenamespace, \
    get_kubenamespace, update_kubenamespace
from autodeploy.pagehelper import pagehelper, generatehtml


# 镜像docker添加
@checklogin
def dimages_add(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == 'GET':
            return render_to_response("pjdeploy/dockerimageadd.html", locals())
        else:
            dname = request.POST.get('dname', False)
            durl = request.POST.get('durl', False)
            if not (dname and durl):
                return HttpResponse(message % '输入有误')
            else:
                result = adddockerimages(dname, durl)
                if result:
                    localmessage = "添加成功"
                else:
                    localmessage = "添加失败"
                return render_to_response("pjdeploy/dockerimageadd.html", locals())
    else:
        return HttpResponse(message % '你没有模块权限')


# 修改docker镜像
@checklogin
def dimages_edit(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == 'GET':
            id = request.GET.get('id', '')  # 获取用户名
            result = all_get_one('dockerimages', id)
            if result:
                dname = result.dname
                durl = result.durl
                return render_to_response("pjdeploy/dockerimagesedit.html", locals())
            else:
                return HttpResponse(message % '记录不存在')
        else:
            id = request.POST['id'].encode('utf-8')
            dname = request.POST['dname'].encode('utf-8')
            durl = request.POST['durl'].encode('utf-8')
            result = update_dockerimages(id, dname, durl)
            if result:
                localmessage = "更新成功"
            else:
                localmessage = "更新失败"
            return render_to_response("pjdeploy/dockerimagesedit.html", locals())
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# 列出docker镜像
@checklogin
def dimages_list(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        keyword = request.GET.get('keyword', '')
        page = request.GET.get('page', '')
        count = 0  # 总记录数
        peritem = 10  # 每页记录数
        if keyword:  # 带搜索的处理
            data = get_dockerimages(keyword)  # 查询权限说明为关键词的记录
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
            data = get_dockerimages(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/pjdeploy/imageslist/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_dockerimages(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/pjdeploy/imageslist/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render_to_response("pjdeploy/dockerimageslist.html", locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


# 删除docker镜像
@checklogin
def dimages_del(request, *args, **kwargs):
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == "GET":
            id = request.GET.get('id', '')
            if not id:
                return HttpResponse(message % '操作错误')
            else:
                result = all_delete_one('dockerimages', id)
                if result:
                    return HttpResponse('docker镜像删除成功')
                else:
                    return HttpResponse('删除失败')
        elif request.method == "POST":
            docker_list = request.POST.get('id', '')
            if not docker_list:
                return HttpResponse('没有选中记录')
            docker_list1 = docker_list.split(',')
            for i in docker_list1:
                all_delete_one('dockerimages', i)
            return HttpResponse('删除成功')
        else:
            return HttpResponse('错误请求')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# kube名称空间添加
@checklogin
def kube_add(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == 'GET':
            return render_to_response("pjdeploy/kubeadd.html", locals())
        else:
            kname = request.POST.get('kname', False)
            kvalue = request.POST.get('kvalue', False)
            if not (kname and kvalue):
                return HttpResponse(message % '输入有误')
            else:
                result = addkubenamespace(kname, kvalue)
                if result:
                    localmessage = "添加成功"
                else:
                    localmessage = "添加失败"
                return render_to_response("pjdeploy/kubeadd.html", locals())
    else:
        return HttpResponse(message % '你没有模块权限')

# 修改kube名称空间
@checklogin
def kube_edit(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == 'GET':
            id = request.GET.get('id', '')  # 获取用户名
            result = all_get_one('kubenamespace', id)
            if result:
                kname = result.kname
                kvalue = result.kvalue
                return render_to_response("pjdeploy/kubeedit.html", locals())
            else:
                return HttpResponse(message % '记录不存在')
        else:
            id = request.POST['id'].encode('utf-8')
            kname = request.POST['kname'].encode('utf-8')
            kvalue = request.POST['kvalue'].encode('utf-8')
            result = update_kubenamespace(id, kname, kvalue)
            if result:
                localmessage = "更新成功"
            else:
                localmessage = "更新失败"
            return render_to_response("pjdeploy/kubeedit.html", locals())
    else:
        return HttpResponse(message % '你没有操作此项目的权限')


# 列出kube名称空间
@checklogin
def kube_list(request, *args, **kwargs):
    cname = TITLE
    username = kwargs.get("username")
    privage = kwargs.get("privage")
    if privage == 2:
        keyword = request.GET.get('keyword', '')
        page = request.GET.get('page', '')
        count = 0  # 总记录数
        peritem = 10  # 每页记录数
        if keyword:  # 带搜索的处理
            data = get_kubenamespace(keyword)  # 查询权限说明为关键词的记录
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
            data = get_kubenamespace(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)  # 计算分页的类
            totalpage = pageclass.totalpage()  # 总页数
            start = pageclass.prev()  # 开始记录数
            end = pageclass.next1()  # 结束记录数
            data = data[start:end]  # 取当前页要显示的记录
            start = start + 1
            pagehtml = generatehtml('/pjdeploy/kubelist/?page=', page, totalpage)  # 生成分页的html代码
        else:
            page = try_int(page)  # 转为int类型
            data = get_kubenamespace(False)  # 获取所有记录
            count = data.count()  # 获取总记录数
            pageclass = pagehelper(page, count, peritem)
            totalpage = pageclass.totalpage()
            start = int(pageclass.prev())  # 开始记录数
            end = int(pageclass.next1())  # 结束记录数
            data = data[start:end]
            start = start + 1
            pagehtml = generatehtml('/pjdeploy/kubelist/?page=', page, totalpage)
        if not data:
            return HttpResponse(message % '操作错误')
        return render_to_response("pjdeploy/kubelist.html", locals())
    else:
        return HttpResponse(message % '你没有权限访问该模块')


# 删除kube名称空间
@checklogin
def kube_del(request, *args, **kwargs):
    privage = kwargs.get("privage")
    if privage == 2:
        if request.method == "GET":
            id = request.GET.get('id', '')
            if not id:
                return HttpResponse(message % '操作错误')
            else:
                result = all_delete_one('kubenamespace', id)
                if result:
                    return HttpResponse('kubernetes名称删除成功')
                else:
                    return HttpResponse('删除失败')
        elif request.method == "POST":
            kube_list = request.POST.get('id', '')
            if not kube_list:
                return HttpResponse('没有选中记录')
            kube_list1 = kube_list.split(',')
            for i in kube_list1:
                all_delete_one('kubenamespace', i)
            return HttpResponse('删除成功')
        else:
            return HttpResponse('错误请求')
    else:
        return HttpResponse(message % '你没有操作此项目的权限')