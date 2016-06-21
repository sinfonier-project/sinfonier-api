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

import utils
from utils import *

from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
import os

import requests

from bs4 import BeautifulSoup

api_logger = config.getlog()
stormuiapi = config.getStormUIAPI()

class GetLog(BaseHandler):
	"""
	Get log from a topology connecting with Storm Slave using SSH protocol. WORST way!!

	Params:
		name
		lines
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
			if 'name' not in list(data.keys()) and 'lines' not in list(data.keys()):
				api_logger.error("Error requests params.")
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				try:
					t_name = data['name']
					t_lines = data['lines']
				except Exception as e:
					api_logger.error("Error requests params "+str(e))
					self.finish('{"result":"error","description":"Error requests params","debug":"'+str(e)+'"}')
				try:
					workerFile = open(options.storm_topology_path+t_name+"/worker","r")
					hostName,fileName = workerFile.read().splitlines()
					api_logger.debug("HostName LOG: "+hostName)
					api_logger.debug("FileName LOG"+fileName)
					#get log file from storm cluster
					ssh = SSHClient()
					ssh.load_system_host_keys()
					ssh.connect(hostName)
					ssh.set_missing_host_key_policy(AutoAddPolicy())
					scp = SCPClient(ssh.get_transport())
					api_logger.debug('/var/log/storm/'+fileName)
					scp.get('/var/log/storm/'+fileName,'/data/tmp/')
					u = Utils()
					api_logger.debug('/data/tmp/'+fileName)
					lines = ""
					for line in u.lastlines('/data/tmp/'+fileName,int(t_lines)):
						lines += line
					os.remove('/data/tmp/'+fileName)
					self.set_header ('Content-Type', 'text/plain')
					self.set_header ('Content-Disposition', 'attachment; filename='+fileName+'')
					self.finish(lines)
				except Exception as e:
					api_logger.error("Error getting topology log "+str(e))
					self.finish('{"result":"error","description":"Error getting topology log.", "detail":"Log not found, wait while your topology create it."}')
	
		else:
			api_logger.error("Content-Type:application/json missing")
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')

class GetLogV3(BaseHandler):
	"""
	Get log from a topology using Logviewer server and getting worker info using Storm API. Better way!!

	Params:
		name
		lines
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
			if 'name' not in list(data.keys()) and 'lines' not in list(data.keys()):
				api_logger.error("Error requests params.")
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				try:
					t_name = data['name']
					t_lines = data['lines']
				except Exception as e:
					api_logger.error("Error requests params "+str(e))
					self.finish('{"result":"error","description":"Error requests params","debug":"'+str(e)+'"}')
				try:
					filename = stormuiapi.getWorkersByTopologyName(t_name)[0]
					if filename:
						api_logger.info("LogFilename: "+filename)
						#get log file from storm cluster
						n_lines = int(t_lines)*200
						url = filename+"&tail="+str(n_lines)
						api_logger.debug("URL to fecth"+url)
						content = ""
						try:
							content = requests.get(url).content
						except Exception as e:
							api_logger.error("Error getting log from Storm UI : "+str(e))
							self.finish('{"result":"error","description":"Error getting log from Storm UI: ", "detail":"'+str(e)+'"}')
						try:
							# Remove HTML tags from Storm Log 8000 port
							lines = BeautifulSoup(content).text
							api_logger.debug("Getting "+str(len(lines.splitlines()))+" lines.")
							self.set_header ('Content-Type', 'text/plain')
							self.set_header ('Content-Disposition', 'attachment; filename='+filename+'')
							self.finish(lines)
						except Exception as e:
							api_logger.error("Error parsing data from Storm UI"+str(e))
							self.finish('{"result":"error","description":"Error parsing data from Storm UI: ", "detail":"'+str(e)+'"}')
					else:
						api_logger.error("Error getting worker from Storm UI API")
						self.finish('{"result":"error","description":"Error getting worker from Storm UI API", "detail":""}')
				except Exception as e:
					api_logger.error("Unknown error"+str(e))
					self.finish('{"result":"error","description":"Error getting topology log: ", "detail":"'+str(e)+'"}')
		else:
			api_logger.error("Content-Type:application/json missing")
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')

class GetLogV2(BaseHandler):
	"""
	Get log from a topology using Logviewer and getting worker log information from worker file.

	Params:
		name
		lines
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
			if 'name' not in list(data.keys()) and 'lines' not in list(data.keys()):
				api_logger.error("Error requests params.")
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				try:
					t_name = data['name']
					t_lines = data['lines']
				except Exception as e:
					api_logger.error("Error requests params "+str(e))
					self.finish('{"result":"error","description":"Error requests params","debug":"'+str(e)+'"}')
				try:
					workerFile = open(options.storm_topology_path+t_name+"/worker","r")
					hostName,fileName = workerFile.read().splitlines()
					workerFile.close()
					api_logger.debug("HostName LOG: "+hostName)
					api_logger.debug("FileName LOG"+fileName)
					#get log file from storm cluster
					n_lines = int(t_lines)*200
					url = "http://"+ str(hostName)+":8000/log?file="+str(fileName)+"&tail="+str(n_lines)
					api_logger.debug("URL to fecth"+url)
					content = ""
					try:
						content = requests.get(url).content
					except Exception as e:
						api_logger.error("Error getting log from Storm UI : "+str(e))
						self.finish('{"result":"error","description":"Error getting log from Storm UI: ", "detail":"'+str(e)+'"}')
					try:
						soup = BeautifulSoup(content)
						lines = soup.text
						api_logger.debug("Getting "+str(len(lines.splitlines()))+" lines.")
						self.set_header ('Content-Type', 'text/plain')
						self.set_header ('Content-Disposition', 'attachment; filename='+fileName+'')
						self.finish(lines)
					except Exception as e:
						api_logger.error("Error parsing data from Storm UI"+str(e))
						self.finish('{"result":"error","description":"Error parsing data from Storm UI: ", "detail":"'+str(e)+'"}')
				except Exception as e:
					api_logger.error("Unknown error"+str(e))
					self.finish('{"result":"error","description":"Error getting topology log: ", "detail":"'+str(e)+'"}')
		else:
			api_logger.error("Content-Type:application/json missing")
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')