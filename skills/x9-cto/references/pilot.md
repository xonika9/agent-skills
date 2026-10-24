# Pilot

A standing CTO run that keeps the repository's work moving without the owner:
it launches ready work, integrates finished work, and reports.

## Start

- Load the pilot owner named by the repository's AGENTS.md CTO block; it owns
  what may be launched, what counts as accepted, and when `main` may be pushed.
  Without one, report pilot as unavailable here and stop.
- Delete the scheduled tasks of an earlier pilot run in this repository, so
  only one pilot runs.
- Create two scheduled tasks bound to this chat: a tick every 30 minutes and
  a report at 09:00 local. Their prompts name the tick or the report
  and point here; they list no chats or cards, because state lives on the
  repository's board.
- Run the first tick now.

## Tick

- Read the end of every chat working on the started work the repository
  lists, including chats an earlier run launched; the start is stale.
  Delegate this collection to a fact-extraction worker under the runtime's
  routing (in Claude Code, Sonnet at high): it returns a short digest per chat,
  check and branch, with the commits, report paths and quoted lines the
  decisions rest on. This chat keeps integration, launches, pushes and owner
  questions, and checks each decisive fact against primary evidence.
- Integrate finished work under the repository's acceptance rules. Answer an
  executor's question when canon settles it; otherwise hold it for the report.
- Launch what the repository rules allow and record each launch where the
  repository keeps current state.
- A tick with nothing to do sends the owner nothing.

## Report

At 09:00 and on `report`: what finished since the last report, what runs and
what each waits for, spend, and the owner's open questions.

## Stop

Delete this run's scheduled tasks, confirm with the task list, leave launched
chats running, and name them.

## Boundaries

- Deploy and other owner-reserved actions wait for the owner's word.
- This chat keeps its model; workers follow the global runtime routing.
- In T3 Code, a chat waiting on a background check stays snoozed: marking it
  done drops its completion notice and later its background process.
