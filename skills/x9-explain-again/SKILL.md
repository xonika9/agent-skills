---
name: x9-explain-again
description: Use only when the user explicitly says they did not understand the immediately previous substantive assistant answer in this thread, for example «не понял» or «объясни иначе/проще», even when the specific unclear fragment cannot yet be identified. Do not use for a new standalone request such as «объясни X», for explaining an article or source, for a durable visual teaching artifact, a visual scheme, or when no previous substantive answer is accessible.
---

# Explain again

Repair understanding of one fragment of the immediately previous substantive assistant answer. This is a model-invoked skill in Claude Code and Codex; `portable` means structural compatibility only, not verified invocation behavior.

## Trigger boundary

Use this skill only when the user's message is explicit confusion about the immediately preceding substantive answer in the same thread. That answer is an assistant response to the user, excluding tool output, status updates, system messages, and imported older chats.

Do not treat a general request to explain a topic as a reference to a prior answer. Explaining a provided article or source remains a source-explanation task. Creating a durable visual teaching artifact belongs to `ce-explain`; creating a visual scheme belongs to `x9-diagrams`.

## Response

Identify the specific claim, conclusion, example, or step that is unclear. Add only the context needed to make that fragment understandable, then use a different explanatory method: an analogy, a concrete example, a causal breakdown, or simpler words. Include a tiny example only when it resolves the confusion.

Do not merely shorten or repeat the earlier wording. Do not create files, invoke `ce-explain` or `x9-diagrams` automatically, or start an autonomous loop. If the user still does not understand, one more bounded explanation is allowed; each new request still needs a clear referent.

When the unclear referent cannot be determined, ask one short question and do not invent context.

## Completion

Return either a concise explanation that addresses the identified fragment through a different method, or one short clarifying question when the fragment is not identifiable.
