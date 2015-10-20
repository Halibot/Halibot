#
# Main bot class
#    Handles routing, config, agent/module loading
#
import json
import threading
import sys
from halmodule import HalModule
from halagent import HalAgent
from loader import Loader
from queue import Queue,Empty

# Avoid appending "." if it i
if "." not in sys.path:
	sys.path.append(".")
import logging

class Halibot():

	config = {}
	agents = {}
	modules = {}
	queue = None

	thread = None
	running = False
	rld = False

	log = None
	
	def __init__(self):
		self.queue = Queue()
		self.log = logging.getLogger(self.__class__.__name__)

	# Start the Hal instance
	def start(self, block=True):
		self.running = True
		self._load_config()
		self._instantiate_agents()
		self._instantiate_modules()

	def shutdown(self):
		self.log.info("Shutting down halibot...");

		for m in self.modules.values():
			m.shutdown()
		for a in self.agents.values():
			a.shutdown()

		self.log.info("Halibot shutdown. Threads left: " + str(threading.active_count()))

	def _load_config(self):
		with open("config.json","r") as f:
			self.config = json.loads(f.read())

			self.agent_loader = Loader(self.config["agent-path"], HalAgent)
			self.module_loader = Loader(self.config["module-path"], HalModule)

	def _instantiate_agents(self):
		inst = self.config["agent-instances"]

		for k in inst.keys():
			# TODO include directive

			conf = inst[k]

			obj = self.agent_loader.get(conf["of"])

			self.agents[k] = obj(self, conf)
			self.agents[k].name = k
			self.agents[k].init()
			self.log.info("Instantiated agent '" + k + "'")

	def _instantiate_modules(self):
		inst = self.config["module-instances"]

		for k in inst.keys():
			# TODO include directive

			conf = inst[k]

			obj = self.module_loader.get(conf["of"])

			self.modules[k] = obj(self, conf)
			self.modules[k].name = k
			self.modules[k].init()
			self.log.info("Instantiated module '" + k + "'")

	def get_object(self, name):
		# TODO priority?
		if name in self.modules: return self.modules[name]
		if name in self.agents: return self.agents[name]
		return None

