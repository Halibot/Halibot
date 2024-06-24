from collections import OrderedDict
#get_input = input

class Option():
	def __init__(self, key, prompt=None, default=None, depends=None):
		self.key = key
		self.prompt = prompt if prompt != None else key
		self.default = default
		self.depends = depends

	def ask(self, get_input):
		prompt = self.prompt
		if self.default != None:
			prompt += ' [' + str(self.default) + ']'
		prompt += ': '

		while True:
			v = get_input(prompt)
			if v == '': return self.default
			try:
				return self.validate(v)
			except ValueError:
				continue

		return "This shouldn't be run"

	# To be implemented by subclassers
	def validate(self, value):
		return value

# Builtin option classes
class StringOption(Option):
	pass

class IntOption(Option):
	def validate(self, value):
		return int(value)

class NumberOption(Option):
	def validate(self, value):
		return float(value)

class BooleanOption(Option):
	def validate(self, value):
		if isinstance(value, str):
			if value.lower() == 'true':  return True
			if value.lower() == 'false': return False
			raise ValueError()
		return value

Option.String = StringOption
Option.Int = IntOption
Option.Number = NumberOption
Option.Boolean = BooleanOption

class HalConfigurer():

	def __init__(self, options={}):
		self.options = OrderedDict(options)
		self.configure() # fill out options dict

	# Build a dictionary mapping config key to the validator
	def option(self, option_type, key, **kwargs):
		self.options[key] = option_type(key, **kwargs)

	def optionString(self, key, **kwargs):
		self.option(Option.String, key, **kwargs)

	def optionInt(self, key, **kwargs):
		self.option(Option.Int, key, **kwargs)

	def optionNumber(self, key, **kwargs):
		self.option(Option.Number, key, **kwargs)

	def optionBoolean(self, key, **kwargs):
		self.option(Option.Boolean, key, **kwargs)

	# Implemented by module, call to generate configurer
	def configure(self):
		pass # pragma: no cover

	# Validate a complete config blob. Use for initial load from config file
	#  config (dict): blob to check
	#  fill_default (bool): will throw exception if there are missing keys, otherwise fills with defaults
	# returns a config blob on success (with defaults if selected), throws exception on problem
	def validate_config(self, config, fill_default=True):
		ret = {}
		missing = []
		for key, validator in self.options.items():
			tmp = config.get(key)

			# Ensure the key exists, and if we aren't taking defaults, ensure we report
			if not tmp and not fill_default:
				missing.append(key)
				continue
			elif not tmp:
				ret[key] = validator.default
				continue

			# Propogate ValueError if there is one
			ret[key] = validator.validate(tmp)

		if missing and not fill_default:
			str = "Missing key" + ("s" if len(missing) > 1 else "") + ": " + ", ".join(missing)
			raise KeyError(str)

	# Validate an individual key/value pair. Probably used for runtime changes/configurerers.
	def validate_key(self, key, value):
		validator = self.options.get(key)
		if not validator:
			return KeyError("No such config option")
		return validator.validate(value)
