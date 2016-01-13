#!/usr/bin/python

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import config
from tornado.options import options

from mongohandler import *
from topologyhandler import *
from modulehandler import *
from stormloghandler import *
from statushandler import *

import tornado.ioloop
import tornado.web
import tornado.httpserver

api_logger = config.getlog()

class MainHandler(tornado.web.RequestHandler):
	
	def get(self):
		api_logger.info("HEADERS: "+str(self.request))
		self.write("Sinfonier API v0.1.")


application = tornado.web.Application([
	(r"/", MainHandler),
	(r"/loadmodule",LoadModule),
	(r"/compilemodule",CompileModule),
	(r"/updatemodule",LoadModule),
	(r"/runtopology",RunTopology),
	(r"/stoptopology",StopTopology),
	(r"/updatetopology",UpdateTopology),
	(r"/getlog",GetLog),
	(r"/fgetlog",GetLogV2),
	(r"/apigetlog",GetLogV3),
	(r"/status",Status),
	(r"/fstatus",StatusV2),
	(r"/apistatus",StatusV3)
])

if __name__ == "__main__":
	sockets = tornado.netutil.bind_sockets(options.port)
	tornado.process.fork_processes(options.concurrency)
	server = tornado.httpserver.HTTPServer(application)
	server.add_sockets(sockets)
	tornado.ioloop.IOLoop.instance().start()
	server = tornado.httpserver.HTTPServer(application)

