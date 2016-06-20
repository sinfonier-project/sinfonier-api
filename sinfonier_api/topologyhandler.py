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

import json
import time
import utils
import config

from utils import *
from tornado.options import options

from mongohandler import MongoHandler

api_logger = config.getlog()
stormuiapi = config.getStormUIAPI()


class RunTopology(BaseHandler):
	"""
	Lunch topology on cluster.

	Params:
		name: string
		xml: string
		reload: bool
	"""

	def prepare(self):
		content_type = self.request.headers.get("Content-Type", "")
		if content_type.startswith("application/json"):
			self.arguments = tornado.escape.json_decode(self.request.body)
		else:
			self.arguments = None

	def post(self):
		if self.arguments:
			api_logger.info("HEADERS: " + str(self.request))
			# Parse each param
			data = self.arguments
			if 'name' not in list(data.keys()) or 'xml' not in list(data.keys()) or 'reload' not in list(data.keys()):
				api_logger.error("Error requests params")
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				try:
					t_name = data['name']
					t_xml = data['xml']
					api_logger.info("XML: " + str(t_xml))
					t_reload = data['reload']
				except Exception as e:
					api_logger.error("Error requests params" + str(e))
					self.write('{"result":"error","description":"Error requests params","debug":"' + str(e) + '"}')

			u = Utils()

			try:
				# Create folder (named as topology name) if not exists
				u.checkAndcreate(options.storm_topology_path + str(t_name), "storm", "storm")
				try:
					# Create folder /var/storm/topologies/{name}/config if not exists
					u.checkAndcreate(options.storm_topology_path + str(t_name) + options.storm_topology_config_path,
					                 "storm", "storm")
					try:
						# Create folder /data/storm/topologies/{name}/jar if not exists
						u.checkAndcreate(
							options.storm_topology_data_path + str(t_name) + options.storm_topology_jar_path, "storm",
							"storm")
					except Exception as e:
						api_logger.error("Error on Create folder " + options.storm_topology_data_path + str(
							t_name) + options.storm_topology_jar_path + " if not exists. " + str(e))
				except Exception as e:
					api_logger.error("Error on Create folder " + options.storm_topology_path + str(
						t_name) + options.storm_topology_config_path + " if not exists. " + str(e))
			except Exception as e:
				api_logger.error("Error on Create folder (named as topology name) if not exists. " + str(e))
			
			if t_reload:
				# Use global jar /var/storm/lastjar/file.jar
				jar_path = options.storm_global_jar_path + options.storm_global_jar_bin
			else:
				# Use last jar /var/storm/topologies/{name}/jar/file.jar
				jar_path = options.storm_topology_data_path + str(
					t_name) + options.storm_topology_jar_path + storm_global_jar_bin
			#
			# Create xml file 
			# 		/var/storm/{topologyname}/config/
			try:
				with open(options.storm_topology_path + str(t_name) + options.storm_topology_config_path + str(
						t_name) + ".xml", "w") as builder_file:
					builder_file.write(str(t_xml))
			except Exception as e:
				api_logger.error("Error creating config file. " + str(e))
				self.finish('{"result":"error","description":"Error creating config file."}')

			# Launch topology
			#	<STORM_BINARY_PATH>/storm 
			#				jar /var/storm/lastjar/sinfonier-community-1.0.0.jar com.sinfonier.DynamicTopology 
			#							/var/storm/{topologyname}/config/TOPOLOGY_NAME.xml TOPOLOGY_NAME
			cmd_launch = options.storm_binary + " jar " + jar_path + " com.sinfonier.DynamicTopology " + \
			             options.storm_topology_path + str(t_name) + options.storm_topology_config_path + str(t_name) + ".xml " + str(t_name)
			cmd = execCommand(cmd_launch)
			# Get output and error
			(output, err) = cmd.execute()
			if err:
				try:
					error = err.split("\n")[0].replace('"', '#')
					error = error.split("\n")[0].replace('`', '#')
				except Exception as e:
					api_logger.error("Error getting exception from JAVA.")
					error = "Unkown error"
				api_logger.error("Error executing launching topology command. " + str(err))
				self.finish(
					'{"result":"error","description":"Error launching topology", "detail":"' + str(error) + '"}')
			else:
				api_logger.debug("Command output: " + str(output))
				errorDebug = False
				warDebug = False
				dedugStack = ""
				warStack = ""
				fDate = ""
				for line in output.splitlines():
					if "ERROR" in line:
						errorDebug = True
						api_logger.error("Found ERROR TAG: Error launching topology. " + str(dedugStack))
						dedugStack = line
						break
				if errorDebug:
					self.finish('{"result":"error","description":"Error launching topology", "detail":"' + str(
						dedugStack) + '"}')
				else:
					# Change state on mongo
					moncon = MongoHandler()
					moncon.mongoStartCon()
					moncon.updateRunningState(t_name)
					moncon.mongoStopCon()
					self.finish('{"result":"success","description":"Topology running"}')
		else:
			api_logger.error("Content-Type:application/json missing")
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')


