# Halibot Message Format

Internally, Halibot functions by translating messages from various protocols into a generic format.
These translated messages are then handed to the modules.
Thanks to the protocol-agnostic format, modules do not need to know anything about how these modules were received.
Therefore, a module that works in an IRC room should also work in XMPP.

# The Specification

Messages are received as an object that works like a javascript-like dictionary, either `msg.body` or `msg["body"]` is acceptable for accessing.
The following are top-level attributes:

 - `body`: The data being sent. In most cases, this is the text of the message.
 - `type`: Type of message, determines what may be in `body`. See `MessageFormat.md` for more info.
 - `author`: A short name for who sent the message.
 - `identity`: A string that uniquely identifies a user.
 - `origin`: Where this message originated from.
 - `target`: Where this message is intended to go.
 - `misc`: Unspecified, miscellaneous data. Typically agent-specific.

## Body (*string*)

The body of the message is simply the data that is being passed along.
See the **type** section below for what can be expected in this section.
This will always be a `str` object, and can be empty (`""`).

## Type (*string*)

The type of message should be set to reflect the kind of message being passed along.
The valid types of messages are defined more in depth in `MessageFormat.md`.

Most messages are use the type `simple`, which are for general chatter (e.g. plaintext messages sent to/from a channel or user).

## Author (*string*)

The `author` field is a short, sensible name to address the sender of a message by.
This is typically the nickname of a user.
This should *not* be a fully qualified user name if possible.
Using XMPP as an example, the `author` for the JID `foo@bar.baz.server.com` should just be something like `foo`.
This string should never be empty.
Cases where an author is not specified (like server messages) are to be documented in the agent protocol specifications.

## Identity (*string*)

Unlike `author`, this is a field that is *not* designed to fit into conversation.
Instead, this field carries uniquely identifying information about the `author`.
This should be used by modules for permissions verification, per-user behavior, and so on **instead** of `author`.
As `author` may be a changeable nickname, this provides a handle to a user that is static.
Using XMPP as an example again, the nickname in a MUC may be `foobar`, but the `msg.identity` is still `foo@bar.baz.server.com`.
Unlike `author`, however, this may be an empty string (`""`), as some protocols support anonymous users (e.g. IRC).
The permissions system uses `msg.identity` under the hood *by design*, to prevent spoofing via nickname change.

## Origin (*string*)
## Target (*string*)
## Misc (*dict*)
