#!/usr/bin/env python3

import halibot
import json
import logging
import sys
import os
import shutil
import tarfile
import urllib.request
import io
import argparse
import code

def h_init(args):
	confpath = os.path.join(args.path, "config.json")
	pkgpath  = os.path.join(args.path, "packages")
	permpath = os.path.join(args.path, "permissions.json")

	if not os.path.exists(args.path):
		os.mkdir(args.path)
	else:  # Dir does exist, ensure clear
		if os.listdir(args.path):
			r = input("Directory not empty, are you sure you want to init here? [y/N]: ")
			if not r.lower() in ("y", "yes", "yolo"):
				return

	if os.path.exists(confpath):
		r = input("A 'config.json' already exists, overwrite with new? [y/N]: ")
		if not r.lower() in ("y", "yes", "yolo"):
			return

	config = {
		"package-path": [
			"packages"
		],
		"repos": ["https://halibot.fish:4842"],
		"agent-instances": {},
		"module-instances": {},
		"filter-instances": {},
		"use-auth": False
	}

	with open(confpath, "w") as f:
		f.write(json.dumps(config, sort_keys=True, indent=4))

	if not os.path.exists(permpath):
		with open(permpath, "w") as f:
			f.write(json.dumps([], sort_keys=True, indent=4))

	if not os.path.exists(pkgpath):
		os.mkdir(pkgpath)
		print("Created '{}'".format(pkgpath))

	print("Halibot instance has been initialized!")
	print("\nUse '{} run' to run the instance, or edit 'config.json' to add module/agent instances".format(sys.argv[0]))

def h_run(args):
	# Maybe do the config loading here?
	if not os.path.exists("config.json"):
		print("Failed to start: No halibot configuration found in the current directory!")
		return

	bot = halibot.Halibot()
	bot._load_config()

	logfile = None
	loglevel = logging.DEBUG
	loglevel_str = "DEBUG"
	loglevels = {
		"CRITICAL": logging.CRITICAL,
		"ERROR": logging.ERROR,
		"WARNING": logging.WARNING,
		"INFO": logging.INFO,
		"DEBUG": logging.DEBUG,
		"NOTSET": logging.NOTSET
	}

	# Set log level if argument is provided
	if args.log_level:
		loglevel_str = args.log_level
	elif "log-level" in bot.config:
		loglevel_str = bot.config["log-level"]

	# Error check log level string
	if loglevel_str not in loglevels:
		print("Log level '{}' invalid.".format(loglevel_str))
		return
	else:
		loglevel = loglevels[loglevel_str]

	# Set log file if argument is provided
	if args.log_file:
		logfile = args.log_file
	elif "log-file" in bot.config:
		logfile = bot.config["log-file"]

	logging.basicConfig(filename=logfile, level=loglevel)

	# Print used configuration
	if logfile:
		print("Logs at '{}' with log level '{}'".format(logfile, loglevel_str))
	else:
		print("Log level '{}'".format(loglevel_str))

	# Start the bot, block if non-interactive, otherwise let the shell handle the blocking
	bot.start(block=not args.interactive)

	if args.interactive:
		local = {
			"bot": bot,
			"halibot": halibot,
		}
		code.interact(banner="Halibot welcomes you!", local=local)
		bot.shutdown()
		print("Halibot bides you farewell.")

def h_fetch(args):
	# In order to access the config easily
	bot = halibot.Halibot()
	bot._load_config()

	# Error checking
	if not "repos" in bot.config:
		print("There are no repos specified in the config.json.")
		print("I have nothing to fetch from!")
		return

	# Try to fetch each requested package
	for name in args.packages:
		# Install to the first package path by default
		dst = os.path.join(bot.config["package-path"][0], name)

		success = False
		for r in bot.config["repos"]:
			src = r + "/fetch/" + name
			try:
				print("Trying to fetch package from '{}'...".format(r))
				bio = io.BytesIO(urllib.request.urlopen(src).read())
				tar = tarfile.open(mode="r:*", fileobj=bio)
				os.mkdir(dst)
				tar.extractall(dst)

				print("\033[92mSuccessfully fetched '{}' into '{}'.\033[0m".format(name, dst))
				success = True
				break
			except Exception as e:
				print(e)

		if not success:
			print("\033[91mFailed to fetch '{}'!\033[0m".format(name))

def h_search(args):
	# In order to access the config easily
	bot = halibot.Halibot()
	bot._load_config()

	# Error checking
	if not "repos" in bot.config:
		print("There are no repos specified in the config.json.")
		print("I have nowhere to search!")
		return

	# Query all listed repositories
	results = {}
	for r in bot.config["repos"]:
		url = r + "/search/"
		if args.term != None:
			url += args.term

		data = urllib.request.urlopen(url).read().decode('utf-8')
		subres = json.loads(data)
		results = dict(list(subres.items()) + list(results.items()))

	# Output results
	sorted_keys = list(results.keys())
	sorted_keys.sort()
	for name in sorted_keys:
		print(name, "-", results[name]['description'])


