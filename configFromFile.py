import configparser
import re
from subprocess import call
import sys

class configurator:
	# the legal global config Keys
	syncConfigKeys = {
		"maxthreadnum":0,
		"lockpolicy":0,
		"timeout":0,
		"synclog":0,
	}
	syncConfigKeyDefault = {
		"maxthreadnum":"2",
		"lockpolicy":"wait",
		"timeout":"1d",
		"synclog":"syncLog.log"
	}
	# the legal config keys, 1 means that the key must exist
	mirrorConfigKeys = {
		"COMMON":{
                        "synctool":1,
                        "url":1,
                        "synctime":0,
						"syncinterval":0,
                        "syncpath":1,
                        "priority":0
		},
		"rsync":{
                        "parameter":0
		},
		"bandersnatch":{
                        "parameter":0,
                        "configfilename":0,
                        "logfilename":0
		},
		"git":{
			"parameter":0
		}
	}
	mirrorConfigKeyDefault = {
		"COMMON":{
                        "synctool":"",
                        "url":"",
                        "synctime":"0",
						"syncinterval":1,
                        "syncpath":"",
                        "priority":"1"},
		"rsync":{
                        "parameter":"--verbose --recursive --update --links --hard-links --safe-links --perms --times --delete-after --progress --human-readable "},
		"bandersnatch":{
                        "parameter":"-c",
                        "configfilename":"bandersnatch_config.conf",
                        "logfilename":"bandersnatch_log.log"
		},
		"git":{
			"parameter":"remote -v update"
		}
	}

	ScriptDirectory = "Scripts"
	cronFileName = "cron"

	def __init__(self, debugLevel_ = 0):
		self.debugLevel = debugLevel_

	def checkSyncConfigAccuracy(self, filename):
		parser = configparser.ConfigParser()
		globalSection = 'GLOBAL'
		#read the config file
		if parser.read(filename) == []:
			self.perror("config File "+filename+" not found, exiting...", 1)
			return False
		if not globalSection in parser.sections():
			self.perror("section GLOBAL missing")
			return False
		# check the unidentified keys
		for key in parser[globalSection]:
			if not key in configurator.syncConfigKeys:
				self.verbose("warning: key "+key+" unidentified", 1)
		# check the must-exist keys
		isKeyExist = True
		for key in configurator.syncConfigKeys:
			if configurator.syncConfigKeys[key]==1 and not key in parser[globalSection]:
				self.perror("key "+key+" must exist", 1)
				isKeyExist = False
		return isKeyExist

	def checkMirrorConfigAccuracy(self, filename):
		parser = configparser.ConfigParser()
		# read the config file
		if parser.read(filename) == []:
			self.perror("config File "+filename+" not found, exiting...", 1)
			return False
		# read the configs
		for section in parser.sections():
			# check the 'synctool' key
			try:
				syncKeys = dict(configurator.mirrorConfigKeys[parser[section]["synctool"]], **configurator.mirrorConfigKeys["COMMON"])
			except KeyError:
				self.perror("in section "+section+": synctool missing or incorrect")
				return False
			# check the unidentified keys
			for key in parser[section]:
				if not key in syncKeys:
					self.verbose("warning: in section "+section+": key "+key+" unidentified", 1)
			# check the must-exist keys
			isKeyExist = True
			for key in syncKeys:
				if syncKeys[key]==1 and not key in parser[section]:
					self.perror("in section "+section+" : key "+key+" must exist", 1)
					isKeyExist = False
		return isKeyExist

	def generateSyncCommands(self, syncConfigFileName, mirrorConfigFileName):
		"""generate sync command from two config file
		:return False if error occurred
		:return a list of (section, command) if no error occurred
		"""
		if not self.checkMirrorConfigAccuracy(mirrorConfigFileName):
			return  False
		if not self.checkSyncConfigAccuracy(syncConfigFileName):
			return False

		syncParser = configparser.ConfigParser()
		syncParser.read(syncConfigFileName)
		mirrorParser = configparser.ConfigParser()
		mirrorParser.read(mirrorConfigFileName)

		buffs = []
		for section in mirrorParser.sections():
			buff = ''
			synctool = mirrorParser[section]["synctool"]
			# the replacer that replace all the macros in template
			replacer = re.compile(r'%\((\w+)\)%')
			legalKeys = dict(configurator.syncConfigKeys, **configurator.mirrorConfigKeys[synctool])
			legalKeys.update(configurator.mirrorConfigKeys["COMMON"])
			try:
				template = open("templates/"+synctool+"Template","r")
				buff = template.read()
				for key in replacer.findall(buff):
					key = key.lower()
					# check macro's legitimacy
					if not key in legalKeys:
						self.perror('Template: illegal key "'+key+'"')
						return False
					# replace macro with value
					if key in syncParser["GLOBAL"]:
						buff = replacer.sub(syncParser["GLOBAL"][key],buff,1)
					elif key in mirrorParser[section]:
						buff = replacer.sub(mirrorParser[section][key],buff,1)
					elif key in configurator.syncConfigKeys:
						buff = replacer.sub(configurator.syncConfigKeyDefault[key],buff,1)
					elif key in configurator.mirrorConfigKeyDefault["COMMON"]:
						buff = replacer.sub(configurator.mirrorConfigKeyDefault["COMMON"][key],buff,1)
					elif key in configurator.mirrorConfigKeyDefault[synctool]:
						buff = replacer.sub(configurator.mirrorConfigKeyDefault[synctool][key],buff,1)
					else:
						self.perror('Template: key "'+key+'" not found')
						return False
			except FileNotFoundError:
				self.perror("file \""+synctool+"Template\" not found")
				return False
			buffs.append((section, buff))
		return buffs

	def generateExcutables(self, syncConfigFileName, mirrorConfigFileName):
		"""generate excutables from two file
		note : this will remove the old excutales
		"""
		syncCommands = self.generateSyncCommands(syncConfigFileName, mirrorConfigFileName)
		if not syncCommands:
			return False
		# make the script directory
		if call(["test","-d",configurator.ScriptDirectory]) == 1:
			self.verbose("directory "+configurator.ScriptDirectory+" does not exist, creating one...", 2)
			call(["mkdir",configurator.ScriptDirectory])
		else:
			call(["rm","-rf",configurator.ScriptDirectory])
			call(["mkdir",configurator.ScriptDirectory])
		# write buffs into file
		for (section,command) in syncCommands:
			outFile = open(configurator.ScriptDirectory+'/'+section+'.sh',"w")
			outFile.write(command)
			outFile.close()
			call(["chmod","+x",configurator.ScriptDirectory+'/'+section+'.sh'])

			self.verbose("========"+section+".sh=======", 2)
			self.verbose(command,2)
		return True

	def writeCrontab(self, configFilename):
		if not self.checkMirrorConfigAccuracy(configFilename):
			return False
		parser = configparser.ConfigParser()
		parser.read(configFilename)

		rootDir = sys.path[0]
		cronFile = open(configurator.cronFileName,"w")
		# write the cron tab according to sync time and sync interval
		for section in parser.sections():
			if "synctime" in parser[section]:
				syncTime = parser[section]["synctime"]
			else:
				syncTime = self.mirrorConfigKeyDefault["COMMON"]["synctime"]
			if "syncinterval" in parser[section]:
				syncInterval = parser[section]["syncinterval"]
			else:
				syncInterval = self.mirrorConfigKeyDefault["COMMON"]["syncinterval"]
			cronFile.write('* %s */%s * * /bin/sh %s/%s/%s.sh\n'%(syncTime, syncInterval, rootDir,configurator.ScriptDirectory,section))
		cronFile.close()
		# write into crontab
		self.verbose("writing crontab... ", 0)
		call(['sudo','crontab','-u','root',configurator.cronFileName])

	def perror(self, error, level=1):
		if self.debugLevel >= level:
			print("error: "+error)

	def verbose(self, info, level=2):
		if self.debugLevel >= level:
			print(info)
