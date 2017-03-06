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
PROJECTPATH = config.get('base', 'projectfilepath')
svnurl = config.get('base', 'svnurl')

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

# jenkins配置
jenkinsurl = config.get('jenkins', 'jenkinsurl')
jenkinsuser = config.get('jenkins', 'jenkinsuser')
jenkinspassword = config.get('jenkins', 'jenkinspassword')
jenkinsip = config.get('jenkins', 'jenkinsip')
jenkinsfileport = config.get('jenkins', 'jenkinsfileport')

# 本地配置
localipaddr = config.get('base', 'ipaddr')
localport = config.get('base', 'port')

# etcd配置
etcdip = config.get('etcd', 'etcdip')
etcdport = config.get('etcd', 'etcdport')

# window.history.go(-1),也可以使用window.history.back()
message = '''
    <script>alert("%s"); </script>
    <script language="javascript">
        window.history.back();
    </script>
'''
# 转到主页,两个参数，一个为提示内容，一个为跳转链接
messageindex = '''
    <script>alert("%s"); </script>
    <script language="javascript">
        self.location='%s';
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
    'project',
    'pjdeploy',
    'hosts',
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


# jenkins配置文件xml,第一个参数为描述，第二个参数为svn地址,第三个参数为svn验证id, 第四个参数为maven参数,第五个参数为发送邮件列表，第六个参数为构建后运行脚本

jenkinsconfig = u'''<?xml version='1.0' encoding='UTF-8'?>
<maven2-moduleset plugin="maven-plugin@2.14">
  <actions/>
  <description>%s</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.security.AuthorizationMatrixProperty>
      <permission>hudson.model.Item.Read:zhouyu</permission>
      <permission>hudson.model.Item.Build:zhouyu</permission>
    </hudson.security.AuthorizationMatrixProperty>
    <jenkins.model.BuildDiscarderProperty>
      <strategy class="hudson.tasks.LogRotator">
        <daysToKeep>1</daysToKeep>
        <numToKeep>10</numToKeep>
        <artifactDaysToKeep>-1</artifactDaysToKeep>
        <artifactNumToKeep>-1</artifactNumToKeep>
      </strategy>
    </jenkins.model.BuildDiscarderProperty>
  </properties>
  <scm class="hudson.scm.SubversionSCM" plugin="subversion@2.7.1">
    <locations>
      <hudson.scm.SubversionSCM_-ModuleLocation>
        <remote>%s</remote>
        <credentialsId>%s</credentialsId>
        <local>.</local>
        <depthOption>infinity</depthOption>
        <ignoreExternalsOption>true</ignoreExternalsOption>
      </hudson.scm.SubversionSCM_-ModuleLocation>
    </locations>
    <excludedRegions></excludedRegions>
    <includedRegions></includedRegions>
    <excludedUsers></excludedUsers>
    <excludedRevprop></excludedRevprop>
    <excludedCommitMessages></excludedCommitMessages>
    <workspaceUpdater class="hudson.scm.subversion.UpdateUpdater"/>
    <ignoreDirPropChanges>false</ignoreDirPropChanges>
    <filterChangelog>false</filterChangelog>
  </scm>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <rootModule>
    <groupId>com.gd.qrp</groupId>
    <artifactId>qrp</artifactId>
  </rootModule>
  <goals>%s</goals>
  <aggregatorStyleBuild>true</aggregatorStyleBuild>
  <incrementalBuild>false</incrementalBuild>
  <ignoreUpstremChanges>false</ignoreUpstremChanges>
  <ignoreUnsuccessfulUpstreams>false</ignoreUnsuccessfulUpstreams>
  <archivingDisabled>false</archivingDisabled>
  <siteArchivingDisabled>false</siteArchivingDisabled>
  <fingerprintingDisabled>false</fingerprintingDisabled>
  <resolveDependencies>false</resolveDependencies>
  <processPlugins>false</processPlugins>
  <mavenValidationLevel>-1</mavenValidationLevel>
  <runHeadless>false</runHeadless>
  <disableTriggerDownstreamProjects>false</disableTriggerDownstreamProjects>
  <blockTriggerWhenBuilding>true</blockTriggerWhenBuilding>
  <settings class="jenkins.mvn.DefaultSettingsProvider"/>
  <globalSettings class="jenkins.mvn.DefaultGlobalSettingsProvider"/>
  <reporters/>
  <publishers>
    <hudson.plugins.emailext.ExtendedEmailPublisher plugin="email-ext@2.52">
      <recipientList>$DEFAULT_RECIPIENTS%s</recipientList>
      <configuredTriggers>
        <hudson.plugins.emailext.plugins.trigger.AlwaysTrigger>
          <email>
            <subject>$PROJECT_DEFAULT_SUBJECT</subject>
            <body>$PROJECT_DEFAULT_CONTENT</body>
            <recipientProviders>
              <hudson.plugins.emailext.plugins.recipients.ListRecipientProvider/>
            </recipientProviders>
            <attachmentsPattern></attachmentsPattern>
            <attachBuildLog>false</attachBuildLog>
            <compressBuildLog>false</compressBuildLog>
            <replyTo>$PROJECT_DEFAULT_REPLYTO</replyTo>
            <contentType>project</contentType>
          </email>
        </hudson.plugins.emailext.plugins.trigger.AlwaysTrigger>
      </configuredTriggers>
      <contentType>default</contentType>
      <defaultSubject>$DEFAULT_SUBJECT</defaultSubject>
      <defaultContent>$DEFAULT_CONTENT</defaultContent>
      <attachmentsPattern></attachmentsPattern>
      <presendScript>$DEFAULT_PRESEND_SCRIPT</presendScript>
      <postsendScript>$DEFAULT_POSTSEND_SCRIPT</postsendScript>
      <attachBuildLog>false</attachBuildLog>
      <compressBuildLog>false</compressBuildLog>
      <replyTo>$DEFAULT_REPLYTO</replyTo>
      <saveOutput>false</saveOutput>
      <disabled>false</disabled>
    </hudson.plugins.emailext.ExtendedEmailPublisher>
  </publishers>
  <buildWrappers/>
  <prebuilders/>
  <postbuilders>
    <hudson.tasks.Shell>
      <command>%s

</command>
    </hudson.tasks.Shell>
  </postbuilders>
  <runPostStepsIfResult>
    <name>FAILURE</name>
    <ordinal>2</ordinal>
    <color>RED</color>
    <completeBuild>true</completeBuild>
  </runPostStepsIfResult>
</maven2-moduleset>'''