def h_unfetch(args):
	# In order to access the config easily
	bot = halibot.Halibot()
	bot._load_config()

	# Remove each requested package
	for name in args.packages:
		# Install to the first package path by default
		success = False
		for pkgpath in bot.config["package-path"]:
			path = os.path.join(pkgpath, name)
			if os.path.exists(path):
				shutil.rmtree(path)
				print("Removed '{}' installed to '{}'.".format(name, path))
				success = True

		if not success:
			print("Could not find package '{}'".format(name))

def h_info(args):
	bot = halibot.Halibot()
	bot._load_config()

	if args.object_name:
		# Show configuration of specific object

		conf = bot.config.get("agent-instances", {}).get(args.object_name)
		conf = bot.config.get("module-instances", {}).get(args.object_name) if not conf else conf
		if not conf:
			print("No such agent or module")
			return

		print("\n{args.object_name}: ({conf['of']})".format(args=args, conf=conf))
		for k in conf:
			if k != "of":
				print("  {k}: {conf[k]}".format(k=k, conf=conf))
	else:
		# Show all configured objects
		if len(bot.config.get("agent-instances", {})) > 0:
			print("\nConfigured agents:")
			agents = bot.config.get("agent-instances")
			for name in agents:
				print("  {name} ({agents[name]['of']})".format(name=name, agents=agents))

		if len(bot.config.get("module-instances", {})) > 0:
			print("\nConfigured modules:")
			modules = bot.config.get("module-instances")
			for name in modules:
				print("  {name} ({modules[name]['of']})".format(name=name, modules=modules))

	print("")


def h_list_packages(args):
	bot = halibot.Halibot()
	bot._load_config()

	pkgs = []
	for path in bot.config.get("package-path"):
		pkgs = pkgs + os.listdir(path)
	pkgs.sort()

	print("\nAvailable packages:")
	for p in pkgs:
		print("  {}".format(p))
	print("")

def h_add(args):
	# In order to access the config easily
	bot = halibot.Halibot()
	bot._load_config()

	for clspath in args.things:
		# Validate that it is actually an object
		split = clspath.split(":")
		if len(split) > 2:
			print("Invalid class path '{}', expected no more than 1 colon (:).".format(clspath))
			continue

		pkg = bot.get_package(split[0])
		if pkg == None:
			print("Cannot find package '{}'.".format(split[0]))
			continue

		if len(split) == 1:
			if not hasattr(pkg, "Default"):
				print("Package '{}' has no default class, must specify the class to add explicitly.".format(split[0]))
				continue
			cls = pkg.Default
			clspath += ":Default"
		else:
			cls = getattr(pkg, split[1], None)
			if cls == None:
				print("Class '{}' does not exist on package '{}'.".format(split[1], split[0]))
				continue

		if args.destkey:
			destkey = args.destkey
		else:
			if issubclass(cls, halibot.HalModule):
				destkey = "module-instances"
			elif issubclass(cls, halibot.HalAgent):
				destkey = "agent-instances"
			else:
				print("Cannot determine if '{}' is a module or agent, use '-m' or '-a'.")
				continue

		#(name, conf) = cls.configure({ 'of': clspath })
		name = input("Enter instance name: ")
		# TODO: Consider putting this logic into a lib function?
		cfgr = cls.Configurer()
		tmpcfg = {}
		for key,opt in cfgr.options.items():
			if opt.depends and not tmpcfg.get(opt.depends, False):
				continue # Skip items that are dependent on a false-booleaned parameter

			tmpcfg[key] = opt.ask(input)

		tmpcfg["of"] = clspath

		if name in bot.config["agent-instances"] or name in bot.config["module-instances"]:
			print("Instance name '{}' is already in configuration, please choose a different instance name".format(name))
			return

		bot.config[destkey][name] = tmpcfg

	bot._write_config()

def h_rm(args):
	# In order to access the config easily
	bot = halibot.Halibot()
	bot._load_config()

	for name in args.names:
		if name in bot.config["agent-instances"]:
			bot.config["agent-instances"].pop(name)
		elif name in bot.config["module-instances"]:
			bot.config["module-instances"].pop(name)
		else:
			print("No such object '{}'".format(name))
			continue
		print("Removed '{}'.".format(name))

	bot._write_config()

