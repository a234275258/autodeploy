# coding: utf-8
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from autodeploy.settings import TITLE, URL, DEFAULT_FROM_EMAIL, DBHOST, message, messageindex, \
    logger, jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig
from autodeploy.autodeploy_api import is_login
from project.project_api import add_project

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
        buildtype = request.POST.get('buildtype', False)
        if not (proname and prodesc and prosvn and buildtype):
            return HttpResponse(message % '提交数据有误')
        result = add_project(proname, prodesc, prosvn, buildtype)
        if request:
            message = "项目添加成功"
        else:
            message = "项目添加失败"
        return render_to_response('project/addproject.html', locals())



# 修改项目
def project_edit(request):
    pass


# 项目列表
def project_list(request):
    pass


# 删除项目
def project_del(request):
    pass
