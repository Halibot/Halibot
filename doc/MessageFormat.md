# Halibot Message Format

Internally, Halibot functions by translating messages from various protocols into a generic format.
These translated messages are then handed to the modules.
Thanks to the protocol-agnostic format, modules do not need to know anything about how these modules were received.
Therefore, a module that works in an IRC room should also work in XMPP.

# The Specification

Messages are received as an object that works like a javascript-like dictionary, either `msg.body` or `msg["body"]` is acceptable for accessing.
The following are top-level attributes:

 - `body`: The data being sent. In most cases, this is the text of the message.
 - `type`: Type of message, determines what may be in `body`.
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
The valid types of messages are:

| Type String | Description                         | What is in `body` |
| ----------- | ----------------------------------- | ----------------- |
| `simple`    | Plain text message sent from a user | Plain text        |

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

## Target (*string*)

`target` and its sibling `origin` are two fields used to manage the routing of a message.
`target` specifies where a message is intended, and is read by the internal message passing logic to determine where it should go.
Both `target` and `origin` use a string format called "Resource Identifiers", or RI for short.
Since they both use the same format, they can be interchanged easily to form a "reply".
These RIs serve as a way to uniquely identify a particular pathway of communication.

Resource Identifiers is a string containing substrings joined by a `"/"`.
Each substring should contain some information for the routing of the message, most commonly the name of an object instance.
When reading a resource identifier, the leftmost (first) string should be considered the top-level resource, or the first in the route.
Likewise, the rightmost (last) string is considered the end of the route, either the originating source or end goal.
When sending messages, Halibot only considers the leftmost string for sending a message, which it interprets as an object instance name.
It is up to each receiving object in the route to continue the chain.

To explain what RIs look like and how they are used, consider the following example.
An IRC agent sends messages to a Quote module.
The messages generated in the IRC agent would set `msg.target = "quote"`, and `msg.origin = "irc/##foobar"`.
Halibot will then route the message to the Quote module, which will handle the message.

Now, if the Quote module wants to respond back, all it needs to do is flip `.target` and `.origin`, and it is ready to go
(Note, this is handled by the `.reply()` method on HalObjects).
However, the keen eyed may have noticed that the RI from the IRC agent looks a bit different.
In reality, the IRC agent didn't just decide to message the Quote module out of its own free will, a channel message from ##foobar initiated the action.
And so, this RI can be read as `"irc"` contains a route to `"##foobar"`, because what Quote really wants to reply to is the channel.
Thus, the reply is set to the IRC agent, who then ultimately routes the content to `##foobar`.

## Origin (*string*)

See `target` above. Similar concept, specifies the source of a message

## Misc (*dict*)

The `misc` field is an option dictionary for any extra information that should be attached to a message, but isn't supported by any particular Halibot protocol.
As this is a freeform field, it is 100% up to agents and modules to even consider anything in here, since there is no standard.
Any usage of this field by an object should be loudly documented by the object.
