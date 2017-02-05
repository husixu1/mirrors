import configparser
import re
from subprocess import call

class configurator:
	# the legal global config Keys
	syncConfigKeys = { "maxthreadnum":0, "lockpolicy":0,"timeout":0,"defaultrsyncparameter":0}
	syncConfigKeyDefault = {"maxthreadnum":"2", "lockpolicy":"wait", "timeout":"1d","defaultrsyncparameter":""}
	# the legal config keys, 1 means that the key must exist
	mirrorConfigKeys = {
		"COMMON":{"synctool":1,"url":1,"synctime":0,"syncpath":1,"priority":0},
		"rsync":{"parameter":0},
		"pypimirror":{"parameter":0, "configfilename":0, "logfilename":0} }
	mirrorConfigKeyDefault = {
		"COMMON":{"synctool":"","url":"","synctime":"00:00","syncpath":"","priority":"1"},
		"rsync":{"parameter":""},
		"pypimirror":{"parameter":"-v -U -c", "configfilename":"", "logfilename":"pypimirror_log"} }

	ScriptDirectory = "Scripts"

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
					self.verbose("warning: key "+key+" unidentified", 1)
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
		syncParser = configparser.ConfigParser()
		mirrorParser = configparser.ConfigParser()
		if syncParser.read(syncConfigFileName)==[]:
			self.perror("config File "+syncConfigFileName+" not found, exiting...", 1)
			return False
		if mirrorParser.read(mirrorConfigFileName)==[]:
			self.perror("config File "+mirrorConfigFileName+" not found, exiting...", 1)
			return False
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
					elif key in configurator.mirrorConfigKeyDefault[synctool]:
						buff = replacer.sub(configurator.mirrorConfigKeyDefault[synctool][key],1)
					else:
						self.perror('Template: key "'+key+'" not found')
			except FileNotFoundError:
				self.perror("file \""+synctool+"Template\" not found")
				return False
			buffs.append((section, buff))
		return buffs

	def generateExcutables(self, syncCommands):
		# make the script directory
		if call(["test","-d",configurator.ScriptDirectory]) == 1:
			self.verbose("directory "+configurator.ScriptDirectory+" does not exist, creating one...", 2)
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

	def writeCrontab(self, sections):
		pass

	def perror(self, error, level=1):
		if self.debugLevel >= level:
			print("error: "+error)

	def verbose(self, info, level=2):
		if self.debugLevel >= level:
			print(info)
