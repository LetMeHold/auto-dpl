#!/usr/bin/python
# -*- coding: UTF-8 -*-

from wrap import *

if GL.isHTTP:
    #启动http服务, isHTTP的判断请参考全局模块wrap/gl.py的内容
    conf = {'server.socket_host': '0.0.0.0', 'server.socket_port': int(sys.argv[3])}
    cherrypy.config.update(conf)
    GL.log.info('http接口服务启动：%s %s %s' % (GL.progZh,GL.envZh,sys.argv[3]))
    cherrypy.quickstart(Server())
else:
    #进入交互循环
    loop = Loop()
    loop.cmdloop()

