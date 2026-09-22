#!/bin/bash
# Regenerate schema.sql from the live Bambu database.  Run on a t3 node as cmsprod:
#
#     ./dump-schema.sh > schema.sql
#
# The mysql client reads the [mysql] group of ~/.my.cnf, which is where the Kraken
# credentials live (kdb.py uses read_default_group="mysql").  mysqldump reads
# [client]/[mysqldump] instead and therefore cannot connect -- hence this script.

DB=${1:-Bambu}
ORDER="Datasets Blocks Lfns Requests Files"      # logical order, inputs then outputs

all=$(mysql -N -B "$DB" -e "show tables") || exit 1
# the listed tables first, then anything else that turned up
tables=""
for t in $ORDER; do
  echo "$all" | grep -qx "$t" && tables="$tables $t"
done
for t in $all; do
  echo "$ORDER" | grep -qw "$t" || tables="$tables $t"
done

cat <<HDR
-- Kraken production database '$DB' -- schema of record.
--
-- Read off the live server on $(date +%Y-%m-%d) by $(basename "$0").
-- See README.md in this directory for what the tables mean and how to connect.
--
-- Regenerate (from t3desk000.mit.edu as cmsprod):
--
--     ./$(basename "$0") > schema.sql
--
-- AUTO_INCREMENT counters are stripped: they are state, not schema.

CREATE DATABASE IF NOT EXISTS $DB;
USE $DB;
HDR

for t in $tables; do
  echo
  mysql "$DB" -e "show create table \`$t\`\G" \
    | sed -e '/^\*\{10,\}/d' \
          -e '/^[[:space:]]*Table:[[:space:]]/d' \
          -e 's/^[[:space:]]*Create Table:[[:space:]]//' \
          -e 's/ AUTO_INCREMENT=[0-9]*//' \
          -e 's/^) ENGINE\(.*\)$/) ENGINE\1;/'
done
