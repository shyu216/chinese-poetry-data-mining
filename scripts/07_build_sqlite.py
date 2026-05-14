#!/usr/bin/env python3
"""
script: 07_build_sqlite.py
stage: P7-前端数据服务
artifact: SQLite 聚合数据库
purpose: 将诗词、作者、词频结果聚合为一个前端可直接读取的 SQLite 数据库。
inputs:
- results/preprocessed
- results/author_v2
- results/wordcount_v2
outputs:
- results/sqlite/chinese-poetry.sqlite
- results/sqlite/meta.json
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED_DIR = PROJECT_ROOT / 'results' / 'preprocessed'
AUTHORS_DIR = PROJECT_ROOT / 'results' / 'author_v2'
WORDCOUNT_DIR = PROJECT_ROOT / 'results' / 'wordcount_v2'
OUTPUT_DIR = PROJECT_ROOT / 'results' / 'sqlite'
DB_PATH = OUTPUT_DIR / 'chinese-poetry.sqlite'
META_PATH = OUTPUT_DIR / 'meta.json'

sys.path.insert(0, str((PROJECT_ROOT / 'scripts' / 'flatbuffers_generated').resolve()))

from AuthorChunk.AuthorChunkFile import AuthorChunkFile  # type: ignore  # noqa: E402

BATCH_SIZE = 1000


def decode_text(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value or ''


def ensure_inputs() -> None:
    required = [
        PREPROCESSED_DIR / 'poems_chunk_meta.json',
        AUTHORS_DIR / 'authors-meta.json',
        WORDCOUNT_DIR / 'meta.json',
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f'缺少输入文件: {missing}')


def connect_db() -> sqlite3.Connection:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    # 仅用于可重复执行的离线构建，优先写入速度；若中途中断，直接重新生成产物即可。
    conn.execute('PRAGMA journal_mode = OFF')
    conn.execute('PRAGMA synchronous = OFF')
    conn.execute('PRAGMA temp_store = MEMORY')
    conn.execute('PRAGMA cache_size = -200000')
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        '''
        CREATE TABLE dataset_meta (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );

        CREATE TABLE poems (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          author TEXT NOT NULL,
          dynasty TEXT NOT NULL,
          genre TEXT NOT NULL,
          poem_type TEXT,
          sentences_text TEXT NOT NULL,
          meter_pattern TEXT,
          hash TEXT NOT NULL,
          words_text TEXT NOT NULL,
          chunk_id INTEGER NOT NULL
        );

        CREATE TABLE authors (
          author TEXT PRIMARY KEY,
          poem_count INTEGER NOT NULL,
          poem_ids_json TEXT NOT NULL,
          poem_type_counts_json TEXT NOT NULL,
          meter_patterns_json TEXT NOT NULL,
          word_frequency_json TEXT NOT NULL,
          similar_authors_json TEXT NOT NULL,
          chunk_id INTEGER NOT NULL
        );

        CREATE TABLE word_counts (
          word TEXT PRIMARY KEY,
          count INTEGER NOT NULL,
          rank INTEGER NOT NULL,
          chunk_id INTEGER NOT NULL
        );
        '''
    )


def insert_dataset_meta(conn: sqlite3.Connection) -> None:
    poems_meta = json.loads((PREPROCESSED_DIR / 'poems_chunk_meta.json').read_text(encoding='utf-8'))
    authors_meta = json.loads((AUTHORS_DIR / 'authors-meta.json').read_text(encoding='utf-8'))
    wordcount_meta = json.loads((WORDCOUNT_DIR / 'meta.json').read_text(encoding='utf-8'))

    meta_rows = [
        ('generated_at', datetime.now(timezone.utc).isoformat()),
        ('poems_total', str(poems_meta['metadata']['total'])),
        ('poems_chunks', str(poems_meta['metadata']['chunks'])),
        ('authors_total', str(authors_meta['totalAuthors'])),
        ('authors_chunks', str(authors_meta['total'])),
        ('wordcount_total', str(wordcount_meta['total_words'])),
        ('wordcount_chunks', str(wordcount_meta['total_chunks'])),
    ]
    conn.executemany('INSERT INTO dataset_meta(key, value) VALUES (?, ?)', meta_rows)


def load_poems(conn: sqlite3.Connection) -> int:
    poem_files = sorted(PREPROCESSED_DIR.glob('poems_chunk_*.csv'))
    total = 0
    insert_sql = '''
      INSERT OR REPLACE INTO poems (
        id, title, author, dynasty, genre, poem_type,
        sentences_text, meter_pattern, hash, words_text, chunk_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    for chunk_id, poem_file in enumerate(poem_files):
        batch = []
        with poem_file.open('r', encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                batch.append((
                    row.get('id', '') or '',
                    row.get('title', '') or '',
                    row.get('author', '') or '佚名',
                    row.get('dynasty', '') or '',
                    row.get('genre', '') or '',
                    row.get('poem_type', '') or '',
                    row.get('sentences_simplified', '') or '',
                    row.get('meter_pattern', '') or '',
                    row.get('hash', '') or '',
                    row.get('words', '') or '',
                    chunk_id,
                ))
                if len(batch) >= BATCH_SIZE:
                    conn.executemany(insert_sql, batch)
                    total += len(batch)
                    batch.clear()

        if batch:
            conn.executemany(insert_sql, batch)
            total += len(batch)

        if chunk_id % 25 == 0 or chunk_id == len(poem_files) - 1:
            print(f'[sqlite] poems: {chunk_id + 1}/{len(poem_files)} chunks')

    return total


def iter_author_rows(meta_chunks: Iterable[dict]) -> Iterable[tuple]:
    for chunk in meta_chunks:
        chunk_id = int(chunk['index'])
        file_path = AUTHORS_DIR / chunk['filename']
        buffer = file_path.read_bytes()
        chunk_file = AuthorChunkFile.GetRootAsAuthorChunkFile(buffer, 0)

        for i in range(chunk_file.AuthorsLength()):
            author = chunk_file.Authors(i)
            if author is None:
                continue

            poem_ids = [decode_text(author.PoemIds(j)) for j in range(author.PoemIdsLength())]
            poem_type_counts = {}
            for j in range(author.PoemTypeCountsLength()):
                item = author.PoemTypeCounts(j)
                if item is None:
                    continue
                key = decode_text(item.Word())
                if key:
                    poem_type_counts[key] = item.Count()

            meter_patterns = []
            for j in range(author.MeterPatternsLength()):
                item = author.MeterPatterns(j)
                if item is None:
                    continue
                pattern = decode_text(item.Pattern())
                if pattern:
                    meter_patterns.append({'pattern': pattern, 'count': item.Count()})

            word_frequency = {}
            for j in range(author.WordFrequencyLength()):
                item = author.WordFrequency(j)
                if item is None:
                    continue
                word = decode_text(item.Word())
                if word:
                    word_frequency[word] = item.Count()

            similar_authors = []
            for j in range(author.SimilarAuthorsLength()):
                item = author.SimilarAuthors(j)
                if item is None:
                    continue
                name = decode_text(item.Author())
                if name:
                    similar_authors.append({'author': name, 'similarity': item.Similarity()})

            yield (
                decode_text(author.Author()),
                author.PoemCount(),
                json.dumps(poem_ids, ensure_ascii=False, separators=(',', ':')),
                json.dumps(poem_type_counts, ensure_ascii=False, separators=(',', ':')),
                json.dumps(meter_patterns, ensure_ascii=False, separators=(',', ':')),
                json.dumps(word_frequency, ensure_ascii=False, separators=(',', ':')),
                json.dumps(similar_authors, ensure_ascii=False, separators=(',', ':')),
                chunk_id,
            )


def load_authors(conn: sqlite3.Connection) -> int:
    authors_meta = json.loads((AUTHORS_DIR / 'authors-meta.json').read_text(encoding='utf-8'))
    insert_sql = '''
      INSERT OR REPLACE INTO authors (
        author, poem_count, poem_ids_json, poem_type_counts_json,
        meter_patterns_json, word_frequency_json, similar_authors_json, chunk_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''

    total = 0
    batch = []
    for chunk_index, row in enumerate(iter_author_rows(authors_meta['chunks'])):
        batch.append(row)
        if len(batch) >= 200:
            conn.executemany(insert_sql, batch)
            total += len(batch)
            batch.clear()
        if chunk_index % 100 == 0:
            print(f'[sqlite] authors: processed {chunk_index + 1}/{len(authors_meta["chunks"])} chunks')

    if batch:
        conn.executemany(insert_sql, batch)
        total += len(batch)

    return total


def load_word_counts(conn: sqlite3.Connection) -> int:
    meta = json.loads((WORDCOUNT_DIR / 'meta.json').read_text(encoding='utf-8'))
    insert_sql = 'INSERT OR REPLACE INTO word_counts (word, count, rank, chunk_id) VALUES (?, ?, ?, ?)'
    total = 0

    for index, chunk in enumerate(meta['chunks']):
        chunk_path = WORDCOUNT_DIR / chunk['file']
        chunk_rows = json.loads(chunk_path.read_text(encoding='utf-8'))
        conn.executemany(insert_sql, ((word, count, rank, index) for word, count, rank in chunk_rows))
        total += len(chunk_rows)
        if index % 5 == 0 or index == len(meta['chunks']) - 1:
            print(f'[sqlite] wordcount: {index + 1}/{len(meta["chunks"])} chunks')

    return total


def create_indexes(conn: sqlite3.Connection) -> None:
    conn.executescript(
        '''
        CREATE INDEX idx_poems_chunk_id ON poems(chunk_id);
        CREATE INDEX idx_poems_author ON poems(author);
        CREATE INDEX idx_poems_dynasty ON poems(dynasty);
        CREATE INDEX idx_poems_genre ON poems(genre);
        CREATE INDEX idx_poems_dynasty_genre ON poems(dynasty, genre);
        CREATE INDEX idx_authors_chunk_id ON authors(chunk_id);
        CREATE INDEX idx_authors_poem_count ON authors(poem_count DESC);
        CREATE INDEX idx_word_counts_chunk_id ON word_counts(chunk_id);
        CREATE INDEX idx_word_counts_rank ON word_counts(rank);
        CREATE INDEX idx_word_counts_count ON word_counts(count DESC);
        '''
    )


def write_meta(conn: sqlite3.Connection, poems_total: int, authors_total: int, wordcount_total: int) -> None:
    payload = {
        'file': DB_PATH.name,
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'sizeBytes': DB_PATH.stat().st_size,
        'tables': {
            'poems': poems_total,
            'authors': authors_total,
            'word_counts': wordcount_total,
        },
        'stats': {
            'poems': conn.execute('SELECT COUNT(*) FROM poems').fetchone()[0],
            'authors': conn.execute('SELECT COUNT(*) FROM authors').fetchone()[0],
            'word_counts': conn.execute('SELECT COUNT(*) FROM word_counts').fetchone()[0],
        },
    }
    META_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def main() -> None:
    ensure_inputs()
    conn = connect_db()
    try:
        create_schema(conn)
        insert_dataset_meta(conn)
        poems_total = load_poems(conn)
        authors_total = load_authors(conn)
        wordcount_total = load_word_counts(conn)
        create_indexes(conn)
        conn.commit()
        conn.execute('VACUUM')
        conn.commit()
        write_meta(conn, poems_total, authors_total, wordcount_total)
        print(f'[sqlite] done: {DB_PATH}')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
