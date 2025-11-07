#!/usr/bin/env python3
"""
Import Textract JSON into SQLite

Creates these tables (if not exist):
- documents
- form_fields
- tables_meta
- table_cells

Usage:
    python textract_to_sql.py /path/to/textract_analysis.json

If no path provided, defaults to `textract_analysis_1_20251107_152416.json` in the repo root.
"""
import sqlite3
import json
import os
import sys
from datetime import datetime

DEFAULT_JSON = "textract_analysis_1_20251107_152416.json"
DB_FILE = "textract_data.db"

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        file_size_bytes INTEGER,
        analyzed_at TEXT,
        full_text TEXT,
        total_blocks INTEGER,
        average_confidence REAL,
        word_count INTEGER,
        raw_json TEXT,
        created_at TEXT
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS form_fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        key TEXT,
        value TEXT,
        confidence REAL,
        FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS tables_meta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        table_index INTEGER,
        row_count INTEGER,
        column_count INTEGER,
        confidence REAL,
        table_json TEXT,
        FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS table_cells (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER,
        row_index INTEGER,
        col_index INTEGER,
        cell_text TEXT,
        FOREIGN KEY(table_id) REFERENCES tables_meta(id) ON DELETE CASCADE
    )
    """
]


def create_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    for stmt in SCHEMA:
        cur.executescript(stmt)
    conn.commit()


def insert_document(conn: sqlite3.Connection, results: dict, filename: str, file_size: int) -> int:
    cur = conn.cursor()
    doc = results.get('file_info', {})
    analyzed_at = doc.get('analyzed_at') or results.get('file_info', {}).get('analyzed_at')
    text_det = results.get('text_detection', {})

    cur.execute(
        '''INSERT INTO documents (filename, file_size_bytes, analyzed_at, full_text, total_blocks, average_confidence, word_count, raw_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            filename,
            file_size,
            analyzed_at,
            text_det.get('full_text', ''),
            text_det.get('total_blocks', 0),
            text_det.get('average_confidence', 0.0),
            text_det.get('word_count', 0),
            json.dumps(results, ensure_ascii=False),
            datetime.utcnow().isoformat()
        )
    )
    conn.commit()
    return cur.lastrowid


def insert_form_fields(conn: sqlite3.Connection, document_id: int, results: dict):
    cur = conn.cursor()
    fields = results.get('form_analysis', {}).get('form_fields', [])
    for f in fields:
        cur.execute(
            'INSERT INTO form_fields (document_id, key, value, confidence) VALUES (?, ?, ?, ?)',
            (document_id, f.get('key', ''), f.get('value', ''), f.get('confidence', 0.0))
        )
    conn.commit()


def insert_tables(conn: sqlite3.Connection, document_id: int, results: dict):
    cur = conn.cursor()
    tables = results.get('table_analysis', {}).get('tables', [])
    for idx, t in enumerate(tables):
        rows = t.get('rows', [])
        row_count = t.get('row_count', len(rows))
        column_count = t.get('column_count', 0)
        confidence = t.get('confidence', 0.0)
        table_json = json.dumps(t, ensure_ascii=False)

        cur.execute(
            'INSERT INTO tables_meta (document_id, table_index, row_count, column_count, confidence, table_json) VALUES (?, ?, ?, ?, ?, ?)',
            (document_id, idx, row_count, column_count, confidence, table_json)
        )
        table_id = cur.lastrowid

        # Insert cells
        for r_idx, row in enumerate(rows):
            # row may be list of cells; handle missing columns
            for c_idx, cell in enumerate(row):
                cell_text = cell if cell is not None else ''
                cur.execute(
                    'INSERT INTO table_cells (table_id, row_index, col_index, cell_text) VALUES (?, ?, ?, ?)',
                    (table_id, r_idx, c_idx, cell_text)
                )
    conn.commit()


def import_json_to_db(json_path: str, db_path: str = DB_FILE):
    if not os.path.exists(json_path):
        print(f"JSON file not found: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    file_size = os.path.getsize(json_path)

    conn = sqlite3.connect(db_path)
    create_schema(conn)

    print("Inserting document record...")
    document_id = insert_document(conn, results, os.path.basename(json_path), file_size)
    print(f"Document id: {document_id}")

    print("Inserting form fields...")
    insert_form_fields(conn, document_id, results)

    print("Inserting tables and their cells...")
    insert_tables(conn, document_id, results)

    conn.close()
    print(f"Import complete. DB file: {db_path}")


if __name__ == '__main__':
    json_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
    import_json_to_db(json_path)
