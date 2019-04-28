#!/usr/bin/python
# -*- coding: UTF-8 -*-

from wrap import *

#mod = Model('server-background')
#mod = Model('monitor-server')
#bus = Business()
#bus.info(mod)
#bus.jenkinsBuild(mod)
#time.sleep(1)
#bus.jenkinsInfo(mod)
#GL.upload('/mydata/packages/program1/tmp/server-background', 'host-test-01', '/mydata/program1/server-background')

mod = Model('server-background')
print mod.dplPath()[:mod.dplPath().rfind('/')]

