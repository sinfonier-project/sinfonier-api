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

import logging
import os

import stormuiapi

from logging import handlers
from tornado.options import define, options

# MONGO CONFIG
define("port", default=8899, help="run on the given port", type=int)
define("concurrency", default=0, help="num of proceess", type=int)
define("mongo_host", default="localhost", help="sinfonier database host")
define("mongo_database", default="sinfonier", help="mongo database name")
define("mongo_collection", default="topologies", help="mongo collection name")

# STORM CLUSTER
# 		GLOBAL CONFIG
define("storm_binary", default="/usr/local/storm/bin/storm", help="storm binay")
define("storm_global_jar_path", default="/var/storm/lastjar/", help="storm binary path")
define("storm_global_jar_bin", default="sinfonier-community-1.0.0.jar", help="storm binay")
# 		TOPOLOGIES CONFIG
define("storm_topology_path", default="/var/storm/topologies/", help="storm xml path")
define("storm_topology_config_path", default="/config/", help="storm topology config folder")
define("storm_topology_data_path", default="/data/storm/topologies/", help="topologies data path")
define("storm_topology_jar_path", default="/jar/", help="storm topology config folder")

# FOLDER STRUCTURE
#   /var/storm/topologies/{topologyName}/config/{topologyName}.xml

# 		MAVEN CONFIG
define("maven_binary", default="/usr/local/maven/bin/mvn", help="maven binay")
define("maven_sinfonier_pom", default="/var/storm/src/sinfonier_backend/pom.xml", help="maven pom")
define("maven_sinfonier_m2_pom", default="/var/storm/src/sinfonier_backend/m2-pom.xml", help="maven m2-pom")

# STORMBACKEND
define("backend_working_path", default="/var/storm/src/sinfonier_backend/", help="backend path")
define("backend_python_path", default="/var/storm/src/sinfonier_backend/multilang/resources/",
       help="backend python path")
define("backend_java_path", default="/var/storm/src/sinfonier_backend/src/jvm/com/sinfonier/", help="backend java path")

define("backend_java_path_drains", default="/var/storm/src/sinfonier_backend/src/jvm/com/sinfonier/drains/",
       help="backend drains")
define("backend_java_path_bolts", default="/var/storm/src/sinfonier_backend/src/jvm/com/sinfonier/bolts/",
       help="backend bolts")
define("backend_java_path_spouts", default="/var/storm/src/sinfonier_backend/src/jvm/com/sinfonier/spouts/",
       help="backend spouts")

BASE_PATH = os.path.dirname(__file__)

# API TEMPLATES
define("backend_template_path", default=os.path.join(BASE_PATH, "templates"), help="API templates")

# GISTS CREDENTIALS

define("gist_api_token", default="<API_TOKEN_GIST>", help="gist api token")
define("gist_username", default="<USER_GIST>", help="gist username")

# Logging config
MAX_BYTES = 3000000
BACKUP_NUM = 3
LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(name)s  - %(message)s'
LOG_LOCATION = os.environ.get("SINFONIER_LOG", os.path.join(BASE_PATH, "api.log"))

# For avoid non-existin log file problems we create if
with open(LOG_LOCATION, "w") as f:
	f.write("\n")

api_logger = logging.getLogger('sinfonier-api')
api_logger.setLevel(logging.DEBUG)
fh = handlers.RotatingFileHandler(LOG_LOCATION, maxBytes=MAX_BYTES, backupCount=BACKUP_NUM)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(LOGGING_FORMAT)
fh.setFormatter(formatter)
api_logger.addHandler(fh)


def getlog():
	return api_logger


def getStormUIAPI():
	return stormuiapi.StormUIAPI()
