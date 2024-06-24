# Halibot Message Types

While most Halibot activity is generally simple chatter between agents and modules, there are other message types reserved for other functions.
The most common type is the obviously named `simple`, which indicates the body field contains plain text that an agent or module should react to.
An example of another type of message is a `status` message, which could be used for say, indicating a user has joined a channel.
Message types can also be further refined with a subtype.
Using the previous example, the status subtype would be `status:join`.

## How are types used?

This is actually a bit of trick question.
Types for the most part are actually *ignored* by Halibot core.
So why bother defining them?
Types exist so that agents and modules can have a platform to hint at how the message should be interpreted.
As mentioned before, in most cases, messages are used to send a protocol's chat messages over to modules for them to handle.
However, this does not provide a platform for an agent to relay *other* useful metadata, like a user joining a channel.
Types thus provide a standardized way to further translate protocol-specific information into a generic platform for modules to react to.

Types can also be used as a grouping of subtypes.
Not all protocols are designed the same, some provide more fine detail.
Therefore, types are also flexible via use of subtypes, to also provide more detail.
In slightly more simple terms, consider the type to be a top-level category, and a subtype to be more specific.
See the table below for more examples.

## HalObject API

A Message type (`msg.type`) is defined by a string of the form `<type>` or `<type>:<subtype>`.
Subtypes are optional and not required, however it must be noted that inclusion or omission of a subtype may cause the message to be handled differently than expected.
Refer to the table below to ensure that the correct message type and/or subtype is used.

While Halibot core does not handle messages any different by type, HalObject instead uses a "top-level" filter based on type.
That is, messages of a different supertype can be sent to different receive handlers.
By default, if no specialized receivers are defined, all messages regardless of type are send to `.receive()`.
A notable exception is the `HalModule` class, which by default defines all the type receivers (except `simple`) as no-ops, to passively ignore unhandled types.

To clear things up, here is a quick diagram and example:
```python
'''
msg.type = simple
  Agent -> dispatch() -> Module -> .receive_simple() -> .receive()
msg.type = status:join
  Agent -> dispatch() -> Module -> .receive_status()
'''

class Example(HalModule):

	# Receiver of msg.type = status messages ONLY
	def receive_status(self, msg):
		# Respond to a user entering the channel
		if msg.type.subtype == "join":
			self.reply(msg, body="Hello, " + msg.author, type="simple")
		# Respond to a user leaving the channel
		elif msg.type.subtype in ("part","quit"):
			self.reply(msg, body="Goodbye, " + msg.author, type="simple")
		# Agent or protocol doesn't specify what type of status, so have a default catch-all
		else:
			self.reply(msg, body="{} did something.", type="simple")

	# Default receiver of all messages
	def receive(self, msg):
		if msg.body.lower() in ("hi", "hello")
			self.reply(msg, body="Hello, " + msg.author)

```

**NOTE:** `msg.type` will always contain the full string `"<type>:subtype"`.
The attribute `msg.type.subtype` exists for convenience to either return the string of the subtype, or the empty string if no subtype is set.

## TL;DR

As a rule: `msg.status` defines how to interpret what is in the `msg.body`.
Furthermore, `msg.status` also defines what handlers are called when this message is received in the HalObject API.
It is up to the modules and agents to correctly communicate the data within `msg.body` -- there is no validation done via Halibot core.
Thus, if `msg.status`'s type indicates that `msg.body` should be an integer, both sides must do their own enforcement.

## Table of Types

| Type String   | Description                             | What is in `msg.body` |
| ------------- | --------------------------------------- | --------------------- |
| `simple`      | Plain text message sent to/from a user  | Plain text            |
| `status`      | A user changed connection status        | undefined             |
| `status:join` | A user joined the channel               | undefined             |
| `status:part` | A user left the channel                 | undefined             |
| `status:quit` | A user disconnected                     | undefined             |
