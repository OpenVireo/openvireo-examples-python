"""Account recovery: resetting with a recovery link, and restoring the old vaults afterwards.

Guide: https://developer.openvireo.com/sdk/guides/recovery/

    python examples/recovery.py info <token>     # what a reset would do; works signed out
    python examples/recovery.py status           # after a reset: is there an archive to restore?

reset() and restore() change the account, so they only run when you call them yourself.
"""

from __future__ import annotations

import asyncio
import sys

import openvireo as ov

from _common import ISSUER, make_client, sign_in


# Resetting
async def info(account: ov.Account, token: bytes) -> None:
    i = await account.recover_info(token)  # works signed out
    print(i)  # email, not_before, expires_at, archive_days, personal_vaults, shared_grants, sole_admin_orgs


async def reset(account: ov.Account, token: bytes, new_password: bytes) -> None:
    created = await account.recover(token, new_password, None, True)  # signed in and unlocked afterwards
    print("Your new Secret Key (keep it safe):", created.secret_key.decode())


# Restoring the old vaults
async def restore(account: ov.Account, old_password: bytes, old_secret_key: bytes) -> None:
    status = await account.recovery_status()  # archived, email, expires_at, vaults, locked
    if status.archived and not status.locked:
        await account.restore_from_archive(old_password, old_secret_key)  # vault list reloaded


async def main(args: list[str]) -> None:
    client = make_client()
    if args[:1] == ["info"] and len(args) == 2:
        await info(await client.connect(ISSUER), args[1].encode())
    elif args == ["status"]:
        account = await sign_in(client)
        print(await account.recovery_status())
        await account.sign_out(False)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
