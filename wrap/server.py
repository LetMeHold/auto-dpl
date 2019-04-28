#!/usr/bin/python  
# -*- coding: UTF-8 -*-

import traceback
import cherrypy
import thread
from wrap import *
from paramiko import SSHException

class Server(object):

    #指定host启动工程
    #参数 host 远程主机名
    #参数 mod 工程对象
    def start(self, host, mod):
        GL.remoteCommand(host, mod.startCmd())

    #指定host停止工程
    def stop(self, host, mod):
        GL.remoteCommand(host, mod.stopCmd())

    #指定host重启工程
    def restart(self, host, mod):
        self.start(host, mod)
        time.sleep(1)
        self.stop(host, mod)

    #提供操作工程服务，通常其他系统调用本服务是要操作一个节点而不是所有节点，所以这里需要指定主机
    #参数 opt 操作选项(start/stop/restart)
    #参数 ip 目标IP地址
    #参数 proj 目标工程名
    @cherrypy.expose    #开放本服务
    @cherrypy.tools.json_out()  #返回json格式内容
    def service(self, opt, ip, proj):
        GL.log.info('收到请求 (%s %s %s)' % (opt,ip,proj))
        ret = {'err':1, 'msg':'unknown'}    #定义返回值
        retry = 3   #重试三次
        while (retry != 0):
            try:
                retry -= 1
                mod = Model(proj)
                host = GL.getHostFromIp(ip) #将ip转换为主机名
                if host not in mod.hosts():
                    raise Exception('主机(%s)上未部署%s' % (host,proj))
                if opt == 'restart':
                    self.restart(host, mod)
                elif opt == 'start':
                    self.start(host, mod)
                elif opt == 'stop':
                    self.stop(host, mod)
                else:
                    raise Exception('不支持的操作选项：%s' % opt)
                ret['err'] = 0
                ret['msg'] = ''
                GL.log.info('请求操作完成 (%s %s %s)' % (opt,ip,proj))
                break
            except (SystemExit,SSHException) as e:
                #系统异常，通常是网络波动引起的，重试
                msg = traceback.format_exc()
                ret['err'] = 1
                ret['msg'] = msg
                GL.log.error('捕获到系统异常 (%s %s %s) : \n%s \n重试 %d ' % (opt,ip,proj,msg,retry))
            except Exception as e:
                #普通异常，通常是代码问题或请求内容问题，不重试
                msg = traceback.format_exc()
                ret['err'] = 1
                ret['msg'] = msg
                GL.log.error('捕获到普通异常 (%s %s %s) : \n%s \n不重试' % (opt,ip,proj,msg))
                retry = 0
        GL.log.info('本次请求处理完毕')
        return ret

