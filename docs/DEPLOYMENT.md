# Local operation and recovery

The Python development server binds only localhost. For persistent operation the supplied container uses Waitress, a non-root user, a read-only application filesystem and a named `/data` volume. Container acceptance remains pending; do not infer verified production readiness from configuration.

Run `python3 scripts/setup.py` once. It creates `.env` with mode 0600 and refuses to overwrite it. Keep the key private. Then `docker compose up --build -d`. The local endpoint is port 8118. Never use `docker compose down -v` unless you intend to erase the ledger.

For local Python backup, stop the server before copying `tempo.sqlite3` to a private backup location. Restore only while stopped, into a new location, and run `PRAGMA integrity_check` with Python's sqlite3 module. Retain the original until restored projects, entries and exports are verified. Container volume backup/recovery still needs a reproducible acceptance test.

Remote access needs a separately configured trusted HTTPS reverse proxy, firewall and private credentials. No HTTPS deployment is configured or verified. Anyone possessing the owner key can read, edit or delete the complete ledger. No public share links or team roles exist.

## Verified backup procedure

Stop the container before copying its database:

```sh
docker compose stop
mkdir -m 700 backup
container=$(docker compose ps -aq tempo-field)
docker cp "$container:/data/tempo.sqlite3" backup/source.sqlite3
chmod 600 backup/source.sqlite3
python3 scripts/backup.py backup/source.sqlite3 backup/tempo.sqlite3
docker compose start
```

The helper uses SQLite's backup API, checks integrity, creates mode-0600 output and refuses to overwrite an existing destination. Protect both copies. Restore into a **new empty volume**, while stopped, at `/data/tempo.sqlite3`, owned by UID/GID 10001 with mode 0600. The `/data` directory must also be writable by UID 10001. Retain the original volume and backup until exports match and new writes work. Restoring a running timer preserves its original start, so elapsed downtime is counted; edit it if that is not the intended work duration.

Reproduce the isolated test with `docker build -t tempo-field:acceptance .` followed by `python3 scripts/container_acceptance.py`. It creates unique disposable containers and volumes and removes only those test resources. The test checks exact JSON/CSV preservation, a running timer, restart, restore and subsequent edits.

Where an administrator supplies a trusted private CA, pass it with `docker build --secret id=pip_ca,src=/path/to/approved-ca.pem -t tempo-field:acceptance .`. The secret is available only during dependency installation and is not copied into the image. Normal public-CA builds need no secret. Do not disable TLS verification.
