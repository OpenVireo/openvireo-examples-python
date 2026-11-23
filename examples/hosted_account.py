"""Hosted accounts: connecting, signing up and in, locking, the account itself, devices and deletion.

Guide: https://developer.openvireo.com/sdk/guides/hosted-account/

Running it signs in, prints the account and its devices, locks and unlocks, and signs out. The
functions that change the account (sign_up, change_password, delete_account, ...) are here to read
and copy; main() doesn't call them.
"""

from __future__ import annotations

import asyncio

import openvireo as ov
from openvireo.hosts import KeyringStore, default_host

from _common import ISSUER, ask_for_code, env


# Connecting
async def connect() -> ov.Account:
    client = ov.OvClient(
        ov.ClientConfig(
            device=ov.DeviceInfo(id=None, name="Backup script on Linux", platform=ov.Platform.CLI),
            offline=False,
            server=None,
        ),
        # where sessions and trusted-device keys live (pip install "openvireo[keyring]")
        default_host(store=KeyringStore(), cache_dir="~/.cache/openvireo"),
    )
    return await client.connect(ISSUER)


# Signing up
async def sign_up(account: ov.Account, email: str, password: bytes) -> None:
    created = await account.register(ov.RegisterInput(email=email, password=password, kdf=None, trust_device=True))
    show_emergency_kit(created.secret_key)  # the only time the Secret Key is shown; the user must keep it


def show_emergency_kit(secret_key: bytes) -> None:
    print("Your Secret Key (keep it safe):", secret_key.decode())


# Signing in
async def sign_in(account: ov.Account, email: str, password: bytes, secret_key: bytes | None) -> None:
    # secret_key: only needed the first time on this device (else None)
    login = ov.LoginInput(email=email, password=password, secret_key=secret_key, totp=None, trust_device=True)
    step = await account.login(login)
    while isinstance(step, ov.LoginStep.NEEDS_TOTP):  # two-factor authentication is on
        step = await account.submit_totp(step.challenge, ask_for_code())


# Unlocking and locking
async def lock_and_unlock(account: ov.Account, password: bytes) -> None:
    account.lock()  # wipes the keys from memory; the session stays
    if account.is_signed_in() and not account.is_unlocked():
        await account.unlock(password, None)


async def sign_out(account: ov.Account, forget_secret_key: bool) -> None:
    # False ends the session on the server and forgets it here; True also forgets the trusted Secret Key
    await account.sign_out(forget_secret_key)


# Staying unlocked across a restart
async def stay_unlocked(account: ov.Account, reloaded: ov.Account) -> None:
    secret = account.unlocked_keyset_secret()  # keep it in the OS keychain, never on disk in the clear
    # after a restart, on a connected (signed-in, locked) account
    await reloaded.resume_unlocked(secret)


async def watch_for_sign_out(account: ov.Account) -> None:
    reason = await account.signed_out()  # waits: SESSION_EXPIRED, TOKEN_REUSED, UNAUTHORIZED, LOGOUT, ...
    print("Signed out:", reason)


# The account itself
def show_account(account: ov.Account) -> None:
    print("email:", account.email())
    print("user id:", account.user_id())
    print("fingerprint:", account.fingerprint())  # this account's public key fingerprint, for others to compare


async def change_password(account: ov.Account, current: bytes, new: bytes) -> None:
    await account.change_password(current, new, None)  # signs the other devices out


async def change_email(account: ov.Account, new_email: str, password: bytes) -> None:
    await account.request_email_change(new_email)  # mails a code to the new address
    code = input(f"Code sent to {new_email}: ").strip()
    await account.change_email(new_email, code, password)


async def account_website_link(account: ov.Account) -> str:
    return (await account.web_session_url("/settings")).decode()  # a one-time link (60 s)


# Devices
async def list_devices(account: ov.Account) -> None:
    for d in await account.devices():  # name, platform, last_seen_at, current, ...
        print(d.name, d.platform, d.last_seen_at, "(this device)" if d.current else "")


async def revoke_device(account: ov.Account, name: str) -> None:
    devices = await account.devices()
    old = next((d for d in devices if not d.current and d.name == name), None)
    if old:
        await account.revoke_device(old.id)


# Deleting the account
async def delete_account(account: ov.Account, password: bytes, typed_email: str, heir: str | None) -> None:
    preview = await account.deletion_preview()
    print("would be erased on", preview.erase_on)
    print("vaults:", [(v.name, v.shared_with) for v in preview.vaults])  # shared vaults can be given away first
    print("orgs:", [(o.name, o.outcome) for o in preview.orgs])  # leave, delete or blocked
    if heir and preview.vaults and preview.vaults[0].shared_with:
        await account.transfer_vault(preview.vaults[0].id, heir)

    scheduled_for = await account.delete_account(password, typed_email)
    print("scheduled for", scheduled_for)
    # This device is signed out and its offline cache is gone. The Secret Key stays, so after signing in again:
    if account.deletion_scheduled_for():
        await account.restore_account(password)


async def main() -> None:
    password = env("OV_PASSWORD").encode()
    account = await connect()
    secret_key = env("OV_SECRET_KEY").encode()
    await sign_in(account, env("OV_EMAIL"), password, secret_key)
    show_account(account)
    await list_devices(account)
    await lock_and_unlock(account, password)
    await sign_out(account, False)


if __name__ == "__main__":
    asyncio.run(main())
