"""Shared setup for the examples: a client, and an account signed in from environment variables.

Set OV_EMAIL, OV_PASSWORD and OV_SECRET_KEY (and OV_ISSUER for a server other than
https://accounts.openvireo.com). The Secret Key is only needed the first time on a device.
"""

from __future__ import annotations

import os
import sys

import openvireo as ov
from openvireo.hosts import default_host

ISSUER = os.environ.get("OV_ISSUER", "https://accounts.openvireo.com")


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"Set {name} to run this example.")
    return value


def make_client(name: str = "OpenVireo examples", *, offline: bool = False, cache_dir: str | None = None) -> ov.OvClient:
    return ov.OvClient(
        ov.ClientConfig(
            device=ov.DeviceInfo(id=None, name=name, platform=ov.Platform.CLI),
            offline=offline,
            server=None,
        ),
        default_host(cache_dir=cache_dir),
    )


def ask_for_code() -> str:
    return input("Authenticator code: ").strip()


async def sign_in(client: ov.OvClient) -> ov.Account:
    """Connects and signs in, asking for a TOTP code when two-step sign-in is on."""
    account = await client.connect(ISSUER)
    secret_key = os.environ.get("OV_SECRET_KEY")
    login = ov.LoginInput(
        email=env("OV_EMAIL"),
        password=env("OV_PASSWORD").encode(),
        secret_key=secret_key.encode() if secret_key else None,
        totp=None,
        trust_device=True,
    )
    step = await account.login(login)
    while isinstance(step, ov.LoginStep.NEEDS_TOTP):
        step = await account.submit_totp(step.challenge, ask_for_code())
    return account
