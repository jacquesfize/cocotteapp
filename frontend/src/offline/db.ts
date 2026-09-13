import { openDB, type IDBPDatabase } from 'idb'

const DB_NAME = 'cocotte-offline'
const DB_VERSION = 1
const STORE = 'pending-writes'

export interface MarkOwnedWrite {
  type: 'mark-owned'
  shoppingListId: number | string
  ingredientIds: number[]
}

export type QueuedWriteInput = MarkOwnedWrite

export type QueuedWrite = QueuedWriteInput & { id: number; createdAt: number }

let dbPromise: Promise<IDBPDatabase> | null = null

function getDb() {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        db.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true })
      },
    })
  }
  return dbPromise
}

export async function queueWrite(entry: QueuedWriteInput) {
  const db = await getDb()
  return db.add(STORE, { ...entry, createdAt: Date.now() })
}

export async function listQueuedWrites(): Promise<QueuedWrite[]> {
  const db = await getDb()
  return db.getAll(STORE)
}

export async function removeQueuedWrite(id: number) {
  const db = await getDb()
  return db.delete(STORE, id)
}

export async function clearQueue() {
  const db = await getDb()
  return db.clear(STORE)
}
