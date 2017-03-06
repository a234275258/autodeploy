#coding:utf-8
from django.shortcuts import render
from autodeploy.settings import TITLE
from django.http import HttpResponseRedirect
from django.contrib.sessions.models import Session
from autodeploy.autodeploy_api import get_alldata, last_login, counthosts, countproject, gethosts, \
        getdeployinfo
import datetime


# 计算日期,返回两个日期间相差多少天，多少小时，多少分钟，多少秒
def countdate(olddate):
    nowtime = datetime.datetime.now()
    t1 = nowtime - olddate  # 现在时间减最后登陆日期
    temp = str(t1)
    day = ""
    hours = ""
    minute = ""
    second = ""
    if "days" in temp:
        day = t1.days
        hours = temp.split(",")[1].split(":")[0]
        minute = temp.split(",")[1].split(":")[1]
        second = temp.split(",")[1].split(":")[2]
    else:
        day = 0
        hours = temp.split(":")[0]
        minute = temp.split(":")[1]
        second = temp.split(":")[2]
    if "." in second:
        second = second.split('.')[0]
    return day, hours, minute, second
    #return "%s days" % day, "%s hours" % hours, "%s minutes" % minute, "%s second" % second



#主页
def index(request):
    cname = TITLE
    username = request.session.get('username', False)
    isadmin = request.session.get('isadmin', False)
    if username:
        online = Session.objects.filter(expire_date__gte=datetime.datetime.now())  # 获取未过期的sessions
        onlinecount = online.count()
        usercount = get_alldata(False).count()
        userlist = last_login()  # 取最后10次登陆的用户
        if not userlist:
            userlist = ""
        for i in userlist:  # 把最后一次登陆时间到当前时间的时差计算出来
            day, hours, minute, second = countdate(i.get("lastlogin"))
            i["day"] = day
            i["hours"] = hours
            i["minute"] = minute
            i["second"] = second
        hostscount = counthosts()
        projectcount = countproject()
        sysinfo = gethosts(4)   # 获取系统信息，取4条信息
        pjinfo = getdeployinfo()  # 获取最近6次项目部署记录
        return render(request, 'index.html', locals())
    else:
        response = HttpResponseRedirect('/login/')
        return response



def logout(request):  # 退出
    try:
        del request.session['username']
        del request.session['isadmin']
    except:
        pass
    response = HttpResponseRedirect('/login/')
    return response
