#!/usr/bin/python
# -*- coding: UTF-8 -*-

from wrap import *
from cmd2 import Cmd

class Loop(Cmd):
    def __init__(self):
        self.bus = Business()
        Cmd.__init__(self)
        self.svnOptions = { #svn操作的选项与对应业务功能的映射
            'ls': 'self.bus.svnList',
            'co': 'self.bus.svnCheckout',
            'merge': 'self.bus.svnMerge',
            'ci': 'self.bus.svnCommit',
            'cp': 'self.bus.svnCopy',
            'info': 'self.bus.svnInfo'
        }
        self.jksOptions = { #jenkins操作的选项与对应业务功能的映射
            'build': 'self.bus.jenkinsBuild',
            'info': 'self.bus.jenkinsInfo'
        }
        self.projOptions = {    #工程操作的选项与对应业务功能的映射       
            'backup': 'self.bus.backup',
            'update': 'self.bus.update',
            'start': 'self.bus.start',
            'stop': 'self.bus.stop',
            'restart': 'self.bus.restart',
            'info': 'self.bus.info'
        }

    #事件循环开始前自动执行
    def preloop(self):
        self.prompt = '自动部署 %s %s ->> ' % (GL.progZh,GL.envZh)
        GL.log.info('进入交互循环（%s）' % self.prompt)

    #事件循环结束时自动执行
    def postloop(self):
        GL.log.info('退出交互循环（%s）' % self.prompt)

    #输入为空时什么都不做
    def emptyline(self):
        return

    #自定义exit命令：退出循环
    #参数 arg 自定义命令必带，此处未用到
    def do_exit(self, arg):
        return True

    #自定义exit命令的帮助内容，循环中输入help exit时调用
    def help_exit(self):
        print('''
        exit命令：退出交互循环；用法：exit
        ''')

    #默认的自动补全内容，在输入前缀后按tab键时回调该函数，与shell类似
    #参数 args 四个元素的tuple:
    #(要补全的字段, 当前完整的输入, 补全字段的起始位, 补全字段的结束位)
    def completedefault(self, *args):
        #默认自动补全的内容为所有主机名和工程名
        lst = []
        for tmp in GL.hosts+GL.projects:
            #判断以输入的前缀为起始的才加入本次补全
            if tmp.startswith(args[0]):
                lst.append(tmp)
        lst.sort()   #排序，保证每次出现的顺序一致
        return lst

    #自定义svn命令, 实现svn相关操作, 用法见函数help_svn
    def do_svn(self, arg):
        args = arg.split(' ')   #以空格分隔参数
        if len(args) == 2:
            #直接接受两个参数, 第一为选项, 第二为工程
            if args[0] in self.svnOptions and args[1] in GL.projects:
                #以eval来实现对字符串形式的函数名进行调用
                eval(self.svnOptions[args[0]])(Model(args[1]))
                return
        self.help_svn()

    #自定义svn命令的帮助内容，循环中输入help svn时调用
    def help_svn(self):
        print('''
        svn命令：svn相关操作；用法：svn [选项] [工程名];
            选项：
                co      检出
                merge   合并
                ci      提交
                cp      拷贝
                info    信息
        ''')

    #自定义jks命令, 实现jenkins相关操作, 用法见函数help_jks
    def do_jks(self, arg):
        args = arg.split(' ')   #以空格分隔参数
        if len(args) == 2:
            #直接接受两个参数, 第一为选项, 第二为工程
            if args[0] in self.jksOptions and args[1] in GL.projects:
                #以eval来实现对字符串形式的函数名进行调用
                eval(self.jksOptions[args[0]])(Model(args[1]))
                return
        self.help_jks()

    #自定义jks命令的帮助内容，循环中输入help jks时调用
    def help_jks(self):
        print('''
        jks命令：jks相关操作；用法：jks [选项] [工程名];
            选项：
                build   立即构建
                info    查看信息
        ''')

    #自定义proj命令, 实现工程相关操作, 用法见函数help_proj
    def do_proj(self, arg):
        args = arg.split(' ')   #以空格分隔参数
        if len(args) == 2:
            #直接接受两个参数, 第一为选项, 第二为工程
            if args[0] in self.projOptions and args[1] in GL.projects:
                #以eval来实现对字符串形式的函数名进行调用
                eval(self.projOptions[args[0]])(Model(args[1]))
                return
        self.help_proj()

    #自定义proj命令的帮助内容，循环中输入help proj时调用
    def help_proj(self):
        print('''
        proj命令：proj相关操作；用法：proj [选项] [工程名];
            选项：
                backup      备份
                update      更新
                start       启动
                stop        停止
                restart     重启
                info        信息
        ''')

    def do_cmd(self, arg):
        args = arg.split(' ')   #以空格分隔参数
        if len(args)==2 and args[0] in GL.hosts:
            self.bus.cmd(args[0], args[1])

