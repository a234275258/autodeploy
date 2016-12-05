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

# 网站名称设置
TITLE = config.get('base', 'cname')  # 网站标题
URL = config.get('base', 'url')

# ldap配置
ldapconn = config.get('ldap', 'ldapconn')  # ldap服务器
ldappassword = config.get('ldap', 'ldappassword')  # ldappassword
basedn = config.get('ldap', 'basedn')  # basedn
ldapcn = config.get('ldap', 'ldapcn')  # ldapcn

# mysql数据库配置
DBHOST = config.get('db', 'host')
DBENGINE = config.get('db', 'engine')
DBPORT = config.get('db', 'port')
DBUSER = config.get('db', 'user')
DBPASSWORD = config.get('db', 'password')
DBNAME = config.get('db', 'database')

# 邮件配置
email_host = config.get('mail', 'email_host')
email_port = config.get('mail', 'email_port')
email_host_user = config.get('mail', 'email_host_user')
email_host_password = config.get('mail', 'email_host_password')
email_use_tls = config.getboolean('mail', 'email_use_tls')
email_use_ssl = config.getboolean('mail', 'email_use_ssl')

# window.history.go(-1),也可以使用window.history.back()
message = '''
    <script>alert("%s"); </script>
    <script language="javascript">
        window.history.back();
    </script>
'''
# 转到主页
messageindex = '''
    <script>alert("%s"); </script>
    <script language="javascript">
        self.location='/index/';
    </script>
'''

EMAIL_HOST = email_host
EMAIL_PORT = email_port
EMAIL_HOST_USER = email_host_user
EMAIL_HOST_PASSWORD = email_host_password
DEFAULT_FROM_EMAIL = u'管理员<%s>' % email_host_user
EMAIL_USE_TLS = email_use_tls

try:
    EMAIL_USE_SSL = config.getboolean('mail', 'email_use_ssl')
except ConfigParser.NoOptionError:
    EMAIL_USE_SSL = False
EMAIL_BACKEND = 'django_smtp_ssl.SSLEmailBackend' if EMAIL_USE_SSL else 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_TIMEOUT = 5

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
    # 'django.middleware.csrf.CsrfViewMiddleware',
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
        'ENGINE': 'django.db.backends.%s' % DBENGINE,
        'HOST': DBHOST,
        'USER': DBUSER,
        'PASSWORD': DBPASSWORD,
        'PORT': DBPORT,
        'NAME': DBNAME,
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
SESSION_COOKIE_AGE = 3600

STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'templates'),)
