from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from importlib import resources
from typing import Any

logger = logging.getLogger(__name__)

_MIGRATIONS_PACKAGE = "auto_water.migrations"
_NAME_RE = re.compile(r"^(\d+)_(.+)\.(up|down)\.sql$")

_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    up: str
    down: str


def load_migrations() -> list[Migration]:
    """Parse ``NNN_name.{up,down}.sql`` files embedded in ``auto_water.migrations``,
    pair them by integer version, and return them sorted ascending."""
    ups: dict[int, str] = {}
    downs: dict[int, str] = {}
    names: dict[int, str] = {}
    for entry in resources.files(_MIGRATIONS_PACKAGE).iterdir():
        if not entry.is_file():
            continue
        match = _NAME_RE.match(entry.name)
        if not match:
            continue
        version = int(match.group(1))
        names[version] = match.group(2)
        content = entry.read_text(encoding="utf-8")
        if match.group(3) == "up":
            ups[version] = content
        else:
            downs[version] = content

    migrations: list[Migration] = []
    for version in sorted(ups):
        if version not in downs:
            raise ValueError(f"migration {version} ({names[version]}) is missing a .down.sql")
        migrations.append(Migration(version, names[version], ups[version], downs[version]))
    return migrations


def _default_connect(dsn: str) -> Any:
    import psycopg

    return psycopg.connect(dsn)


def _applied_versions(conn: Any) -> set[int]:
    with conn.cursor() as cur:
        cur.execute(_MIGRATIONS_TABLE)
        conn.commit()
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def migrate_up(conn: Any, migrations: list[Migration] | None = None) -> list[int]:
    """Apply every migration not yet recorded in ``schema_migrations``, ascending.
    Returns the versions applied (empty if already up to date)."""
    migrations = load_migrations() if migrations is None else migrations
    applied = _applied_versions(conn)
    done: list[int] = []
    for migration in migrations:
        if migration.version in applied:
            continue
        with conn.cursor() as cur:
            cur.execute(migration.up)  # noqa: S608 - trusted embedded migration file, not user input
            cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (migration.version,))
        conn.commit()
        logger.info("applied migration %03d_%s", migration.version, migration.name)
        done.append(migration.version)
    return done


def migrate_down(conn: Any, target: int = 0, migrations: list[Migration] | None = None) -> list[int]:
    """Roll back applied migrations down to (but not including) ``target``, descending.
    Returns the versions rolled back."""
    migrations = load_migrations() if migrations is None else migrations
    by_version = {m.version: m for m in migrations}
    done: list[int] = []
    for version in sorted(_applied_versions(conn), reverse=True):
        if version <= target:
            break
        migration = by_version.get(version)
        if migration is None:
            raise ValueError(f"no .down.sql available for applied version {version}")
        with conn.cursor() as cur:
            cur.execute(migration.down)  # noqa: S608 - trusted embedded migration file, not user input
            cur.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
        conn.commit()
        logger.info("rolled back migration %03d_%s", version, migration.name)
        done.append(version)
    return done


def _main(argv: list[str] | None = None) -> int:
    import argparse

    from .config import Config
    from .logging_config import configure_logging

    parser = argparse.ArgumentParser(prog="auto_water.migrate")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("up", help="apply pending migrations")
    down = sub.add_parser("down", help="roll back migrations")
    down.add_argument("--to", type=int, default=0, help="target version to roll back to (default 0)")
    args = parser.parse_args(argv)

    config = Config.from_env()
    configure_logging(config.log_level)
    if not config.database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    conn = _default_connect(config.database_url)
    try:
        if args.command == "down":
            migrate_down(conn, target=args.to)
        else:  # default to "up"
            migrate_up(conn)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
