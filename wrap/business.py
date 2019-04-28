#!/usr/bin/python
# -*- coding: UTF-8 -*-

from gl import *
from model import *

class Business:
    def __init__(self):
        pass

    def cmd(self, host, cmd):
        GL.remoteCommand(host, cmd)

    def svnList(self, mod):
        cmd = 'svn ls %s %s %s %s' % (mod.svnTrunk(),mod.svnBranch(),mod.svnTag(),self.svnSuffix())
        GL.localCommand(cmd)

    #svn命令的统一后缀，包含用户名、密码、不缓存凭据
    def svnSuffix(self):
        return '--username %s --password %s --no-auth-cache' % (GL.glInfo['svn_usr'],GL.glInfo['svn_pwd'])

    #检出svn代码
    #参数 mod 工程对象
    def svnCheckout(self, mod):
        if GL.env == 'test':    #测试环境，检出分支代码
            cmd = 'svn co %s %s' % (mod.svnBranch(),mod.branchCopy())
            if GL.confirm('将在本地执行命令: %s 是否确认执行？' % cmd):
                cmd = '%s %s' % (cmd,self.svnSuffix())
                GL.localCommand(cmd)
        elif GL.env == 'product':   #生产环境，检出tag代码
            cmd = 'svn co %s %s' % (mod.svnTag(),mod.tagCopy())
            if GL.confirm('将在本地执行命令: %s 是否确认执行？' % cmd):
                cmd = '%s %s' % (cmd,self.svnSuffix())
                GL.localCommand(cmd)
        else:
            print('当前环境（%s）不需要checkout！' % GL.env)

    #拷贝svn代码
    #参数 mod 工程对象
    def svnCopy(self, mod):
        if GL.env == 'test':    #测试环境，从主干拷贝到分支
            cmd = 'svn cp %s %s --editor-cmd vim' % (mod.svnTrunk(),mod.svnBranch())
            if GL.confirm('将在本地执行命令: %s 是否确认执行？' % cmd):
                cmd = '%s %s' % (cmd,self.svnSuffix())
                GL.localCommand(cmd)
        elif GL.env == 'product':   #生产环境，从分支拷贝到tag
            cmd = 'svn cp %s %s --editor-cmd vim' % (mod.svnBranch(),mod.svnTag())
            if GL.confirm('将在本地执行命令: %s 是否确认执行？' % cmd):
                cmd = '%s %s' % (cmd,self.svnSuffix())
                GL.localCommand(cmd)
        else:
            print('当前环境（%s）不需要copy！' % GL.env)

    #合并svn代码
    #参数 mod 工程对象
    def svnMerge(self, mod):
        if GL.env == 'test':    #测试环境，从主干合并到分支
            cmd = 'svn merge %s %s %s' % (mod.svnBranch(),mod.svnTrunk(),mod.branchCopy())
            if GL.confirm('将在本地执行命令: %s 是否确认执行？' % cmd):
                cmd = '%s %s' % (cmd,self.svnSuffix())
                GL.localCommand(cmd)
        elif GL.env == 'product':   #生产环境，从分支合并到tag
            cmd = 'svn merge %s %s %s' % (mod.svnTag(),mod.svnBranch(),mod.tagCopy())
            if GL.confirm('将在本地执行命令: %s 是否确认执行？' % cmd):
                cmd = '%s %s' % (cmd,self.svnSuffix())
                GL.localCommand(cmd)
        else:
            print('当前环境（%s）不需要merge！' % GL.env)

    #提交svn代码
    #参数 mod 工程对象
    def svnCommit(self, mod):
        if GL.env == 'test':    #测试环境，提交分支的工作副本
            cmd = 'svn ci %s --editor-cmd vim' % mod.branchCopy()
            if GL.confirm('将在本地执行命令: %s 是否确认执行？' % cmd):
                cmd = '%s %s' % (cmd,self.svnSuffix())
                GL.localCommand(cmd)
        elif GL.env == 'product':   #生产环境，提交tag的工作副本
            cmd = 'svn ci %s --editor-cmd vim' % mod.tagCopy()
            if GL.confirm('将在本地执行命令: %s 是否确认执行？' % cmd):
                cmd = '%s %s' % (cmd,self.svnSuffix())
                GL.localCommand(cmd)
        else:
            print('当前环境（%s）不需要commit！' % GL.env)

    #查看svn信息
    def svnInfo(self, mod):
        print('svn info')

    #构建jenkins job
    #参数 mod 工程对象
    def jenkinsBuild(self, mod):
        GL.jks.build_job(mod.jenkinsJob())

    #查看jenkins job最近的构建信息
    #参数 mod 工程对象
    def jenkinsInfo(self, mod):
        num = GL.jks.get_job_info(mod.jenkinsJob())['lastBuild']['number']  #最近的构建序号
        info = GL.jks.get_build_info(mod.jenkinsJob(), num) #通过序号获取构建信息
        tm = datetime.datetime.fromtimestamp(info['timestamp']/1000)
        tmStr = tm.strftime("%Y-%m-%d %H:%M:%S")    #转换构建时间
        print('构建Job：%s' % mod.jenkinsJob())
        print('构建序号：%d' % info['number'])
        print('构建时间：%s' % tmStr)
        print('构建进行中：%s' % info['building'])
        print('构建结果：%s' % info['result'])

    #备份工程，目的地为工程所在主机的备份目录
    #参数 mod 工程对象
    def backup(self, mod):
        #将工程文件夹拷贝到备份目录并加上时间戳后缀
        cmd = 'cp -r %s %s-%s' % (mod.dplPath(),mod.backupPath(),GL.timestamp())
        for host in mod.hosts():    #遍历所在主机
            if GL.confirm('将在%s执行命令: %s 是否确认执行？' % (host,cmd)):
                GL.remoteCommand(host, cmd)

    #更新工程
    #参数 mod 工程对象
    def update(self, mod):
        #清空临时目录，然后解压更新包
        GL.localCommand('rm -rf %s/*; tar -zxf %s -C %s' % (mod.tmpPath(),mod.package(),mod.tmpPath()))
        for host in mod.hosts():    #遍历所在主机
            if GL.confirm('将更新%s到%s的%s。是否确认执行？' % (mod.package(),host,mod.dplPath())):
                #删除远程主机上的工程文件夹
                GL.remoteCommand(host, 'rm -rf %s' % mod.dplPath())
                #上传临时目录的工程文件夹到远程主机
                tgt = mod.dplPath()[:mod.dplPath().rfind('/')]  #目标地址为部署路径的上层文件夹
                GL.upload('%s/%s' % (mod.tmpPath(),mod.name), host, tgt)

    #启动工程
    #参数 mod 工程对象
    def start(self, mod):
        cmd = mod.startCmd()
        for host in mod.hosts():    #遍历所在主机
            if GL.confirm('将在%s执行命令: %s 是否确认执行？' % (host,cmd)):
                GL.remoteCommand(host, cmd)

    #停止工程
    #参数 mod 工程对象
    def stop(self, mod):
        cmd = mod.stopCmd()
        for host in mod.hosts():    #遍历所在主机
            if GL.confirm('将在%s执行命令: %s 是否确认执行？' % (host,cmd)):
                GL.remoteCommand(host, cmd)

    #停止工程
    #参数 mod 工程对象
    def restart(self, mod):
        self.stop(mod)
        time.sleep(1)
        self.start(mod)

    #查看工程信息
    #参数 mod 工程对象
    def info(self, mod):
        #查看本地更新包信息，并加一个换行方便查看
        cmd = 'ls -l %s; echo' % mod.package()
        GL.localCommand(cmd)
        for host in mod.hosts():    #遍历所在主机
            #查看远程主机部署文件夹信息
            GL.remoteCommand(host, 'ls -ld %s' % mod.dplPath())
            #查看工程进程信息
            GL.remoteCommand(host, mod.infoCmd())

