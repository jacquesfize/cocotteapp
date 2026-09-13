import { openDB } from 'idb'

const DB_NAME = 'cocotte-offline'
const DB_VERSION = 1
const STORE = 'pending-writes'

let dbPromise = null

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

export async function queueWrite(entry) {
  const db = await getDb()
  return db.add(STORE, { ...entry, createdAt: Date.now() })
}

export async function listQueuedWrites() {
  const db = await getDb()
  return db.getAll(STORE)
}

export async function removeQueuedWrite(id) {
  const db = await getDb()
  return db.delete(STORE, id)
}

export async function clearQueue() {
  const db = await getDb()
  return db.clear(STORE)
}
