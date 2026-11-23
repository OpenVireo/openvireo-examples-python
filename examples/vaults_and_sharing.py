"""Vaults: listing and opening, reading and writing fields, editing entries, creating, sharing,
revoking and organisations.

Guide: https://developer.openvireo.com/sdk/guides/vaults-and-sharing/

Running it signs in, lists the vaults and the entries of the first one, and reads a field if you
pass an ov:// reference. Nothing is written unless you pass --write, which adds an "OpenVireo
example" entry to the first vault you can write to. The sharing and organisation functions are here
to read and copy; main() doesn't call them.

    python examples/vaults_and_sharing.py ["ov://Vault/Entry/field"] [--write]
"""

from __future__ import annotations

import asyncio
import sys

import openvireo as ov

from _common import make_client, sign_in


# Listing and opening
async def list_and_open(account: ov.Account) -> ov.Vault | None:
    vaults = await account.vaults()  # VaultInfo: id, name, role (VaultRole.READ, WRITE, MANAGE), org_id, ...
    for info in vaults:
        print(f"{info.name}  {info.role}  {info.id}")
    if not vaults:
        return None

    vault = await account.open_vault(vaults[0].id)  # downloads and decrypts it
    print("Entries in", vault.name(), "at", vault.etag())  # the server version this copy is based on
    for e in vault.entries(False):  # EntrySummary records; vault.entry(id) gives the full record
        print(" ", e.title)
    return vault


# Reading and writing fields
async def read_and_write(vault: ov.Vault, key: bytes) -> None:
    print(vault.read_field("ov://Team/GitHub/password").decode())

    await vault.write_field("ov://Team/GitHub/password", b"new value", False)  # edits and syncs
    await vault.write_field("ov://Team/Apps/Stripe/api_key", key, True)  # creates the entry if needed


# Editing the database directly
async def edit_entries(vault: ov.Vault) -> None:
    vault.add_entry(vault.root_group_id(), ov.EntryInput(
        fields=[
            ov.FieldInput(name="Title", value=b"OpenVireo example", protected=None),
            ov.FieldInput(name="UserName", value=b"app", protected=None),
            ov.FieldInput(name="Password", value=b"s3cret", protected=None),
        ],
        remove_fields=[], tags=None, icon_id=None, expiry=ov.EntryExpiry.KEEP(),
    ))
    vault.set_fields(f"ov://{vault.name()}/OpenVireo example", [
        ov.FieldInput(name="UserName", value=b"svc", protected=None),
        ov.FieldInput(name="token", value=b"...", protected=True),
    ], ov.CreateMode.CREATE_IF_MISSING)

    result = await vault.sync(ov.SyncOptions(local_changed=True))
    print(result.outcome)  # SyncOutcome.UPLOADED, PULLED (only downloaded), CREATED or UNCHANGED
    print(result.conflicts)  # entries both sides changed
    print(result.changes)  # what the merge did, entry by entry


# Creating vaults
async def create_vaults(account: ov.Account, org_id: str) -> None:
    await account.create_vault("Personal", None)
    await account.create_vault("Team Infra", org_id)  # org owners and admins get manage automatically


# Sharing
async def share_by_email(account: ov.Account, vault_id: str) -> None:
    grant = await account.share_vault(vault_id, ov.Grantee.EMAIL("bob@example.com"), ov.VaultRole.WRITE)
    await confirm_with_bob(grant.fingerprint)  # compare it with what Bob's app shows, out of band

    await account.change_role(vault_id, grant.principal, ov.VaultRole.READ)  # changing the role


async def share_with_verified_keys(account: ov.Account, vault_id: str) -> None:
    bob = await account.look_up("bob@example.com")
    if not ov.verify_public_keys(bob.public_keys):
        raise RuntimeError("Bob's keys don't verify")
    await confirm_with_bob(bob.public_keys.fingerprint)
    await account.share_vault_with_keys(vault_id, ov.Grantee.PRINCIPAL(bob.principal), ov.VaultRole.WRITE, bob.public_keys)


async def confirm_with_bob(fingerprint: str) -> None:
    answer = input(f"Does Bob's app show {fingerprint}? [y/N] ")
    if answer.strip().lower() != "y":
        raise RuntimeError("fingerprint not confirmed")


# Revoking and rotating
async def revoke_and_rotate(account: ov.Account, vault_id: str, bob_principal: str) -> None:
    await account.revoke(vault_id, [bob_principal])  # removes access and rotates the vault key in one step
    await account.rotate_vault_key(vault_id, [])  # a new key without removing anyone


# Organisations
async def organisations(account: ov.Account, vault_id: str) -> None:
    org = await account.create_org("Acme")
    await account.invite(org.id, "carol@example.com", ov.OrgRole.MEMBER)
    # Carol gets an email, and her app calls account.accept_invitation(invitation_token)

    members = await account.org_members(org.id)
    carol = next(m for m in members if m.email == "carol@example.com" and m.status == ov.MemberStatus.ACCEPTED)
    await account.confirm_member(org.id, carol, [ov.VaultGrantRequest(vault_id=vault_id, role=ov.VaultRole.READ)])

    await account.set_member_role(org.id, carol, ov.OrgRole.ADMIN)  # admins get manage on every org vault
    report = await account.remove_member(org.id, carol.user_id)  # and rotates her vaults
    print("rotated:", report.rotated, "failed:", report.failed)


async def main(args: list[str]) -> None:
    account = await sign_in(make_client())
    try:
        vault = await list_and_open(account)
        refs = [a for a in args if a.startswith("ov://")]
        if vault and refs:
            print(refs[0], "=", vault.read_field(refs[0]).decode())
        if "--write" in args:
            infos = [v for v in await account.vaults() if v.role != ov.VaultRole.READ]
            if infos:
                await edit_entries(await account.open_vault(infos[0].id))
    finally:
        await account.sign_out(False)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
