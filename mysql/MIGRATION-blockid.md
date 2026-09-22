# Migration: widening `BlockId` from `mediumint` to `int`

**Status: proposed, not yet executed.**

## The problem

`Blocks.BlockId` is a signed `mediumint` and stops at **8,388,607**. As of 2026-09-22 the
counter is at **6,143,905** -- 73.2% used, 2,244,702 ids left. When it runs out every
block insert fails and cataloguing stops.

The counter and the row count differ by one, so essentially nothing has ever been deleted
and id consumption tracks row growth directly.

`Lfns.BlockId` is the same type and must be widened to match.

## The change

```sql
ALTER TABLE Lfns   MODIFY BlockId int NOT NULL;                   -- FIRST
ALTER TABLE Blocks MODIFY BlockId int NOT NULL AUTO_INCREMENT;    -- second
```

**Why `int` and not `unsigned mediumint`.** Unsigned only doubles the ceiling to 16.7M for
exactly the same outage: the same conversation again in roughly twenty years. `int` gives
2.1 billion -- 256x the headroom -- for one extra byte per row: ~6 MB on `Blocks`, ~4 MB on
`Lfns`, plus index growth, call it 40 MB against 2.3 GB total. `bigint` buys nothing more
that matters here.

**Why signed.** The rest of this schema uses `-1` sentinels; 2.1 billion is already
effectively unlimited for this table, so there is no reason to introduce a signedness
exception that code might trip over.

**Why `Lfns` first.** A wider column holds every existing value, and `int`/`mediumint`
comparisons work normally, so the half-migrated state is safe in that direction. The other
order leaves a window -- narrow at 6.1M, but free to avoid -- in which a new block could
take an id that `Lfns` cannot store.

## Privileges required -- `ssluser` cannot do this

The account every Kraken script uses holds only `SELECT, INSERT, UPDATE, DELETE` on
`Bambu`. Attempting any part of this migration with it fails immediately:

```
ERROR 1142 (42000): ALTER command denied to user 'ssluser'@'T3DESK000.MIT.EDU'
```

That covers the timing test too, which needs `CREATE` and `DROP` for its scratch copy.
**The migration must be run by an account with `ALTER`, `CREATE` and `DROP` on `Bambu`** --
i.e. the administrative account on the database server t3desk008.mit.edu. Either grant
those to `ssluser` temporarily for the window, or have whoever holds root on that server
run the statements.

## Before the maintenance window

1. **Time it on a copy.** The only way to know the length of the outage. MyISAM has no
   online DDL: the `ALTER` copies the table and rebuilds every index under a full table
   lock. `Lfns` is the expensive one (640 MB data + 324 MB index).

   ```sql
   CREATE TABLE Lfns_test LIKE Lfns;
   INSERT INTO Lfns_test SELECT * FROM Lfns;
   ALTER TABLE Lfns_test MODIFY BlockId int NOT NULL;   -- time this
   DROP TABLE Lfns_test;
   ```

   Expect minutes rather than hours, but measure rather than trust that.

2. **Check free space** on the server (t3desk008). The rebuild needs room for a full copy
   of the largest table, roughly 1 GB. *Checked 2026-09-22: 394 GB free on `/`, ample.*

3. **Back up `Blocks` and `Lfns`.** Note `mysqldump` cannot connect with the current
   `~cmsprod/.my.cnf` (see [README.md](README.md)); either add a `[client]` group
   mirroring `[mysql]`, or copy the MyISAM files at the OS level under
   `FLUSH TABLES Blocks, Lfns WITH READ LOCK`.

4. **Record the baseline** so the verification below has something to compare against:

   ```sql
   SELECT COUNT(*) FROM Blocks;  SELECT MAX(BlockId) FROM Blocks;
   SELECT COUNT(*) FROM Lfns;
   ```

5. **Stop the Kraken agents** so nothing writes while the tables are locked.

   *Checked 2026-09-22: there is no long-running agent to stop. `show processlist` shows
   no persistent clients, and t3desk000 runs no Kraken daemon or crontab -- writes come
   from short-lived batch-job connections (`bin/checkFile.py` and friends), which will
   simply queue behind the table lock. `Files` grew ~25k rows in a day, so the flow is
   real but intermittent. If the ALTER turns out to be short, a formal outage may be
   unnecessary; that depends on the timing test, which is still blocked on privileges.*

## Verification afterwards

```sql
SHOW CREATE TABLE Blocks\G     -- BlockId int(11) NOT NULL AUTO_INCREMENT
SHOW CREATE TABLE Lfns\G       -- BlockId int(11) NOT NULL
SELECT COUNT(*) FROM Blocks;   -- unchanged from the baseline
SELECT MAX(BlockId) FROM Blocks;
SELECT COUNT(*) FROM Lfns;     -- unchanged
SELECT COUNT(*) FROM Lfns l JOIN Blocks b ON l.BlockId = b.BlockId;   -- joins still land
```

Then restart the agents, and regenerate the committed schema:

```bash
cd $KRAKEN_BASE/mysql && ./dump-schema.sh > schema.sql
```

## Rollback

Widening is not destructive -- every old value fits. If something goes wrong mid-way the
recovery is to restore the backup, not to narrow the column back. Narrowing would fail
anyway once any id exceeds 8,388,607.

## Optional, same window

Both add risk to the outage; take them or leave them.

- `Lfns.NEvents` and `Files.NEvents` are also `mediumint`. A file with more than 8.4M
  events is recorded wrong today, silently. Same one-line `MODIFY ... int`.
- Add a `[client]` group to `~cmsprod/.my.cnf` mirroring `[mysql]`, so `mysqldump`,
  `mysqladmin` and the other standard tools work -- which matters most exactly when you
  want a quick backup.

## Measure the growth rate

No table in this database has a timestamp column, so the current rate of block creation
cannot be recovered from the data. The "roughly four years of headroom" figure in
[README.md](README.md) is a lifetime average since 2014; the recent rate is probably
higher. Start logging the counter now -- a month of data settles it:

```cron
0 6 * * 1  mysql -N -B -e "select now(), auto_increment from information_schema.tables \
             where table_schema='Bambu' and table_name='Blocks';" >> ~/blockid-growth.log
```
