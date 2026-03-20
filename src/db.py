"""Datenbank-Modul — SQLite-Verwaltung für Connector-Konfigurationen."""

import sqlite3
import json
from pathlib import Path

# Datenbankpfad im Home-Verzeichnis
DB_DIR = Path.home() / ".business-bridge"
DB_PATH = DB_DIR / "connectors.db"


def _get_connection() -> sqlite3.Connection:
    """Datenbankverbindung herstellen und Tabellen erstellen falls nötig."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS connectors (
            name TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            base_url TEXT NOT NULL,
            api_key TEXT,
            config TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def save_connector(name: str, platform: str, base_url: str,
                   api_key: str | None = None, config: dict | None = None):
    """Connector in der Datenbank speichern oder aktualisieren."""
    conn = _get_connection()
    conn.execute("""
        INSERT INTO connectors (name, platform, base_url, api_key, config, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(name) DO UPDATE SET
            platform=excluded.platform,
            base_url=excluded.base_url,
            api_key=excluded.api_key,
            config=excluded.config,
            updated_at=datetime('now')
    """, (name, platform, base_url, api_key, json.dumps(config or {})))
    conn.commit()
    conn.close()


def get_connector(name: str) -> dict | None:
    """Connector aus der Datenbank laden."""
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM connectors WHERE name = ?", (name,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    result = dict(row)
    result["config"] = json.loads(result["config"])
    return result


def list_connectors() -> list[dict]:
    """Alle gespeicherten Connectors auflisten."""
    conn = _get_connection()
    rows = conn.execute("SELECT * FROM connectors ORDER BY name").fetchall()
    conn.close()
    results = []
    for row in rows:
        r = dict(row)
        r["config"] = json.loads(r["config"])
        results.append(r)
    return results


def delete_connector(name: str) -> bool:
    """Connector aus der Datenbank löschen."""
    conn = _get_connection()
    cursor = conn.execute("DELETE FROM connectors WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
