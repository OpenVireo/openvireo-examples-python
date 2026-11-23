"""Moving a .kdbx file into an account: as a new vault, or merged into a vault you already have.

Guide: https://developer.openvireo.com/sdk/guides/move-to-account/

    python examples/move_to_account.py Passwords.kdbx            # a new vault named after the file
    python examples/move_to_account.py Passwords.kdbx "Personal" # merge into the vault "Personal"

The file's password is read from KDBX_PASSWORD.
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

import openvireo as ov

from _common import env, make_client, sign_in


async def import_as_new_vault(account: ov.Account, file_bytes: bytes, password: bytes, name: str) -> None:
    creds = ov.KdbxCredentials(password=password, key_file=None)
    outcome = await account.import_kdbx(file_bytes, creds, ov.ImportMode.NEW_VAULT(name=name, org_id=None))
    if not outcome.uploaded:
        # the vault exists but its first upload failed (outcome.upload_error): retry it later
        await outcome.vault.sync(ov.SyncOptions(local_changed=True))
    print("Imported into", outcome.vault.name())


async def merge_into(client: ov.OvClient, vault: ov.Vault, file_bytes: bytes, password: bytes) -> None:
    file = await client.open_local(file_bytes, ov.KdbxCredentials(password=password, key_file=None))
    summary = vault.import_from(file, ov.LocalImportMode.MERGE())  # added, updated, unchanged
    # or: ov.LocalImportMode.COPIES(parent_group_id=group_id), with vault.import_targets() listing the groups
    await vault.sync(ov.SyncOptions(local_changed=True))
    print(summary)


async def main(path: str, into: str | None) -> None:
    file_bytes = pathlib.Path(path).read_bytes()
    password = env("KDBX_PASSWORD").encode()
    client = make_client()
    account = await sign_in(client)
    try:
        if into is None:
            await import_as_new_vault(account, file_bytes, password, pathlib.Path(path).stem)
        else:
            info = next(v for v in await account.vaults() if v.name == into)
            await merge_into(client, await account.open_vault(info.id), file_bytes, password)
    finally:
        await account.sign_out(False)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None))
