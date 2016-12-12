#coding: utf-8
from django.shortcuts import render_to_response
from autodeploy.settings import  TITLE, URL, DEFAULT_FROM_EMAIL, DBHOST, message, messageindex, \
    logger, jenkinsurl, jenkinsuser, jenkinspassword, jenkinsconfig, PROJECTPATH, jenkinsfileport, \
    jenkinsip
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.safestring import mark_safe
from project.project_api import get_project
from autodeploy.autodeploy_api import is_login
from project.models import project_build
import time

# Create your views here.

def pjdeploy_add(request):
    cname = TITLE
    privage = is_login(request)  # 权限，0为未登录，2为管理员，3为普通用户
    if privage == 0:
        return HttpResponseRedirect('/login/')
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if request.method == "GET":
        projectdata = get_project(False)
        return render_to_response('pjdeploy/adddeploy.html', locals())
    else:  # POST方法
        Pro_name = request.POST.get('Pro_name', False)
        version = request.POST.get('version', False)
        comment = request.POST.get('comment', False)
        replicas = request.POST.get('replicas', False)
        isagent = request.POST.get('isagent', False)
        if not(Pro_name and version and comment and replicas and isagent):
            return HttpResponse(message % '获取数据有误')
        if project_build.objects.filter(Pro_name=Pro_name).filter(svnversion=version).exists():  # 如果数据库中有数据
            build = project_build.objects.filter(Pro_name=Pro_name).order_by('-id')[0]
            if build.success != 1:
                return HttpResponse(message % '你所选的版本号没有成功构建的记录，请重新构建再部署')
            return HttpResponse(message % '请重新构建再部署')
        else:
            return HttpResponse(message % '请重新构建再部署')
        Publish_time = time.strftime('%Y-%m-%d %H:%M:%S')
        success = 2


def pjdeploy_list(request):
    pass

def pjdeploy_edit(request):
    pass

def pjdeploy_del(request):
    pass

def pjdeploy_rollbackadd(request):
    pass

def pjdeploy_rollbacklist(request):
    pass

def pjdeploy_rollbackedit(request):
    pass

def pjdeploy_rollbackdel(request):
    pass