class StopTopology(BaseHandler):
	"""
	Stop topology on cluster.

	Params:
		name
	"""

	def prepare(self):
		content_type = self.request.headers.get("Content-Type", "")
		if content_type.startswith("application/json"):
			self.arguments = tornado.escape.json_decode(self.request.body)
		else:
			self.arguments = None

	def post(self):
		if self.arguments:
			# Parse each param
			data = self.arguments
			if 'name' not in list(data.keys()):
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				t_name = ""
				try:
					t_name = data['name']
				except Exception as e:
					api_logger.error("Error requests params: " + str(e))
					self.write('{"result":"error","description":"Error requests params","debug":"' + str(e) + '"}')

				## Get Topology ID

				topo_info = stormuiapi.getTopologySummaryByName(t_name)
				if topo_info:
					topo_id = topo_info["id"]
					api_logger.debug("Stopping topology " + t_name)
					response = stormuiapi.killTopology(topo_id, "0")
					if response["status"] == "KILLED":

						# Change state on mongo
						moncon = MongoHandler()
						moncon.mongoStartCon()
						moncon.updateStoppedState(t_name)
						moncon.mongoStopCon()
						# Delete worker file
						try:
							os.remove(options.storm_topology_path + t_name + "/worker")
						except:
							api_logger.debug("Error removing worker file of topology " + t_name + ". Continuing...")
						self.finish('{"result":"success","description":"Topology stopped"}')

					else:
						api_logger.error("Topology '" + t_name + "' couldn't be stopped")
						api_logger.error(json.dumps(response))
						self.write(
							'{"result":"error","description":"Topology "' + t_name + '" could not be stopped",'
							                                                         '"debug":""}')

				else:
					api_logger.error("Topology '" + t_name + "' not found")
					self.write('{"result":"error","description":"Topology '"+t_name+"' not found","debug":""}')

		else:
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')


class UpdateTopology(BaseHandler):
	"""
	Update topology running.

	Params:
		name: string
		xml: string
		reload: bool
	"""

	def prepare(self):
		content_type = self.request.headers.get("Content-Type", "")
		if content_type.startswith("application/json"):
			self.arguments = tornado.escape.json_decode(self.request.body)
		else:
			self.arguments = None

	def post(self):
		if self.arguments:
			# Parse each param
			data = self.arguments
			if 'name' not in list(data.keys()) or 'xml' not in list(data.keys()) or 'reload' not in list(data.keys()):
				self.finish('{"result":"error","description":"Error requests params"}')
			else:
				try:
					t_name = data['name']
					t_xml = data['xml']
					t_reload = data['reload']
				except Exception as e:
					api_logger.error("Error requests params: " + str(e))
					self.write('{"result":"error","description":"Error requests params","debug":"' + str(e) + '"}')

			## STOP TOPOLOGY

			topo_info = stormuiapi.getTopologySummaryByName(t_name)
			api_logger.debug("Stopping topology " + t_name)
			if topo_info:
				topo_id = topo_info["id"]

				response = stormuiapi.killTopology(topo_id, "0")
				if response["status"] == "KILLED":
					
					## Topology Killed
					# Change state on mongo
					moncon = MongoHandler()
					moncon.mongoStartCon()
					moncon.updateState(t_name, "hold")

					for i in range(4):
						response = stormuiapi.getTopologySummaryByName(t_name)
						if not response:
							api_logger.info("Topology " + t_name + " killed.")
							break
						time.sleep(5)
					else:
						api_logger.debug("Topology " + t_name + " couldn't be stopped on time. Waiting 5 sec more...")
						time.sleep(5)

					if t_reload == "true":
						# Use global jar /var/storm/lastjar/file.jar
						jar_path = options.storm_global_jar_path + options.storm_global_jar_bin
					else:
						# Use last jar /var/storm/topologies/{name}/jar/file.jar
						jar_path = options.storm_topology_data_path + str(
							t_name) + options.storm_topology_jar_path + storm_global_jar_bin
					#
					# Create xml file 
					# 		/var/storm/{topologyname}/config/
					try:
						with open(options.storm_topology_path + str(t_name) + options.storm_topology_config_path + str(
								t_name) + ".xml", "w") as builder_file:
							builder_file.write(str(t_xml))
					except Exception:
						self.finish('{"result":"error","description":"Internal error"}')

					# Launch topology
					#	/opt/sinfonier/storm/bin/storm 
					#				jar /var/storm/lastjar/sinfonier-community-1.0.0.jar com.sinfonier.DynamicTopology 
					#							/var/storm/{topologyname}/config/TOPOLOGY_NAME.xml TOPOLOGY_NAME
					api_logger.debug("Restarting topology " + t_name + ".")
					cmd_launch = options.storm_binary + " jar " + jar_path + " com.sinfonier.DynamicTopology " + \
					             options.storm_topology_path + str(
						t_name) + options.storm_topology_config_path + str(t_name) + ".xml " + str(t_name)
					cmd = execCommand(cmd_launch)
					# Get output and error
					(output, err) = cmd.execute()
					if err:
						# Change state on mongo
						moncon = MongoHandler()
						moncon.mongoStartCon()
						moncon.updateStoppedState(t_name)
						moncon.mongoStopCon()
						self.finish(
							'{"result":"error","description":"Error launching topology","detail":"' + str(err) + '"}')
					else:
						api_logger.info("Topology " + t_name + " updated successfully")
						# Change state on mongo
						moncon = MongoHandler()
						moncon.mongoStartCon()
						moncon.updateRunningState(t_name)
						moncon.mongoStopCon()
						self.write('{"result":"success","description":"Topology restarted."}')
				else:
					# TOPOLOGY NOT KILLED
					self.finish('{"result":"error","description":"Error stopping topology","detail":"Not killed"}')
		else:
			self.finish('{"result":"error","description":"Content-Type:application/json missing"}')
