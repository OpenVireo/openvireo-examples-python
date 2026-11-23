"""Service accounts: create one for CI, then read, inject and write secrets with its token.

Guide: https://developer.openvireo.com/sdk/guides/service-accounts/

    OPENVIREO_SERVICE_ACCOUNT_TOKEN=... python examples/service_accounts.py "ov://Team Infra/CI/token"

create() needs an organisation owner or admin signed in, so main() doesn't call it.
"""

from __future__ import annotations

import asyncio
import os
import sys

import openvireo as ov

from _common import make_client


# Creating one
async def create(account: ov.Account, org_id: str, vault_id: str) -> None:
    created = await account.create_service_account(org_id, ov.NewServiceAccount(
        name="ci",
        vaults=[ov.VaultGrantRequest(vault_id=vault_id, role=ov.VaultRole.READ)],
        expires_at="2027-01-01T00:00:00Z",  # or None
        secret_name=None,
    ))
    print(created.token.decode())  # show it once; store it as a CI secret

    await account.issue_service_account_secret(created.service_account.id, "staging", None)


# Reading and writing
async def main(reference: str) -> None:
    client = make_client("CI")
    sa = await ov.ServiceAccount.from_token(client, os.environ["OPENVIREO_SERVICE_ACCOUNT_TOKEN"].encode())
    try:
        password = await sa.read(reference)
        print(f"{reference}: {len(password)} bytes")

        template = f"TOKEN={reference.replace(' ', '%20')}\n".encode()
        injected = await sa.inject(template)  # mask injected.secrets in logs
        print(f"injected {len(injected.secrets)} secret(s)")

        if os.environ.get("ROTATE"):
            await sa.write(reference, os.environ["ROTATE"].encode(), False)  # needs the write role
    finally:
        sa.close()  # wipes the keys from memory


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1]))
