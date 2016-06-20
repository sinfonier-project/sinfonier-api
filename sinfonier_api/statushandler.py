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
import config
import requests

from utils import *
from tornado.options import options
from bs4 import BeautifulSoup

api_logger = config.getlog()
stormuiapi = config.getStormUIAPI()


class Status(BaseHandler):
	"""
	Get status by topology name using Storm list command

	Params:
		name: string
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
				except Exception as e:
					api_logger.error("Error requests params "+str(e))
					self.finish('{"result":"error","description":"Error requests params","debug":"'+str(e)+'"}')
				# <STORM_PATH>/storm/bin/storm list
				cmd_launch = options.storm_binary+" list"
				cmd = utils.execCommand(cmd_launch)
				# Get output and error
				(output, err) = cmd.execute()
				if err:
					api_logger.error("Error getting topology list. "+str(err))
					self.finish('{"result":"error","description":"Error getting topology list","detail":"'+str(err)+'"}')
				elif output:
					api_logger.debug("Command output: "+str(output))
					notFound = False
					topoState = ""
					for line in output.splitlines():
						if t_name in line:
							notFound = True
							try:
								api_logger.info("Found Topology")
								api_logger.debug(line.split(" "))
								for aux in line.split(" "):
									if aux != "" and aux != t_name:
										api_logger.info("Status found: "+str(aux))
										topoState = aux
										break
							except Exception as e:
								api_logger.error("Error parsing errors from output. "+str(e))
								pass
					if not notFound:
						api_logger.error("Topology not found.")
						self.finish('{"result":"error","description":"Topology not found"}')
					elif notFound:
						api_logger.info("Topology Status. "+str(topoState))
						self.finish('{"result":"success","description":"Topology Status", "detail":"'+str(topoState)+'"}')
					else:
						api_logger.error("Something was wrong.")
						self.finish('{"result":"error","description":"Something was wrong"}')
		else:
			api_logger.error("Content-Type:application/json missing")
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')


class StatusV3(BaseHandler):
	"""
	Get status by topology name using Storm UI API

	Params:
		name: string
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
			if 'name' not in list(data.keys()):
				api_logger.error("Error requests params.")
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				try:
					t_name = data['name']
				except Exception as e:
					api_logger.error("Error requests params "+str(e))
					self.finish('{"result":"error","description":"Error requests params","debug":"'+str(e)+'"}')
			try:
				response = stormuiapi.getTopologySummaryByName(t_name)
			except Exception as e:
				api_logger.error("Error querying Storm UI API "+str(e))
				self.finish('{"result":"error","description":"Error querying Storm UI API","debug":"'+str(e)+'"}')

			if response:
				api_logger.info("StormUI Api: topology found!")
				status = response["status"]
				api_logger.info("StormUI Api: status found : "+str(status))
				self.finish('{"result":"success","description":"Status found", "detail":"'+str(status)+'"}')
			else:
				api_logger.info("StormUI Api: Status NOT found because Topology NOT found!")
				self.finish('{"result":"error","description":"Status NOT found because Topology NOT found", "detail":""}')
		else:
			api_logger.error("Content-Type:application/json missing")
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')


class StatusV2(BaseHandler):
	"""
	Get status by topology name using Storm UI web page.

	Params:
		name: string
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
			if 'name' not in list(data.keys()):
				api_logger.error("Error requests params.")
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				try:
					t_name = data['name']
				except KeyError as e:
					api_logger.error("Error requests params %s" % str(e))
					self.finish('{"result":"error","description":"Error requests params","debug":"%s"}' % str(e))
					return

				# Check status on UI
				try:
					url = "http://127.0.0.1:8080"
					api_logger.debug("URL to fetch: %s" % url)
					content = requests.get(url).text

					soup = BeautifulSoup(content)
					status = soup.find('a', href=True, text=t_name).find_parent().find_parent().findAll('td')[2].text
					api_logger.debug("Status found! "+status)

					self.finish('{"result":"success","description":"Status found", "detail":"'+str(status)+'"}')
				except requests.exceptions.HTTPError as e:
					api_logger.error("Error getting data from Storm UI"+str(e))
					self.finish('{"result":"error","description":"Error getting data from Storm UI", "detail":"'+str(e)+'"}')
				except AttributeError as e:
					api_logger.error("Error parsing data from Storm UI"+str(e))
					self.finish('{"result":"error","description":"Error parsing data from Storm UI", "detail":"'+str(e)+'"}')
				except IndexError as e:
					api_logger.error("Error parsing data from Storm UI"+str(e))
					self.finish('{"result":"error","description":"Error parsing data from Storm UI", "detail":"'+str(e)+'"}')
				except Exception as e:
					api_logger.error("Uknown error "+str(e))
					self.finish('{"result":"error","description":"Uknown error", "detail":"'+str(e)+'"}')
				
		else:
			api_logger.error("Content-Type:application/json missing")
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')
