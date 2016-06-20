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

import datetime

from pymongo import MongoClient
from tornado.options import options


class MongoHandler(object):

	def __init__(self):
		self.client = None
		self.auth = None
		self.db = None
		self.coll = None

	def mongoStartCon(self):
		self.client = MongoClient(options.mongo_host)
		self.db = self.client[options.mongo_database]

	def updateState(self,name,status):
		self.coll = self.db[options.mongo_collection]
		return self.coll.update({'name':name},{'$set': {'status': status}})
	
	def updateStartAt(self,name):
		self.coll = self.db[options.mongo_collection]
		return self.coll.update({'name':name},{'$set': {'started_at': datetime.datetime.utcnow()}})

	def updateStopAt(self,name):
		self.coll = self.db[options.mongo_collection]
		return self.coll.update({'name':name},{'$set': {'stopped_at': datetime.datetime.utcnow()}})

	def updateRunningState(self,name):
		self.coll = self.db[options.mongo_collection]
		return self.coll.update({'name':name},{'$set': {'status': "running", 'started_at': datetime.datetime.utcnow()}})

	def updateStoppedState(self,name):
		self.coll = self.db[options.mongo_collection]
		return self.coll.update({'name':name},{'$set': {'status': "stopped", 'stopped_at': datetime.datetime.utcnow()}})

	def mongoStopCon(self):
		self.client.close()