def h_config(args):
	# In order to access the config easily
	bot = halibot.Halibot()
	bot._load_config()

	if args.name in bot.config["agent-instances"]:
		destkey = "agent-instances"
	elif args.name in bot.config["module-instances"]:
		destkey = "module-instances"
	else:
		print('No such module or agent exists.')
		return
	pkgconf = bot.config[destkey][args.name]

	# Show or edit the config?
	if args.show:
		# Only a single key?
		if args.key != None:
			print(pkgconf[args.key])
		else:
			for k in pkgconf:
				print(k, "=", pkgconf[k])
	else:
		# Reconfigure the package
		if args.key != None:
			if args.value == None:
				print("You must specify a value with -v.")
				return

			# Detect the type to set
			if args.type:
				ty = args.type
			else:
				if args.key in pkgconf:
					typecls = type(pkgconf[args.key])
					if   typecls == int:   ty = "number"
					elif typecls == float: ty = "number"
					elif typecls == str:   ty = "string"
					elif typecls == bool:  ty = "boolean"
					else:
						print("The type of the key '" + args.key + "' is not a settable type.")
						return
				else:
					print("That key does not exist, you must specify the type with -t.")

			# Get the value
			if ty == "string": value = args.value
			if ty == "number": value = float(args.value)
			if ty == "boolean":
				if   args.value.lower() == 'true': value = True
				elif args.value.lower() == 'false': value = False
				else:
					print("Invalid boolean value, specify 'true' or 'false'.")
					return

			pkgconf[args.key] = value
		else:
			if not "of" in pkgconf:
				print("Corrupt config, package has no 'of' key.")
				return

			split = pkgconf["of"].split(":")
			if len(split) != 2:
				print("Corrupt config, malformed 'of' value.");
				return

			pkg = bot.get_package(split[0])
			if pkg == None:
				print("The package '" + split[0] + "' does not exist so it cannot be configured.")
				return

			cls = getattr(pkg, split[1], None)
			if not cls:
				print("The package '" + split[0] + "' has no module or agent named '" + split[1] + "'.")
				return


			# TODO: Seriously consider putting this logic into a lib function?
			cfgr = cls.Configurer()
			tmpcfg = pkgconf
			for key, opt in cfgr.options.items():
				if opt.depends and not tmpcfg.get(opt.depends, False):
					continue # Skip items that are dependent on a false-booleaned parameter

				tmpcfg[key] = opt.ask(input)

			#(name, conf) = cls.configure(pkgconf, name=args.name)
			bot.config[destkey][args.name] = tmpcfg

		bot._write_config()

if __name__ == "__main__":
	subcmds = {
		"init": h_init,
		"run": h_run,
		"fetch": h_fetch,
		"unfetch": h_unfetch,
		"add": h_add,
		"rm": h_rm,
		"packages": h_list_packages,
		"search": h_search,
		"config": h_config,
		"info": h_info,
	}

	# Setup argument parsing
	parser = argparse.ArgumentParser(description="The world's greatest saltwater chat bot!")
	parser.add_argument("-d", "--directory", help="Use the specified directory rather than the current.")

	sub = parser.add_subparsers(title="commands", dest="cmd", metavar="COMMAND")

	init = sub.add_parser("init", help="initialize a new local halibot instance")
	init.add_argument("path", help="directory path to initialize the halibot instance in", nargs="?", default=".")

	run = sub.add_parser("run", help="run the local halibot instance")
	run.add_argument("-i", "--interactive", help="enter a python shell after starting halibot", action="store_true", required=False)
	run.add_argument("-f", "--log-file", help="file to output logs to, none by default")
	run.add_argument("-l", "--log-level", help="level of logs, DEBUG by default")

	fetch = sub.add_parser("fetch", help="fetch remote packages")
	fetch.add_argument("packages", help="name of package to fetch", nargs="+", metavar="package")

	unfetch = sub.add_parser("unfetch", help="as if you never fetched them at all")
	unfetch.add_argument("packages", help="name of package to unfetch", nargs="+", metavar="package")

	add = sub.add_parser("add", help="add agents or modules to the local halibot instance")
	add.add_argument("things", help="path to class to add", nargs="+", metavar="class")
	addtype = add.add_mutually_exclusive_group()
	addtype.add_argument("-a", "--agent", dest="destkey", action="store_const", const="agent-instances", help="add instances as agents")
	addtype.add_argument("-m", "--module", dest="destkey", action="store_const", const="module-instances", help="add instances as modules")

	rm = sub.add_parser("rm", help="remove agents or modules from the local halibot instance")
	rm.add_argument("names", help="names of agents or modules to remove", nargs="+", metavar="name")

	list_packages = sub.add_parser("packages", help="list all available packages")

	search = sub.add_parser("search", help="search for packages")
	search.add_argument("term", help="what to search for", nargs="?", metavar="term")

	config_cmd = sub.add_parser("config", help="configure or reconfigure a module or agent")
	config_cmd.add_argument("name", help="name of the module or agent to show or reconfigure")
	config_cmd.add_argument("-s", "--show", action="store_true", help="show the configuration rather than set it", required=False)
	config_cmd.add_argument("-k", "--key", help="key to set or key to display with -s", required=False)
	config_cmd.add_argument("-v", "--value", help="value to set key to", required=False)
	config_cmd.add_argument("-t", "--type", choices=["string", "number", "boolean"], help="the type used while setting a config value with -k. If not given, it uses the type of the existing value")

	info = sub.add_parser("info", help="show configuration information")
	info.add_argument("object_name", nargs="?", help="name of module or adent to query about")

	args = parser.parse_args()

	if args.directory:
		os.chdir(args.directory)

	# Try to run a subcommand
	if args.cmd != None:
		subcmds[args.cmd](args)
	else:
		parser.print_help()
