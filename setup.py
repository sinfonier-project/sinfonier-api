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


from os.path import dirname, join
from setuptools import setup, find_packages

# Import requirements
with open(join(dirname(__file__), 'requirements.txt')) as f:
	required = f.read().splitlines()

setup(
	name='sinfonier-api',
	version='1.0.0',
	install_requires=required,
	url='https://github.com/sinfonier-project/sinfonier-api',
	license='Apache License',
	author='Sinfonier Project',
	packages=find_packages(),
	include_package_data=True,
	entry_points={'console_scripts': [
		'sinfonier-api = sinfonier_api.sinfonierapicore:main',
	]},
	description='Sinfonier API was develop to manage Sinfonier Backend and deal with Apache Storm cluster. This '
	            'software is part of Sinfonier-Project',
	long_description=open('README.md', "r").read(),
	classifiers=[
		'Environment :: Console',
		'Intended Audience :: System Administrators',
		'Intended Audience :: Other Audience',
		'License :: OSI Approved :: BSD License',
		'Operating System :: MacOS',
		'Operating System :: Microsoft :: Windows',
		'Operating System :: POSIX',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 3',
		'Topic :: Security',
	]
)
