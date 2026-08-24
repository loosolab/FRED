# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.1] - 2026-08-24

### Fixed

- The `/searchWhitelist` advanced-search autocomplete now replaces a
  whitelist's custom `delimiter` (e.g. the `organism` whitelist's `,`) with
  a whitespace before matching against the typed search string, so typing a
  space where the delimiter is displayed (e.g. `Homo sapiens 9606` instead
  of `Homo sapiens, 9606`) no longer prevents a match.

## [3.0.0] - 2026-08-17

### Breaking

- The `organism` whitelist (and its dependents `gene`, `abbrev/gene_name`,
  `abbrev/organism_name`) was migrated from informal/legacy names (e.g.
  `human`, or the intermediate `Homo_sapiens`) to the current canonical form
  (e.g. `Homo sapiens`, split via the whitelist's `delimiter` field).
  Metadata files generated before this migration store the old
  `organism_name` value, which no longer matches the current whitelist.
  Reading such files now raises a `MetadataVersionError` until they are
  migrated (see below).

### Added

- New `fred migrate <version>` subcommand with a pluggable migration
  framework (`fred/migrations/`). Each migration can define its own
  extra CLI flags via `fred.migrations.base.Migration.add_arguments`.
- `migrate 3.0.0`: updates `organism_name` (and the matching `taxonomy_id`)
  in existing metadata files to the new canonical whitelist values.
  An optional `--regenerate-sample-names` flag fully recomputes each
  sample's `technical_replicates.sample_name` list from the current
  template instead of patching the embedded organism token in place;
  samples whose recomputed count doesn't match the stored one are left
  untouched and flagged for manual review. `condition_name` and
  `technical_replicates.filenames` are never touched.
- `--version` flag to print the installed FRED version.
- Authentication support (`name`/`token`) for cloning private whitelist
  repositories over HTTP(S), configurable via `config.yaml`.
- New structure keys: `culture_type` and `passage_number` under cell
  culture information, and a new `library_preparation` factor (with
  `preparation_status`/`preparation_type`) describing additional
  sequencing library preparation steps (e.g. rRNA depletion, ligation).
- Support for an alternative delimiter when splitting/joining grouped
  whitelist header values, configurable per whitelist.

### Fixed

- Heatmap organism images are now looked up using the whitelist's
  space-separated organism name (e.g. `Homo sapiens` → `Homo_sapiens.png`)
  instead of the raw, no-longer-matching organism string.
- Value/unit factors with only a single value are no longer incorrectly
  collapsed during autogeneration.
- YAML files written under a non-UTF-8 locale (containing raw cp1252/
  Latin-1 bytes, e.g. `µ` or `ö`) are now read correctly with a
  cp1252 fallback.
- Delimiter information is now correctly propagated through factor and
  condition parsing for grouped whitelists.

### Changed

- Docker image installs FRED via `pip install ./metadata-organizer` and
  runs the `fred` entrypoint instead of invoking `metaTools.py` directly
  with manually pinned dependencies.
- Various internal refactors to whitelist input/parsing functions.

[3.0.1]: https://gitlab.gwdg.de/loosolab/software/metadata-organizer/-/compare/v3.0.0...v3.0.1
[3.0.0]: https://gitlab.gwdg.de/loosolab/software/metadata-organizer/-/compare/v2.0.3...v3.0.0
