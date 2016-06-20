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

from __future__ import print_function

import os
import re
import pwd
import grp
import errno

import config
import subprocess
import simplegist
import unicodedata

try:
	from urlparse import urlparse
except ImportError:
	from urllib.parse import urlparse

from tornado.options import options
from jinja2 import Environment, FileSystemLoader

import tornado.web

api_logger = config.getlog()


class BaseHandler(tornado.web.RequestHandler):
	"""
	Base Class used on every Handler
	"""

	def checkMaven(self):
		pass


class execCommand(object):

	def __init__(self, cmdlaunch):
		self.cmdlaunch = cmdlaunch

	def execute(self):
		launch = subprocess.Popen(self.cmdlaunch, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		output, err = launch.communicate()
		return output, err


class Utils(object):

	def lastlines(self, hugefile, n, bsize=2048):
		# get newlines type, open in universal mode to find it
		with open(hugefile, 'rU') as hfile:
			if not hfile.readline():
				return  # empty, no point
			sep = hfile.newlines  # After reading a line, python gives us this
		assert isinstance(sep, str), 'multiple newline types found, aborting'

		# find a suitable seek position in binary mode
		with open(hugefile, 'rb') as hfile:
			hfile.seek(0, os.SEEK_END)
			linecount = 0
			pos = 0

			while linecount <= n + 1:
				# read at least n lines + 1 more; we need to skip a partial line later on
				try:
					hfile.seek(-bsize, os.SEEK_CUR)  # go backwards
					linecount += hfile.read(bsize).count(sep)  # count newlines
					hfile.seek(-bsize, os.SEEK_CUR)  # go back again
				except IOError as e:
					if e.errno == errno.EINVAL:
						# Attempted to seek past the start, can't go further
						bsize = hfile.tell()
						hfile.seek(0, os.SEEK_SET)
						linecount += hfile.read(bsize).count(sep)
						break
					raise  # Some other I/O exception, re-raise
				pos = hfile.tell()

		# Re-open in text mode
		with open(hugefile, 'r') as hfile:
			hfile.seek(pos, os.SEEK_SET)  # our file position from above

			for line in hfile:
				# We've located n lines *or more*, so skip if needed
				if linecount > n:
					linecount -= 1
					continue
				# The rest we yield
				yield line

	def checkAndcreate(self, dir, user, group):
		if not os.path.exists(dir):
			os.makedirs(dir)
			uid = pwd.getpwnam(user).pw_uid
			gid = grp.getgrnam(group).gr_gid
			os.chown(dir, uid, gid)
			return 1
		return 0

	def changeOwner(self, filePath, user, group):
		if os.path.exists(filePath):
			uid = pwd.getpwnam(user).pw_uid
			gid = grp.getgrnam(group).gr_gid
			os.chown(filePath, uid, gid)
			return 1
		return 0

	def write_module(self, module_name, module_lang, source_code, dst_path, module_type):
		"""Gets the source code of a module from a GitHub gist. 

		Args:
		    module_name: The name of the module.
		    module_lang: Code language.
		    source_code: Gist url.
		    dst_path: Absolute path for module on file sytem.

		Returns:
		    The file system path of the newly created module.

		Raises:
		    IOError: An error occurred accessing GitHub or creating the source files.
		"""

		print(type(source_code))

		api_logger.info("Module name: " + str(module_name))
		api_logger.info("Module lang: " + str(module_lang))
		# api_logger.info("Source code: "+str(source_code))
		api_logger.info("DST_PATH: " + str(dst_path))
		api_logger.info("MODULE Type: " + str(module_type))

		if module_lang == "py":
			file_name = os.path.join(dst_path, module_name.lower() + "." + module_lang)
		elif module_lang == "java":
			file_name = os.path.join(dst_path, module_name + "." + module_lang)
		# Get file name for gist and put into
		try:
			with open(file_name, "w") as text_file:
				text_file.write(unicodedata.normalize('NFKD', source_code).encode('ascii', 'ignore'))
				self.changeOwner(file_name, "storm", "storm")
		except Exception as e:
			print(str(e))
			api_logger.error(str(e))
			raise e
		if module_lang == "py":
			# Time to jinja2
			# Check module type
			if module_type == "drain":
				boltType = "drains"
				dst_path = options.backend_java_path_drains
				template_name = options.backend_template_path + "boltjava2python.tmpl"
			elif module_type == "bolt":
				boltType = "bolts"
				dst_path = options.backend_java_path_bolts
				template_name = options.backend_template_path + "boltjava2python.tmpl"
			elif module_type == "spout":
				boltType = "spouts"
				dst_path = options.backend_java_path_spouts
				template_name = options.backend_template_path + "spoutjava2python.tmpl"
			env = Environment(loader=FileSystemLoader('/'))

			template = env.get_template(template_name)
			file_name = os.path.join(dst_path, module_name + ".java")
			try:
				with open(file_name, "w") as text_file:
					text_file.write(
						template.render(boltName=module_name, boltType=boltType, boltNamelowercase=module_name.lower()))
					self.changeOwner(file_name, "storm", "storm")
			except Exception as e:
				api_logger.error(str(e))
				raise e
		return file_name
	
	def get_module(self, module_name, module_lang, gist_url, dst_path, module_type):
		"""Gets the source code of a module from a GitHub gist. 

		Args:
		    module_name: The name of the module.
		    module_lang: Code language.
		    gist_url: Gist url.
		    dst_path: Absolute path for module on file sytem.

		Returns:
		    The file system path of the newly created module.

		Raises:
		    IOError: An error occurred accessing GitHub or creating the source files.
		"""
		# Start gist handler
		API_TOKEN = options.gist_api_token
		USERNAME = options.gist_username
		GHgist = simplegist.Simplegist(username=USERNAME, api_token=API_TOKEN)

		api_logger.info("Module name: " + str(module_name))
		api_logger.info("Module lang: " + str(module_lang))
		api_logger.info("Gist URL: " + str(gist_url))
		api_logger.info("DST_PATH: " + str(dst_path))
		api_logger.info("MODULE Type: " + str(module_type))

		# Get Id and user from URL
		gist_id_reg = re.compile('([a-zA-Z0-9]+)')
		gist_user, gist_id = gist_id_reg.findall(urlparse(gist_url).path)

		api_logger.info("Gist USER: " + str(gist_user))
		api_logger.info("Gist ID: " + str(gist_id))

		# Download code from GIST
		GHgist.profile().getgist(id=gist_id)

		# Authenticate using a GitHub API access token.

		if module_lang == "py":
			file_name = os.path.join(dst_path, module_name.lower() + "." + module_lang)
		elif module_lang == "java":
			file_name = os.path.join(dst_path, module_name + "." + module_lang)
		else:
			file_name = None

		# Get file name for gist and put into
		try:
			with open(file_name, "w") as text_file:
				text_file.write(
					unicodedata.normalize('NFKD', GHgist.profile().content(id=gist_id)).encode('ascii', 'ignore'))
				self.changeOwner(file_name, "storm", "storm")
		except Exception as e:
			api_logger.error(str(e))
			raise e
		if module_lang == "py":
			# Time to jinja2
			# Check module type
			if module_type == "drain":
				boltType = "drains"
				dst_path = options.backend_java_path_drains
				template_name = options.backend_template_path + "boltjava2python.tmpl"
			elif module_type == "bolt":
				boltType = "bolts"
				dst_path = options.backend_java_path_bolts
				template_name = options.backend_template_path + "boltjava2python.tmpl"
			elif module_type == "spout":
				boltType = "spouts"
				dst_path = options.backend_java_path_spouts
				template_name = options.backend_template_path + "spoutjava2python.tmpl"
			env = Environment(loader=FileSystemLoader('/'))

			template = env.get_template(template_name)
			file_name = os.path.join(dst_path, module_name + ".java")
			try:
				with open(file_name, "w") as text_file:
					text_file.write(
						template.render(boltName=module_name, boltType=boltType, boltNamelowercase=module_name.lower()))
					self.changeOwner(file_name, "storm", "storm")
			except Exception as e:
				api_logger.error(str(e))
				raise e
		return file_name
