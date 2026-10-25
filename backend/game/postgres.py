"""Optional hosted store. One session owns the coordinator and serializes transactions.

Requires a direct/session PostgreSQL connection (not a transaction-mode pooler).
Losing the connection fails closed: restart the process to recover durable jobs.
"""

from contextlib import contextmanager
from threading import RLock

from .store import Store


class Row(dict):
    """Keep SQLite's named and positional access at the small SQL boundary."""

    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


def rows(cursor):
    names = [column.name for column in cursor.description] if cursor.description else []
    return lambda values: Row(zip(names, values))


class Connection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, sql, parameters=()):
        # Only static application SQL uses this adapter; values remain bound parameters.
        return self.connection.execute(sql.replace("?", "%s"), parameters)

    def executescript(self, sql):
        for statement in sql.split(";"):
            if statement.strip():
                self.execute(statement)


class PostgresStore(Store):
    def open(self, url):
        import psycopg
        from psycopg.conninfo import conninfo_to_dict

        if "-pooler" in conninfo_to_dict(url).get("host", ""):
            raise ValueError("Use the direct PostgreSQL URL, not a Neon transaction-pooler URL.")
        self._mutex = RLock()
        self._db = psycopg.connect(
            url,
            autocommit=True,
            row_factory=rows,
            connect_timeout=10,
            application_name="allegiance-and-influence",
            client_encoding="utf8",
        )
        try:
            self._db.execute("SET statement_timeout = '15s'")
            # Session lock lasts through commits. Separate preview/production databases
            # have separate ownership. A second worker must not recover the first's jobs.
            owned = self._db.execute(
                "SELECT pg_try_advisory_lock(1936744801, hashtext(current_schema()))"
            ).fetchone()[0]
            if not owned:
                raise RuntimeError("This database already has an active game server. Use one worker.")
        except BaseException:
            self._db.close()
            raise

    @contextmanager
    def connection(self):
        with self._mutex, self._db.transaction():
            yield Connection(self._db)

    def begin_write(self, db):
        # Every connection context already holds the process mutex and a transaction.
        pass

    def add_column(self, db, table, column):
        db.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} TEXT")

    def close(self):
        with self._mutex:
            self._db.close()
