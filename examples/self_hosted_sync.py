"""A self-hosted sync server: pairing a device, syncing a .kdbx file, and the other calls.

Guide: https://developer.openvireo.com/sdk/guides/self-hosted-sync/

    python examples/self_hosted_sync.py pair https://sync.example.org ABCD-EFGH
    python examples/self_hosted_sync.py sync https://sync.example.org personal Passwords.kdbx

Pairing is kept in the OS keychain, so `sync` works in a later run. The file's password is read from
KDBX_PASSWORD; the merged file is written back to the same path.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import openvireo as ov
from openvireo.hosts import KeyringStore, default_host

from _common import env


def make_client() -> ov.OvClient:
    return ov.OvClient(
        ov.ClientConfig(device=ov.DeviceInfo(id=None, name="Laptop", platform=ov.Platform.CLI), offline=False, server=None),
        default_host(store=KeyringStore()),  # a persistent store, so the pairing survives a restart
    )


# Pairing
async def pair(client: ov.OvClient, url: str, code: str) -> ov.SelfHosted:
    return await ov.SelfHosted.pair(client, url, code, "Laptop")


async def restore(client: ov.OvClient, url: str) -> ov.SelfHosted:
    # next time, with the same persistent store; None when this device isn't paired with that server
    server = await ov.restore_self_hosted(client, url)
    if server is None:
        sys.exit(f"Not paired with {url}: run `pair` first.")
    return server


# Syncing a database
async def sync_file(server: ov.SelfHosted, database_id: str, path: pathlib.Path, password: bytes) -> None:
    creds = ov.KdbxCredentials(password=password, key_file=None)
    result = await server.sync_database(database_id, path.read_bytes(), creds)
    # result.kdbx is the merged file: save it locally and reopen it (result.report says what changed)
    path.write_bytes(result.kdbx)
    print(result.report)


# Other calls
async def other_calls(server: ov.SelfHosted) -> None:
    print(await server.health())  # '{"status":"ok"}'; not_sync_server for another site
    for db in await server.list_databases():  # BlobMeta: id, revision, etag, size, updated_at
        print(db.id, db.revision, db.size, db.updated_at)
    first = await server.download("personal")  # the .kdbx as uploaded, or None
    print("personal:", len(first) if first else None, "bytes")
    code = (await server.create_pairing_code()).code  # for the next device
    print("pairing code for the next device:", code)
    stream = await server.events()  # next() gives AccountEvent.DATABASE_CHANGED
    stream.close()


async def main(args: list[str]) -> None:
    client = make_client()
    if args[:1] == ["pair"] and len(args) == 3:
        server = await pair(client, args[1], args[2])
        await other_calls(server)
    elif args[:1] == ["sync"] and len(args) == 4:
        server = await restore(client, args[1])
        await sync_file(server, args[2], pathlib.Path(args[3]), env("KDBX_PASSWORD").encode())
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
