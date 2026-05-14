declare module 'sql.js' {
  export interface SqlJsStatic {
    Database: new (data?: Uint8Array | ArrayLike<number>) => Database
  }

  export interface Statement {
    bind(values?: unknown[] | Record<string, unknown>): void
    step(): boolean
    get(): unknown[]
    getColumnNames(): string[]
    free(): void
  }

  export interface Database {
    prepare(sql: string): Statement
  }

  export interface InitSqlJsOptions {
    locateFile?: (file: string) => string
  }

  export default function initSqlJs(config?: InitSqlJsOptions): Promise<SqlJsStatic>
}
