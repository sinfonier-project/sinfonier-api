# Sinfonier API

![Figure 1 - Sinfonier Simple View](docs/images/SinfonierSimple.png "Figure 1 - Sinfonier Simple View")

Sinfonier API was develop to manage [Sinfonier Backend](https://github.com/sinfonier-project/sinfonier-backend) and deal with Apache Storm cluster. This software is part of [Sinfonier-Project](http://sinfonier-project.net)

Sinfonier:

> Sinfonier is a change in the focus in respect to current solutions in the area of processing information in real-time. We combine an easy-to-use interface, modular and adaptable, and we integrate it with an advanced technological solution to allow you to do the necessary tune up suitable for your needs in matters of information security.

Apache Storm:

> Apache Storm is a free and open source distributed realtime computation system. Storm makes it easy to reliably process unbounded streams of data, doing for realtime processing what Hadoop did for batch processing. Storm is simple, can be used with any programming language, and is a lot of fun to use!

## Description

* Compile modules
* Manage Sinfonier Backend classpath
* Start/Stop Storm toplogies
* Storm Log management

## Installation

### Dependencies

Jinga2

```sh
$ cd /tmp/
$ wget https://pypi.python.org/packages/source/J/Jinja2/Jinja2-2.8.tar.gz
$ tar xvf Jinja2-2.8.tar.gz
$ cd Jinja2-2.8/
$ sudo python setup.py install
```

Crypto

```sh
$ sudo yum install python-crypto
```

PIP Dependencies

```sh
$ sudo pip install tornado requests pymongo simplegist paramiko scp BeautifulSoup4
```

### Configure 

MONGO CONFIG

```python
define("port", default=8899, help="run on the given port", type=int)
define("concurrency", default=0, help="num of proceess", type=int)
define("mongo_host", default="localhost", help="sinfonier database host")
define("mongo_database", default="sinfonier", help="mongo database name")
define("mongo_collection", default="topologies", help="mongo collection name")
```

STORM CLUSTER GLOBAL CONFIG

```python
define("storm_binary", default="<STORM_PATH>/bin/storm", help="storm binay")
define("storm_global_jar_path", default="/var/storm/lastjar/", help="storm binary path")
define("storm_global_jar_bin", default="sinfonier-community-1.0.0.jar", help="storm binay")
```

TOPOLOGIES CONFIG

```python
define("storm_topology_path", default="/var/storm/topologies/", help="storm xml path")
define("storm_topology_config_path", default="/config/", help="storm topology config folder")
define("storm_topology_data_path", default="/data/storm/topologies/", help="topologies data path")
define("storm_topology_jar_path", default="/jar/", help="storm topology config folder")
```

FOLDER STRUCTURE

    /var/storm/topologies/{topologyName}/config/{topologyName}.xml

MAVEN CONFIG

```python
define("maven_binary", default="<MAVEN_PATH>/bin/mvn", help="maven binay")
define("maven_sinfonier_pom", default="/var/storm/src/sinfonier_backend/pom.xml", help="maven pom")
define("maven_sinfonier_m2_pom", default="/var/storm/src/sinfonier_backend/m2-pom.xml", help="maven m2-pom")
```

STORMBACKEND
```python
define("backend_working_path", default="/var/storm/src/sinfonier_backend/", help="backend path")
define("backend_python_path", default="/var/storm/src/sinfonier_backend/multilang/resources/", help="backend python path")
define("backend_java_path", default="/var/storm/src/sinfonier_backend/src/jvm/com/sinfonier/", help="backend java path")

define("backend_java_path_drains", default="/var/storm/src/sinfonier_backend/src/jvm/com/sinfonier/drains/", help="backend drains")
define("backend_java_path_bolts", default="/var/storm/src/sinfonier_backend/src/jvm/com/sinfonier/bolts/", help="backend bolts")
define("backend_java_path_spouts", default="/var/storm/src/sinfonier_backend/src/jvm/com/sinfonier/spouts/", help="backend spouts")
```

API TEMPLATES

```python
define("backend_template_path", default="/opt/sinfonier-api/templates/", help="API templates")
```

GIST CREDENTIALS

```python
define("gist_api_token",default="<YOUR_GIST_TOKEN>",help="gist api token")
define("gist_username",default="<GIST_USER>",help="gist username")
```


### Deploy

```sh
$ cd /opt
$ git clone https://github.com/sinfonier-project/sinfonier-api.git
$ python sinfonierapicore.py

```

## Project leads

* Francisco J. Gomez @ffranz https://github.com/ffr4nz/
* Alberto J. Sanchez @ajsanchezsanz https://github.com/ajsanchezsanz

## Committers

* Eva Suarez @EvaSuarez22
* Pedro J. Martinez @pejema44

## Contributors


## License

Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0

## References

* http://www.tornadoweb.org/en/stable/
* http://storm.apache.org/
* https://maven.apache.org/

