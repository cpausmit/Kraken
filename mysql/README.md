# The Kraken production database (`Bambu`)

Kraken keeps all of its bookkeeping in a single database called **`Bambu`** -- the name
predates the rename of the framework from Bambu to Kraken. Five tables: `Datasets`,
`Blocks` and `Lfns` describe the **input** data; `Requests` and `Files` record what Kraken
has **produced** from it.

The authoritative schema is [`schema.sql`](schema.sql), read off the live server and
regenerated with [`dump-schema.sh`](dump-schema.sh). This file explains what the tables
mean; it does not repeat their definitions.

## Where it lives, and how to reach it

The server is **t3desk008.mit.edu**, MariaDB 11.8.8 -- *not* the machine the framework
itself runs on. Clients connect as the MySQL account `ssluser`, matched by host pattern
`t3%.mit.edu`.

Every script connects identically. `python/kdb.py` and each tool under `bin/` carry the
same line, with no `KRAKEN_*` variable involved:

```python
MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",
                read_default_group="mysql", db="Bambu")
```

Server, account and password therefore all come from the `[mysql]` group of
`~cmsprod/.my.cnf`. To query by hand, log in as `cmsprod` on `t3desk000.mit.edu` and run
`mysql Bambu` -- the client picks up that same group.

**`mysqldump` does not work here.** It reads the `[client]` and `[mysqldump]` groups, not
`[mysql]`, so it finds no host and falls back to a local socket that does not exist. Use
`dump-schema.sh`, which drives the `mysql` client.

Moving the server means editing that one config file. The database name and the path to
the config are hardcoded in all 21 connection sites and cannot be changed from outside the
code.

FiBS uses a separate database (`Fibs`) on the same server, documented with the FiBS
project. The two share only the `ssluser` account.

## Capacity: `BlockId` was widened on 2026-09-22

`Blocks.BlockId` and `Lfns.BlockId` were signed `mediumint`, ceiling 8,388,607, and had
reached 6,143,905 -- 73.2%, with about 2.24M ids left before block inserts would start
failing and cataloguing would stop. Both are now `int`, ceiling 2,147,483,647, which at any
plausible rate is the end of the matter. See
[MIGRATION-blockid.md](MIGRATION-blockid.md) for what was done and what it cost.

`Datasets.DatasetId` (9,398) and `Requests.RequestId` (22,049) are still `mediumint` with
the same 8,388,607 ceiling, but at 0.1% and 0.3% they are nowhere near it.

Still open: `Lfns.NEvents` and `Files.NEvents` are `mediumint`, so a file with more than
8.4M events is recorded wrong, silently. Row counts and counters here still have no
timestamp to measure growth against -- see the logging suggestion in the migration note.

## The tables

Sizes as of 2026-09-22.

| Table | Rows | Data | Index | Holds |
|---|---:|---:|---:|---|
| `Files` | 6,935,707 | 402 MB | 512 MB | one row per output file Kraken has produced |
| `Blocks` | 6,143,903 | 252 MB | 108 MB | input datasets subdivided into filesets |
| `Lfns` | 4,395,223 | 640 MB | 324 MB | the individual input files |
| `Requests` | 16,993 | 1 MB | 1 MB | one campaign (config/version/py) on one dataset |
| `Datasets` | 9,147 | 1 MB | 1 MB | the input datasets themselves |

All five are **MyISAM**, `latin1 / latin1_swedish_ci`. Two consequences:

- **No foreign keys.** MyISAM ignores them, so nothing stops an orphaned `Blocks` row
  pointing at a deleted dataset. Older documentation showed `references` clauses; they were
  never enforced and are not in the live schema.
- **No transactions.** A multi-table delete that fails halfway leaves the rest behind.

### `Datasets`

The most important high level unit. Either from DBS, or derived from locally produced
datafiles (Panda or bambu files). A dataset is addressed everywhere as
process + setup + tier, which is also its unique key.

Derived datasets carry their full history. A DBS dataset
`MET+Run2016B-03Feb2017_ver2-v2+MINIAOD` processed with configuration `pandaf` version
`003` becomes `pandaf=003=MET+Run2016B-03Feb2017_ver2-v2+MINIAOD`.

`bin/addDataset.py` inserts all six columns.

### `Blocks`

A dataset subdivided. In DBS the division is given; in a locally produced sample a block
corresponds to a **fileset** -- the bundle of files the catalog groups together for
processing. Files per fileset is set per dataset when the catalog is generated.

A fileset is a catalog **file** written by `bin/generateCatalogs.py`, not a table here.

This is the table with the key-ceiling problem above.

### `Lfns`

The smallest unit: the logical file name. Blocks contain a number of lfns; they resolve to
a location on disk once converted to the physical file name at the site in question.

No primary key -- `LfnId` (dataset + block + name) is the identity. Note `NEvents` is a
`mediumint`, so a file with more than 8.4M events cannot be recorded correctly.

### `Requests`

One campaign -- config + version + py -- applied to one dataset. `RequestNFilesDone` is the
progress counter the monitors read.

Two quirks. `RequestPy` is `varchar(33)`, an order of magnitude shorter than the other name
columns. And the unique key does **not** include `RequestPy`, so one dataset cannot carry
two requests of the same config/version differing only in the python parameter file.

### `Files`

One row per output file produced, and the table that "how far along is this request"
queries join against.

`SizeBytes` was added after the original schema. `bin/checkFile.py` inserts it with the
row; `bin/updateFileSizes.py` backfills rows that predate it. Its default is `0`, not `-1`
like the other counters, so **zero means "not measured yet", not "empty file"**.

## Access rights

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON `Bambu`.* TO `ssluser`@`t3%.mit.edu`;
GRANT SELECT, INSERT, UPDATE, DELETE ON `Fibs`.*  TO `ssluser`@`t3%.mit.edu`;
```

The host pattern covers every `t3*` machine, so any Tier-3 node holding the password has
full read and write on both databases.

Recreating the account, if it ever comes to that:

```sql
DROP USER 'ssluser'@'t3%.mit.edu';
CREATE USER 'ssluser'@'t3%.mit.edu' IDENTIFIED BY '<password>';
GRANT SELECT, INSERT, UPDATE, DELETE ON Bambu.* TO 'ssluser'@'t3%.mit.edu';
GRANT SELECT, INSERT, UPDATE, DELETE ON Fibs.*  TO 'ssluser'@'t3%.mit.edu';
```

A narrower per-host form (`'ssluser'@'t3serv019.mit.edu'`) and an older subnet form
(`'ssluser'@'18.77.0.%'` and `.1`, `.2`, with `select,insert` only) both appeared in
previous versions of this file. Neither is in place now; read the truth off the server with
`show grants for 'ssluser'@'t3%.mit.edu'`.

## Keeping this honest

Until 2026-09 the schema existed in no file anywhere -- only in a Redmine document, which
had drifted badly: it described a sixth table that no longer exists, `char(36)` columns
that are really `varchar(255)`, and a `varchar(333) not null` that is really a nullable
`varchar(60)`. Regenerate after any schema change:

```bash
ssh cmsprod@t3desk000.mit.edu
cd $KRAKEN_BASE/mysql && ./dump-schema.sh > schema.sql
```

and commit the diff. To widen `Blocks.BlockId` before it runs out, see
[MIGRATION-blockid.md](MIGRATION-blockid.md).
