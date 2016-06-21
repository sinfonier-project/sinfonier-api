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

import utils
import time
import shutil
import config

from random import randint
from tornado.options import options

from utils import *

api_logger = config.getlog()
stormuiapi = config.getStormUIAPI()


class CompileModule(BaseHandler):
	"""
	Compile module on temporal classpath. We just 

	Params:
		name: string
		type: string
		gist: url
		lan: string python/java
	"""
	def prepare(self):
		content_type = self.request.headers.get("Content-Type", "")
		if content_type.startswith("application/json"):
			self.arguments = tornado.escape.json_decode(self.request.body)
		else:
			self.arguments = None

	def post(self):
		if self.arguments:
			api_logger.info("HEADERS: "+str(self.request))
			# Parse each param
			data = self.arguments
			if 'name' not in list(data.keys()) or 'type' not in list(data.keys()) or 'lang' not in list(data.keys()):
				api_logger.error("Error requests params")
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				try:
					t_name = data['name']
					t_type = data['type']
					t_lang = data['lang']
					t_gist = data['gist']
				except Exception as e:
					api_logger.error("Error requests params "+str(e))
					self.finish('{"result":"error","description":"Error requests params","debug":"'+str(e)+'"}')
			# Create working dir
			try:
				workingPath = "/var/storm/src/sinfonier_backend"+str(int(time.time()+randint(50,150)))
				shutil.copytree(options.backend_working_path,workingPath)
			except Exception as e:
				api_logger.error("Error creating working dir. "+str(e))
				self.finish('{"result":"error","description":"Error creating working dir","debug":"'+str(e)+'"}')
			
			# Change routes
			java_path_drains = workingPath+"/src/jvm/com/sinfonier/drains/"
			java_path_bolts = workingPath+"/src/jvm/com/sinfonier/bolts/"
			java_path_spouts = workingPath+"/src/jvm/com/sinfonier/spouts/"

			api_logger.info("New paths: "+java_path_drains+" - "+java_path_bolts+" - "+java_path_spouts)
			fileCfileCreatedreated = True
			# Get code from gist and write it
			util = Utils()
			# Check module type
			if t_type == "drain":
				dst_path = java_path_drains
			elif t_type == "bolt":
				dst_path = java_path_bolts
			elif t_type == "spout":
				dst_path = java_path_spouts
			else:
				shutil.rmtree(workingPath)
				api_logger.error("Module type must be spout/bolt/drain. Deleted working repo.")
				self.finish('{"result":"error","description":"Module type must be spout/bolt/drain"}')
			# Check module language. If Python or Ruby (soon) change path
			if t_lang == "python":
				dst_path = workingPath+"/multilang/resources/"
				module_lang = "py"
			elif t_lang == "java":
				module_lang = "java"
			elif t_lang == "ruby":
				shutil.rmtree(workingPath)
				api_logger.error("Ruby not supported yet. Deleted working repo.")
				self.finish('{"result":"error","description":"Ruby not supported yet"}')
			else:
				shutil.rmtree(workingPath)
				api_logger.error("Language must be supported. Current Python and Java. Deleted working repo.")
				self.finish('{"result":"error","description":"Language must be supported. Current Python and Java"}')
			
			try:
				api_logger.info("Get module.")
				fileName = util.get_module(t_name,module_lang,t_gist,dst_path,t_type)
				api_logger.info("Module Added: "+str(fileName))
				fileCreated = True
			except Exception as e:
				shutil.rmtree(workingPath)
				api_logger.error("Error creating source code file. Deleted working repo. "+str(e))
				self.finish('{"result":"error","description":"Error creating file","debug":"'+str(e)+'"}')
				fileCreated = False	

			if fileCreated:
				# Regenerate jar on /var/storm/lastjar/
				# <MAVEN_PATH>/maven/bin/mvn -f <SINFONIER_BACKEND_PATH>/pom.xml compile
				cmd_launch = options.maven_binary+" -f "+workingPath+"/pom.xml"+" compile"
				cmd = utils.execCommand(cmd_launch)
				# Get output and error
				(output, err) = cmd.execute()
				if err:
					shutil.rmtree(workingPath)
					api_logger.error("Error compiling jar file. Deleted working repo. "+str(err))
					self.finish('{"result":"error","description":"Error compiling jar file", "detail":"'+str(err)+'"}')
				elif output:
					api_logger.debug("Command output: "+str(output))
					errorDebug = False
					warDebug = False
					dedugStack = ""
					warStack = ""
					fDate = ""
					for line in output.splitlines():
						if "ERROR" in line and t_name in line:
							try:
								api_logger.info("Found ERROR")
								dedugStack += time.strftime("%m-%d-%Y %H:%M:%S")+": "
								dedugStack += line.split("com/sinfonier")[1]
								dedugStack += "|"
							except Exception as e:
								api_logger.error("Error parsing errors from output. "+str(e))
								pass
						if "BUILD FAILURE" in line:
							api_logger.info("Found BUILD FAUILURE")
							errorDebug = True
						if "WARNING" in line and t_name in line:
							try:
								api_logger.info("Found WARNING")
								warDebug = True
								warStack += time.strftime("%m-%d-%Y %H:%M:%S")+": "
								warStack += line.split("com/sinfonier")[1]
								warStack += "|"
							except Exception as e:
								api_logger.error("Error parsing errors from output. "+str(e))
								pass
						if "Finished at:" in line:
							api_logger.info("Store Finished time")
							fDate = line
					shutil.rmtree(workingPath)
					if errorDebug:
						api_logger.error("Error compiling module. "+str(dedugStack))
						self.finish('{"result":"error","description":"Error compiling...", "detail":"'+str(dedugStack)+'"}')
					elif warDebug:
						api_logger.info("Warning during compiling. "+str(warStack))
						self.finish('{"result":"warning","description":"Warning during compiling", "detail":"'+str(warStack)+'"}')
					else:
						api_logger.info("Module compiled. "+str(fDate))
						self.finish('{"result":"success","description":"Module compiled", "detail":"'+str(fDate)+'"}')

		else:
			api_logger.error("Content-Type:application/json missing")
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')

