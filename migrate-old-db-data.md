# Migrating data from the old deployment's database

You don't need a clean database. You can do it after the new deployment already has data, because the schema is a single table that's easy to merge.

The `url` table has three columns: `id` (an auto-incrementing integer primary key), `source_key` (unique) and `name`. `tags` is a JSONB column. Nothing else references it, so there are no foreign keys to break.

## What to watch for

- **`id` collisions:** both databases will have used ids 1, 2, 3…, so a plain data dump from the old one will fail on the primary key. Don't copy `id`. Let the new database assign fresh ids.
- **`source_key` collisions:** this column is unique. If the same `source_key` exists in both databases, you have to choose whether the old row is skipped or overwrites the new one.

## Suggested approach

This keeps the new data and adds the old rows that are missing.

1. Dump only the data from the old database, leaving out `id`:

   ```
   psql <old> -c "\copy (SELECT source_key, name, tags FROM url) TO 'old_urls.csv' CSV HEADER"
   ```

2. Load the file into a staging table in the new database, then insert from it:

   ```sql
   CREATE TEMP TABLE url_import (source_key text, name text, tags jsonb);
   \copy url_import FROM 'old_urls.csv' CSV HEADER

   INSERT INTO url (source_key, name, tags)
   SELECT source_key, name, tags FROM url_import
   ON CONFLICT (source_key) DO NOTHING;   -- or DO UPDATE SET name = EXCLUDED.name, tags = EXCLUDED.tags
   ```

Use `DO NOTHING` if the new deployment's data should win, or `DO UPDATE` if the old data should.

## Other things to know

- Run the import after the `migrate` job has created the table, i.e. once the new stack is up.
- If you load with explicit ids anyway, run `SELECT setval(pg_get_serial_sequence('url','id'), (SELECT max(id) FROM url));` afterwards. Otherwise the next API insert will hit a duplicate-key error. Skipping `id`, as above, avoids this.
- Take a `pg_dump` of the old database as a backup before you tear it down.
- The CSV route is simplest for a table this small. Both deployments run Postgres 18 (per `compose.yml`), so a `pg_dump --data-only --column-inserts` would also work. But it carries the `id` column, which is why I'd avoid it here.
