import asyncio
import pathlib
import sqlite3
import tempfile
import threading
import traceback

import aiosqlite


async def probe_thread_to_loop_signal():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def worker():
        loop.call_soon_threadsafe(future.set_result, "ok")

    threading.Thread(target=worker).start()
    return await asyncio.wait_for(future, timeout=2)


async def probe_aiosqlite_roundtrip():
    db_path = pathlib.Path(tempfile.gettempdir()) / "i_safe_runtime_probe.db"
    db = await aiosqlite.connect(db_path)
    try:
        await db.execute("create table if not exists probe(id integer primary key, value text)")
        await db.execute("insert into probe(value) values (?)", ("ok",))
        await db.commit()
        cursor = await db.execute("select value from probe")
        rows = await cursor.fetchall()
        return rows
    finally:
        await db.close()


def probe_sqlite3_sync():
    db_path = pathlib.Path(tempfile.gettempdir()) / "i_safe_runtime_probe_sync.db"
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("create table if not exists probe(id integer primary key, value text)")
        cur.execute("insert into probe(value) values (?)", ("ok",))
        conn.commit()
        cur.execute("select value from probe")
        return cur.fetchall()
    finally:
        conn.close()


async def main():
    print("sqlite3_sync", probe_sqlite3_sync())

    try:
        print("thread_to_loop", await probe_thread_to_loop_signal())
    except Exception as exc:
        print("thread_to_loop_error", repr(exc))
        raise

    try:
        print("aiosqlite", await asyncio.wait_for(probe_aiosqlite_roundtrip(), timeout=2))
    except Exception as exc:
        print("aiosqlite_error", repr(exc))
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
