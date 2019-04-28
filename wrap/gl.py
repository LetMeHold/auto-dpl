#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import time
import datetime
import locale
import jenkins
import json
import logging
from logging.handlers import RotatingFileHandler
from fabric import network
from fabric.api import env,local,run,execute
from fabric.contrib import project
from fabric.context_managers import settings
from fabric.operations import put,get

#配置全局编码为utf8，防止出现中文乱码
reload(sys)
sys.setdefaultencoding('utf8')
language_code, encoding = locale.getdefaultlocale()
locale.setlocale(locale.LC_ALL, '%s.%s' % (language_code, encoding))

class Global:
    def __init__(self): #类的初始化函数
        #判断是否存在正确的启动http服务的参数
        #参数应有四个：启动脚本、项目英文名、环境英文名、端口
        if len(sys.argv)==4 and sys.argv[3].isdigit():
            self.isHTTP = True
        else:
            self.isHTTP = False
        self.mainDir = sys.path[0]  #获取本系统所在路径
        self.confDir = '%s/conf' % self.mainDir #配置文件的路径
        self.logDir = '%s/logs' % self.mainDir  #日志文件的路径
        self.fabric_env = env   #将fabric模块的环境变量保存下来
        self.readConfig()   #读取配置文件
        self.checkEnvMap()  #检查环境配置与映射
        self.checkIpMap()   #检查主机IP映射
        #获取打印日志的实例
        self.log = self.initLogger('DPLLogger', self.logDir, 'auto-dpl.log')
        self.jks = self.initJenkins()   #获取操作jenkins的实例

    def __del__(self):  #类的析构函数
        if network != None:
            #退出时断开所有到其他主机的连接
            network.disconnect_all()

    #操作前确认函数
    #question   询问的内容
    #返回       输入yes返回True，no返回False；其他则继续询问
    def confirm(self, question):
        askstr = '%s [yes or no] : ' % question
        while True:
            instr = raw_input(askstr)
            if instr!='yes' and instr!='no':
                continue
            elif instr == 'yes':
                return True
            else:
                return False

    #提供多个选项供选择
    #items      list类型，包含所有选项
    #question   询问的内容
    #返回       所选选项的内容
    def select(self, items, question):
        index = 1   #序号从1开始
        items.sort()    #排序一下，保证每次显示的顺序一致
        numDict = {}    #序号与选项的映射
        for it in items:
            print('\t%d. %s' % (index,it))
            #以字符串格式的序号为key方便与输入内容作比较
            numDict[str(index)] = it
            index += 1
        while True:
            instr = raw_input(question)
            if instr not in numDict:
                continue
            else:
                return numDict[instr]   #返回所选选项的内容

    def info(self, data):   #打印信息级别的日志
        self.log.info(data)

    def debug(self, data):  #打印调试级别的日志
        self.log.debug(data)

    def error(self, data):  #打印错误级别的日志
        self.log.error(data)

    def warn(self, data):   #打印警告级别的日志
        self.log.warn(data)

    #初始化并返回一个打印日志的对象
    #参数 loggerName  日志对象的名称
    #参数 logDir  日志文件保存的路径
    #参数 logFile 日志文件的名称
    #返回 打印日志对象
    def initLogger(self, loggerName, logDir, logFile):
        if not os.path.exists(logDir):
            os.mkdir(logDir)    #如果路径不存在就新建
        log = logging.getLogger(loggerName) #创建一个打印日志对象
        log.setLevel(logging.DEBUG) #设置基础的日志打印级别
        #输出日志到控制台
        ch = logging.StreamHandler()
        #配置控制台输出的格式
        cfmt = logging.Formatter('%(message)s')
        ch.setFormatter(cfmt)
        ch.setLevel(logging.INFO)   #设置控制台输出的级别，低于基础级别则无效
        log.addHandler(ch)  #将控制台输出添加到打印日志对象
        #配置输出日志到文件,文件最大5M，最多保存5个
        fh = RotatingFileHandler(\
            '%s/%s'%(logDir,logFile), maxBytes=5*1024*1024, backupCount=5)
        #配置文件输出的格式：时间-对象名-线程名-打印级别-日志内容
        ffmt = logging.Formatter('%(asctime)s - %(name)s - \
            %(threadName)s - %(levelname)s - %(message)s')
        fh.setFormatter(ffmt)
        fh.setLevel(logging.DEBUG)  #设置文件输出的级别，低于基础级别则无效
        log.addHandler(fh)  #将文件输出添加到打印日志对象
        return log

    #读取json文件内容，工具函数，供其他函数或模块调用
    def loadJsonFile(self, fileName):
        return json.load(open(fileName, 'r'))

    #读取配置文件
    def readConfig(self):
        #将全局配置内容读取到成员变量glInfo
        glConf = '%s/global.json' % self.confDir
        self.glInfo = self.loadJsonFile(glConf)
        #配置远程登录的密钥及其密码
        self.fabric_env.key_filename = self.glInfo['rsa_file']
        self.fabric_env.password = self.glInfo['rsa_pwd']
        #本系统支持多项目多环境，为简化操作和安全起见，要进行环境隔离
        #每次进入交互循环都要选择项目和环境，而不是用参数进行区分
        if self.isHTTP == False:
            #进入交互逻辑时由用户选择要操作的项目和环境
            #根据项目中文名选择，并将结果赋值给成员变量progZh
            items = self.glInfo['programs'].keys()
            self.progZh = self.select(items, '请选择要操作的项目 ->> ')
            self.program = self.glInfo['programs'][self.progZh] #项目英文名
            #根据环境中文名选择，并将结果赋值给成员变量envZh
            items = self.glInfo['environments'].keys()
            self.envZh = self.select(items, '请选择要操作的环境 ->> ')
            self.env = self.glInfo['environments'][self.envZh]  #环境英文名
        else:
            #启动http服务时通过命令行参数获取要操作的项目和环境
            if sys.argv[1] in self.glInfo['programs'].values():
                self.program = sys.argv[1]
                for k,v in self.glInfo['programs'].items():
                    if v == self.program:
                        self.progZh = k
                if sys.argv[2] in self.glInfo['environments'].values():
                    self.env = sys.argv[2]
                    for k,v in self.glInfo['environments'].items():
                        if v == self.env:
                            self.envZh = k
                else:
                    raise Exception('不支持的环境: %s, 请更正后重试!' % sys.argv[2])
            else:
                raise Exception('不支持的项目: %s, 请更正后重试!' % sys.argv[1])
        #将当前项目的配置内容读取到成员变量progInfo
        progConf = '%s/%s.json' % (self.confDir,self.program)
        self.progInfo = self.loadJsonFile(progConf)
        #所选项目及所选环境下的所有主机
        self.hosts = self.progInfo['deployment'][self.env].keys()
        self.hosts.sort()
        #所选项目及所选环境下的所有工程
        self.projects = self.progInfo['projects'].keys()
        self.projects.sort()

    #检查环境映射，部署中使用的环境英文名必须在全局配置中存在规范的映射
    #检查环境选择，选择的项目中必须存在选择的环境
    def checkEnvMap(self):
        dplEnvList = self.progInfo['deployment'].keys()
        glEnvList = self.glInfo['environments'].values()
        for env in dplEnvList:
            if env not in glEnvList:
                raise Exception('发现未映射的环境: %s, 请更正后重试!' % env)
        if self.env not in dplEnvList:
            raise Exception('所选项目（%s）中不存在所选环境（ %s）, 请更正后重试!' % (self.progZh,self.envZh))

    #检查主机IP映射，部署中使用的主机名必须存在与IP的映射
    def checkIpMap(self):
        for host in self.progInfo['deployment'][self.env].keys():
            if host not in self.progInfo['hosts']:
                raise Exception('发现未映射的host: %s, 请更正后重试!' % host)

    #将主机名转换为映射的IP
    def getIpFromHost(self, host):
        if host not in self.progInfo['hosts']:
            raise Exception('无法识别的host: %s, 请更正后重试!' % host)
        else:
            return self.progInfo['hosts'][host]

    #将IP转换为对应的主机名
    def getHostFromIp(self, ip):
        host = None
        for k,v in self.progInfo['hosts'].items():
            if v == ip:
                host = k
        if host == None:
            raise Exception('无法识别的IP: %s, 请更正后重试!' % ip)
        else:
            return host

    #在本地执行命令，工具函数，供其他模块调用
    #参数 cmd 命令的内容
    def localCommand(self, cmd):
        #通过fabric模块的execute和local在本地执行命令
        execute(local, cmd)

    #在远程主机执行命令，工具函数，供其他模块调用
    #参数 host 主机名
    #参数 cmd 命令的内容
    def remoteCommand(self, host, cmd):
        ip = self.getIpFromHost(host)   #将host转为ip
        #通过fabric模块的execute和run在远程执行命令
        execute(run, cmd, host=ip, pty=False)

    #初始化jenkins实例
    def initJenkins(self):
        return jenkins.Jenkins(\
            self.glInfo['jenkins_url'], \
            username=self.glInfo['jenkins_usr'], \
            password=self.glInfo['jenkins_token'])

    #获取一个当前时间戳字符串
    def timestamp(self):
        dt = datetime.datetime.now()
        return dt.strftime('%Y%m%d%H%M%S')

    #上传本地文件/目录到远程主机
    #参数 local 本地文件/目录
    #参数 host 远程主机名
    #参数 remote 远程文件/目录
    def upload(self, local, host, remote):
        ip = self.getIpFromHost(host)   #将host转为ip
        with settings(host_string=ip):  #每次操作指定目标IP
            put(local, remote, mirror_local_mode=True)

    #def getIpListFromHostList(self, hostList):
        #ipList = []
        #for host in hostList:
            #ip = self.getIpFromHost(host)
            #ipList.append(ip)
        #return ipList

#实例化全局对象，供其他模块调用
GL = Global()

