# coding: utf-8
from django.db import connection
from autodeploy.settings import logger
from autodeploy.settings import DBHOST

# 检测数据库是否正常
def check_db():
    try:
        conn = connection.cursor()  # 检测数据库是正常
        return 1
    except:
        logger.error('连接'+str(DBHOST)+'数据库错误')
        return 0