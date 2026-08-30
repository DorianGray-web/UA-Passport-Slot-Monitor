# User research working rules

## Scope

These instructions apply to the research/user-surveys/ research boundary.
They supplement the repository-root AGENTS.md. More specific instructions in a
descendant directory may narrow the writable scope for an implementation task.

## Research boundaries

- survey/ contains voluntary survey specifications, implementation adapters,
  and sanitized survey results.
- social-listening/ contains anonymized observations derived from public
  comments under its separate methodology and schema.
- shared/ owns stable taxonomy identifiers and shared schemas.
- synthesis/ compares independently processed source aggregates.
- Never write social-listening observations as survey responses or join
  individual records across the two sources.
- Comparative analysis belongs only in synthesis/ and must identify the source
  of every metric.

## Privacy and data handling

- Do not commit names, contact details, passport or appointment data, precise
  locations, IP addresses, User-Agent values, fingerprints, raw Google Sheets
  exports, raw survey responses, raw comments, profile links, secrets, API
  keys, or deployment URLs.
- Commit only reviewed, anonymized processed data and aggregate outputs.
- Treat free text as untrusted plain text. Do not publish raw or merely masked
  text in charts, summaries, examples, or downloadable data.
- Keep source-specific processed data, summaries, and charts inside their
  source directories.

## Identifiers and contracts

- Use stable immutable ASCII IDs instead of localized labels.
- Preserve the existing British spelling for survey research fields such as
  centre_id and centre_ids unless a versioned contract change replaces it.
- Canonical taxonomies in shared/taxonomy/ are the single owners of centres,
  problem categories, and notification channels.
- Do not copy enums into parallel handwritten registries.
- Preserve raw legacy values separately from normalized values and record the
  normalization version and migration status.
- Do not silently change question meaning, requiredness, enum semantics,
  analytical interpretation, schemas, or contract versions.

## Change discipline

- Read the applicable specification, taxonomy, schema, methodology, and
  descendant AGENTS.md before editing.
- Keep survey, social-listening, shared taxonomy/schema, and synthesis changes
  separately reviewable.
- Do not modify generated results or introduce raw data as part of a code or
  documentation task.
- Report conflicts between specifications, taxonomies, schemas, and
  implementation instead of fixing them implicitly.
- Run validation proportionate to the changed artifact and inspect the scoped
  diff before completion.