class LoadModule(BaseHandler):
	"""
	Load module on classpath. After this step module will be available to be used in topolgies.

	Params:
		name: string
		type: string
		gist: url
		lang: string python/java
	"""

	def prepare(self):
		content_type = self.request.headers.get("Content-Type", "")
		if content_type.startswith("application/json"):
			self.arguments = tornado.escape.json_decode(self.request.body)
		else:
			self.arguments = None

	def post(self):
		if self.arguments:
			api_logger.info("HEADERS: "+str(self.request))
			# Parse each param
			data = self.arguments
			if 'name' not in list(data.keys()) or 'type' not in list(data.keys()) or 'lang' not in list(data.keys()):
				api_logger.error("Error requests params")
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				try:
					t_name = data['name']
					t_type = data['type']
					t_lang = data['lang']
					t_gist = data['gist']
				except Exception as e:
					api_logger.error("Error requests params "+str(e))
					self.finish('{"result":"error","description":"Error requests params","debug":"'+str(e)+'"}')	

			# Get code from gist and write it
			util = Utils()
			# Check module type
			if t_type == "drain":
				dst_path = options.backend_java_path_drains
			elif t_type == "bolt":
				dst_path = options.backend_java_path_bolts
			elif t_type == "spout":
				dst_path = options.backend_java_path_spouts
			else:
				api_logger.error("Module type must be spout/bolt/drain.")
				self.write('{"result":"error","description":"Module type must be spout/bolt/drain"}')

			# Check module language. If Python or Ruby (soon) change path
			if t_lang == "python":
				dst_path = options.backend_python_path
				module_lang = "py"
			elif t_lang == "java":
				module_lang = "java"
			elif t_lang == "ruby":
				api_logger.error("Ruby not supported jet.")
				self.write('{"result":"error","description":"Ruby not supported yet"}')
			else:
				api_logger.error("Language must be supported. Current Python and Java")
				self.write('{"result":"error","description":"Language must be supported. Current Python and Java"}')
			
			try:
				api_logger.info("Get module.")
				fileName = util.get_module(t_name,module_lang,t_gist,dst_path,t_type)
				api_logger.info("Module Added: "+str(fileName))
				fileCreated = True
			except Exception as e:
				shutil.rmtree(workingPath)
				api_logger.error("Error creating source code file. Deleted working repo. "+str(e))
				self.finish('{"result":"error","description":"Error creating file","debug":"'+str(e)+'"}')
				fileCreated = False

			if fileCreated:				
				# Regenerate jar on /var/storm/lastjar/
				# <MAVEN_PATH>/maven/bin/mvn -f <SINFONIER_BACKEND_PATH>/pom.xml clean compile install
				cmd_launch = options.maven_binary+" -f "+options.maven_sinfonier_pom+" clean compile install"
				cmd = utils.execCommand(cmd_launch)
				# Get output and error
				(output, err) = cmd.execute()
				if err:
					self.finish('{"result":"error","description":"Error compiling jar file", "detail":"'+str(err)+'"}')
				else:
					# /opt/sinfonier/maven/bin/mvn -f /var/storm/src/sinfonier_backend/pom.xml package
					cmd_launch = options.maven_binary+" -f "+options.maven_sinfonier_pom+" package"
					cmd = utils.execCommand(cmd_launch)
					# Get output and error
					(output, err) = cmd.execute()
					if err:
						api_logger.error("Error compiling jar file. Deleted working repo. "+str(err))
						self.finish('{"result":"error","description":"Error creating jar file","detail":"'+str(err)+'"}')
					elif output:
						api_logger.debug("Command output: "+str(output))
						errorDebug = False
						warDebug = False
						dedugStack = ""
						warStack = ""
						fDate = ""
						for line in output.splitlines():
							if "ERROR" in line and t_name in line:
								try:
									api_logger.info("Found ERROR")
									dedugStack += time.strftime("%m-%d-%Y %H:%M:%S")+": "
									dedugStack += line.split("com/sinfonier")[1]
									dedugStack += "|"
								except Exception as e:
									api_logger.error("Error parsing errors from output. "+str(e))
									pass
							if "BUILD FAILURE" in line:
								api_logger.info("Found BUILD FAUILURE")
								errorDebug = True
							if "WARNING" in line and t_name in line:
								try:
									api_logger.info("Found WARNING")
									warDebug = True
									warStack += time.strftime("%m-%d-%Y %H:%M:%S")+": "
									warStack += line.split("com/sinfonier")[1]
									warStack += "|"
								except Exception as e:
									api_logger.error("Error parsing errors from output. "+str(e))
									pass
							if "Finished at:" in line:
								api_logger.info("Store Finished time")
								fDate = line
						if errorDebug:
							api_logger.error("Error compiling module. "+str(dedugStack))
							self.finish('{"result":"error","description":"Error compiling...", "detail":"'+str(dedugStack)+'"}')
						elif warDebug:
							api_logger.info("Warning during compiling. "+str(warStack))
							self.finish('{"result":"warning","description":"Warning during compiling", "detail":"'+str(warStack)+'"}')
						else:
							api_logger.info("Module compiled. "+str(fDate))
							self.finish('{"result":"success","description":"Module compiled", "detail":"'+str(fDate)+'"}')						
		else:
			api_logger.error("Content-Type:application/json missing")
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')