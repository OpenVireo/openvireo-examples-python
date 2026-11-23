"""Offline: unlock and edit from the cached copy while the servers can't be reached, and merge the
edits in when back online.

Guide: https://developer.openvireo.com/sdk/guides/offline/

Offline needs a persistent store and cache, so this uses the OS keychain and ~/.cache/openvireo.
Run it online once (it signs in), then again offline (it unlocks from the cache).

    python examples/offline.py "ov://Home/Wifi/password" "new value"
"""

from __future__ import annotations

import asyncio
import sys

import openvireo as ov
from openvireo.hosts import KeyringStore, default_host

from _common import ISSUER, ask_for_code, env


async def main(reference: str, value: bytes) -> None:
    client = ov.OvClient(
        ov.ClientConfig(device=ov.DeviceInfo(id=None, name="Laptop", platform=ov.Platform.CLI), offline=True, server=None),
        default_host(store=KeyringStore(), cache_dir="~/.cache/openvireo"),  # offline needs a persistent cache
    )
    password = env("OV_PASSWORD").encode()
    account = await client.connect(ISSUER)
    if not account.is_signed_in():
        step = await account.login(ov.LoginInput(
            email=env("OV_EMAIL"), password=password, secret_key=env("OV_SECRET_KEY").encode(),
            totp=None, trust_device=True,
        ))
        while isinstance(step, ov.LoginStep.NEEDS_TOTP):
            step = await account.submit_totp(step.challenge, ask_for_code())
    elif not account.is_unlocked():
        await account.unlock(password, None)  # works offline from the cached wrapped keyset

    vault_name = reference.removeprefix("ov://").split("/")[0]
    info = next(v for v in await account.vaults() if v.name == vault_name)
    vault = await account.open_vault(info.id)  # offline: the local copy
    print("offline:", account.is_offline())  # True while the servers can't be reached

    try:
        await vault.write_field(reference, value, False)
    except ov.OvError as e:
        if e.code != ov.OvErrorCode.NETWORK_ERROR:
            raise  # offline: the edit is kept and merges in later
        print("Saved locally; it uploads when you're back online.")

    if account.is_offline():
        try:
            result = await account.reconnect()  # back online; result.dropped: revoked vaults, forgotten
            print("reconnected; dropped:", result.dropped)
            await vault.sync(ov.SyncOptions(local_changed=True))  # uploads the kept edit
        except ov.OvError as e:
            if e.code != ov.OvErrorCode.NETWORK_ERROR:
                raise
            print("Still offline.")
    account.lock()  # the session stays, so the next run can unlock offline


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1], sys.argv[2].encode()))
