# Calendar versioning

Use `YY.M.D.N`, for example `26.11.3.1`. The year has two digits; month and
day have no leading zeros; together they represent a valid date in 2000–2099.
`N` is a positive integer without leading zeros, starts at 1 each day, and increases for further releases that day.
The date is determined in `Europe/Moscow`; GitHub tags retain the `v` prefix.

After fetching public tags, `python3 scripts/prepare_release.py --next-version`
selects today's next number. Historical semantic-version releases remain
immutable and do not participate in the daily sequence. Do not ask the owner
to classify the change or confirm the computed version.

An explicit owner-supplied version takes precedence when it has a valid date,
is newer than the latest public release, and has no public tag or GitHub Release.
Do not silently replace an invalid or already published number: report the
conflict and resolve only that decision. If midnight passes before publication,
keep an explicitly selected date; for an automatically selected version,
recompute it before committing and align the changelog date.

The number identifies a release date and sequence, not compatibility. Describe
incompatible behavior and migration steps under Breaking changes and Install /
update. Both plugin manifests, the changelog heading, and the release tag use
the same calendar number. Never change an existing published version or tag.
