from auto_water.migrate import load_migrations, migrate_down, migrate_up


class FakeCursor:
    """A cursor that fakes just enough of schema_migrations to drive the runner."""

    def __init__(self, conn):
        self._conn = conn
        self._last = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._conn.executed.append(sql)
        normalized = " ".join(sql.split()).upper()
        if normalized.startswith("SELECT VERSION FROM SCHEMA_MIGRATIONS"):
            self._last = "versions"
        elif normalized.startswith("INSERT INTO SCHEMA_MIGRATIONS"):
            self._conn.applied.add(params[0])
            self._last = None
        elif normalized.startswith("DELETE FROM SCHEMA_MIGRATIONS"):
            self._conn.applied.discard(params[0])
            self._last = None
        else:
            self._last = None

    def fetchall(self):
        if self._last == "versions":
            return [(v,) for v in sorted(self._conn.applied)]
        return []


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.applied = set()
        self.commits = 0
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def test_load_migrations_finds_initial_and_is_sorted():
    migrations = load_migrations()
    assert migrations, "expected at least one migration"
    first = migrations[0]
    assert first.version == 1
    assert "CREATE TABLE" in first.up.upper()
    assert "DROP TABLE" in first.down.upper()
    assert [m.version for m in migrations] == sorted(m.version for m in migrations)


def test_migrate_up_applies_and_is_idempotent():
    conn = FakeConnection()
    applied = migrate_up(conn)
    assert applied == [1]
    assert conn.applied == {1}
    assert any("CREATE TABLE" in sql.upper() for sql in conn.executed)

    # Re-running is a no-op — nothing new applied.
    conn.executed.clear()
    assert migrate_up(conn) == []
    assert conn.applied == {1}


def test_migrate_down_rolls_back():
    conn = FakeConnection()
    migrate_up(conn)
    conn.executed.clear()

    rolled = migrate_down(conn, target=0)
    assert rolled == [1]
    assert conn.applied == set()
    assert any("DROP TABLE" in sql.upper() for sql in conn.executed)


def test_migrate_down_respects_target():
    conn = FakeConnection()
    migrate_up(conn)
    # target equal to the highest applied version → nothing to roll back
    assert migrate_down(conn, target=1) == []
    assert conn.applied == {1}
