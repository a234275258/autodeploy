# coding:utf-8
"""
Django settings for autodeploy project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

import os
import ConfigParser
import logging.config

logging.config.fileConfig("logger.conf")  # 日志配制文件
logger = logging.getLogger("prodution")  # 取日志标签，可选为development,prodution

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

config = ConfigParser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'autodeploy.conf'))  # 读配置文件
TITLE = config.get('base', 'cname')  # 网站标题
DBHOST = config.get('db', 'host')    # 数据库服务器IP

ldapconn = config.get('ldap', 'ldapconn')  # ldap服务器
basedn = config.get('ldap', 'basedn')    # basedn

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'd8w^r7#^euoc-+srlww5x3(g=#3)#ky3nw4qvnyyvtc!5=%)8a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user',
    'south',
    'vdeploy',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'autodeploy.urls'

WSGI_APPLICATION = 'autodeploy.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '172.19.20.116',
        'USER': 'autodeploy',
        'PASSWORD': '123456',
        'PORT': 3306,
        'NAME': 'autodeploy',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'templates'),)
