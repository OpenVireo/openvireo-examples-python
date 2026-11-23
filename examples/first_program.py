"""A first program: sign in, list the vaults, read one field and sign out.

Guide: https://developer.openvireo.com/sdk/#a-first-program

    OV_EMAIL=... OV_PASSWORD=... OV_SECRET_KEY=... python examples/first_program.py "ov://Personal/GitHub/username"
"""

import asyncio
import sys

import openvireo as ov
from openvireo.hosts import default_host

from _common import ISSUER, env


async def main(email: str, password: bytes, secret_key: bytes, reference: str) -> None:
    client = ov.OvClient(
        ov.ClientConfig(
            device=ov.DeviceInfo(id=None, name="My script", platform=ov.Platform.CLI),
            offline=False,
            server=None,
        ),
        default_host(),
    )
    account = await client.connect(ISSUER)
    # Returns LoginStep.NEEDS_TOTP when two-step sign-in is on: see hosted_account.py
    await account.login(ov.LoginInput(email=email, password=password, secret_key=secret_key, totp=None, trust_device=True))

    vaults = await account.vaults()
    for info in vaults:
        print(info.name, info.role)
    if vaults and reference:
        vault = await account.open_vault(vaults[0].id)
        print(vault.read_field(reference).decode())
    await account.sign_out(False)


if __name__ == "__main__":
    asyncio.run(main(
        env("OV_EMAIL"),
        env("OV_PASSWORD").encode(),
        env("OV_SECRET_KEY").encode(),
        sys.argv[1] if len(sys.argv) > 1 else "",
    ))
