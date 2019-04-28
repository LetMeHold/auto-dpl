#!/usr/bin/python
# -*- coding: UTF-8 -*-

from gl import *

class Model:
    def __init__(self, name):
        flag = False
        for projects in GL.progInfo['deployment'][GL.env].values():
            if name in projects:
                flag = True
        if flag:
            self.name = name
        else:
            raise Exception('无法识别的工程名: %s, 请更正后重试!' % name)

    #工程版本号
    def version(self):
        return GL.progInfo['version']

    #工程的svn主干路径
    def svnTrunk(self):
        return '%s/trunk/%s/%s' % (GL.glInfo['svn_url'],GL.program,self.name)

    #工程的svn分支路径
    def svnBranch(self):
        return '%s/branches/%s/%s/%s' % (GL.glInfo['svn_url'],GL.program,self.version(),self.name)

    #工程的svn tag路径
    def svnTag(self):
        return '%s/tags/%s/%s/%s' % (GL.glInfo['svn_url'],GL.program,self.version(),self.name)

    #分支的工作副本路径
    def branchCopy(self):
        return '%s/branches/%s/%s/%s' % (GL.glInfo['svn_copy'],GL.program,self.version(),self.name)

    #tag的工作副本路径
    def tagCopy(self):
        return '%s/tags/%s/%s/%s' % (GL.glInfo['svn_copy'],GL.program,self.version(),self.name)

    #工程对应的jenkins job的名称
    def jenkinsJob(self):
        return '%s-%s' % (GL.env,self.name)

    #工程的类型
    def type(self):
        return GL.progInfo['projects'][self.name]['type']

    #工程部署的主机
    def hosts(self):
        hosts = []
        for host,projects in GL.progInfo['deployment'][GL.env].items():
            if self.name in projects:
                hosts.append(host)
        return hosts

    #工程的备份路径
    def backupPath(self):
        return '%s/%s' % (GL.progInfo['backup_path'],self.name)

    #工程的部署路径
    def dplPath(self):
        return '%s/%s' % (GL.progInfo['dpl_path'],self.name)

    #工程的更新包
    def package(self):
        return '%s/%s' % (GL.progInfo['package_path'],GL.progInfo['projects'][self.name]['package'])

    #更新时临时解压路径
    def tmpPath(self):
        return '%s/tmp' % GL.progInfo['package_path']

    #工程启动的命令
    def startCmd(self):
        if self.type() == 'server':
            return '%s/bin/start.sh' % self.dplPath()
        elif self.type() == 'tomcat':
            return '%s/bin/startup.sh' % self.dplPath()
        else:
            raise Exception('无法识别的工程类型: %s, 请更正后重试!' % self.type())

    #工程停止的命令
    def stopCmd(self):
        if self.type() == 'server':
            return '%s/bin/stop.sh' % self.dplPath()
        elif self.type() == 'tomcat':
            return '%s/bin/shutdown.sh' % self.dplPath()
        else:
            raise Exception('无法识别的工程类型: %s, 请更正后重试!' % self.type())

    #查询工程信息的命令
    def infoCmd(self):
        #显示更新包信息和工程的进程信息
        return 'tmp=`ps -ef|grep %s/|grep -v grep`; if [ -z "$tmp" ];then echo "未启动"; else echo $tmp; fi' % self.dplPath()

