"""Live events: react when another device changes a vault, or when access changes.

Guide: https://developer.openvireo.com/sdk/guides/events/

Running it signs in, opens the first vault and prints events until you press Ctrl-C or the session
ends. Edit something in another OpenVireo app to see one.
"""

from __future__ import annotations

import asyncio

import openvireo as ov

from _common import make_client, sign_in


def render(vaults: list[ov.VaultInfo]) -> None:
    print("Vaults now:", ", ".join(v.name for v in vaults))


async def watch(account: ov.Account, vault: ov.Vault) -> None:
    stream = await account.subscribe()
    try:
        while (event := await stream.next()) is not None:
            if isinstance(event, ov.AccountEvent.VAULT_CHANGED):
                # another device uploaded (or deleted) a vault this account can open
                print("Vault changed:", event.vault_id)
                if event.vault_id == vault.id() and event.etag != vault.etag():
                    await vault.sync(ov.SyncOptions(local_changed=False))
            elif isinstance(event, ov.AccountEvent.VAULTS_CHANGED):
                render(event.vaults)  # access changed: vaults added, removed or re-keyed
            elif isinstance(event, ov.AccountEvent.SESSION_ENDED):
                break
    finally:
        stream.close()  # from any thread; a pending next() then returns None


async def main() -> None:
    account = await sign_in(make_client())
    try:
        vaults = await account.vaults()
        if not vaults:
            print("No vaults to watch.")
            return
        vault = await account.open_vault(vaults[0].id)
        print("Watching for changes (Ctrl-C to stop)...")
        await watch(account, vault)
    finally:
        await account.sign_out(False)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
