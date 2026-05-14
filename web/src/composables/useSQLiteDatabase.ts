import initSqlJs, { type Database, type SqlJsStatic } from 'sql.js'
import sqlWasmUrl from 'sql.js/dist/sql-wasm.wasm?url'

export type SQLiteBindValue = string | number | Uint8Array | null

const SQLITE_DB_URL = `${import.meta.env.BASE_URL}data/sqlite/chinese-poetry.sqlite`

let sqlJsPromise: Promise<SqlJsStatic> | null = null
let databasePromise: Promise<Database> | null = null

function getSqlJs() {
  if (!sqlJsPromise) {
    sqlJsPromise = initSqlJs({
      locateFile: () => sqlWasmUrl
    })
  }
  return sqlJsPromise
}

async function fetchDatabaseBinary() {
  const response = await fetch(SQLITE_DB_URL)
  if (!response.ok) {
    throw new Error(`Failed to load sqlite database: ${response.status}`)
  }
  return new Uint8Array(await response.arrayBuffer())
}

export async function getSQLiteDatabase() {
  if (!databasePromise) {
    databasePromise = Promise.all([getSqlJs(), fetchDatabaseBinary()]).then(([sqlJs, binary]) => {
      return new sqlJs.Database(binary)
    })
  }
  return databasePromise
}

function normalizeRow<T>(columns: string[], values: unknown[]): T {
  return Object.fromEntries(columns.map((column, index) => [column, values[index]])) as T
}

export async function queryRows<T = Record<string, unknown>>(
  sql: string,
  params: SQLiteBindValue[] = []
): Promise<T[]> {
  const db = await getSQLiteDatabase()
  const stmt = db.prepare(sql)

  try {
    if (params.length > 0) {
      stmt.bind(params)
    }

    const rows: T[] = []
    while (stmt.step()) {
      const values = stmt.get()
      rows.push(normalizeRow<T>(stmt.getColumnNames(), values))
    }
    return rows
  } finally {
    stmt.free()
  }
}

export async function queryFirst<T = Record<string, unknown>>(
  sql: string,
  params: SQLiteBindValue[] = []
): Promise<T | null> {
  const rows = await queryRows<T>(sql, params)
  return rows[0] ?? null
}

export async function queryScalar<T = string | number | null>(
  sql: string,
  params: SQLiteBindValue[] = []
): Promise<T | null> {
  const row = await queryFirst<Record<string, T>>(sql, params)
  if (!row) return null
  const firstKey = Object.keys(row)[0]
  return firstKey ? row[firstKey] ?? null : null
}

export function escapeLike(value: string) {
  return value.replace(/[%_\\]/g, char => `\\${char}`)
}
