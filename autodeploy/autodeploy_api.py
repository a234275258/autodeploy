# coding: utf-8
from django.http import HttpResponseRedirect


def is_login(request):  # 检测用户是否登录
    if request.session.get('username', False):  # 如果已登录,直接跳转
        response = HttpResponseRedirect('/index/')
        return response
