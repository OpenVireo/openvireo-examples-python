"""Share links: share one item, or some text, through a link that needs no account; list and revoke
links; open one.

Guide: https://developer.openvireo.com/sdk/guides/share-links/

    python examples/share_links.py list
    python examples/share_links.py text "The alarm code is 4321"
    python examples/share_links.py open "https://share.openvireo.com/<id>#<key>"
"""

from __future__ import annotations

import asyncio
import sys
import time

import openvireo as ov

from _common import make_client, sign_in


# Making a link
async def share_entry(account: ov.Account, vault: ov.Vault, entry_id: str) -> str:
    entry = vault.entry(entry_id)
    print("can share:", [f.name for f in ov.shareable_fields(entry)])  # in display order

    payload = ov.item_share_payload(entry, ov.default_share_fields(), "Sam")  # username, password, website
    link = await account.create_share(payload, ov.ShareOptions(
        expires_in=7 * 86400,  # seconds: 1 hour to 30 days (free plans: 7 days)
        max_opens=1,  # None: until it expires
        passcode=None,
        vault_id=vault.id(),
        entry_id=entry_id,
    ))
    return link.url.decode()  # https://share.openvireo.com/<id>#<key>


async def share_text(account: ov.Account, text: str) -> str:
    link = await account.create_share(
        ov.text_share_payload(text.encode(), "From the examples", None),
        ov.ShareOptions(expires_in=3600, max_opens=None, passcode=b"tiger lily 42", vault_id=None, entry_id=None),
    )
    return link.url.decode()


# Listing and revoking
async def list_shares(account: ov.Account) -> None:
    for s in await account.list_shares():
        # s.reference has vault, entry, title, readable only by this account
        print(s.id, s.reference.title if s.reference else None, s.status, s.opens, s.max_opens, s.expires_at, s.end_reason)


async def revoke(account: ov.Account, share_id: str) -> None:
    await account.revoke_share(share_id)


async def org_policy(account: ov.Account, org_id: str) -> None:
    await account.set_org_share_links(org_id, ov.ShareLinkPolicy.MANAGERS)  # ON (default), MANAGERS or OFF


# Opening a link
async def open_link(client: ov.OvClient, api: str, link: str) -> None:
    share_id = ov.parse_share_link(link).id
    info = await client.share_info(api, share_id)  # expires_at, opens_left, kdf; doesn't count as an open
    # Show a "Reveal" button and open only when it's pressed: link previews then can't use up a one-time link.
    input(f"Opens left: {info.opens_left}. Press Enter to reveal... ")
    passcode = input("Passcode: ").encode() if info.kdf else None
    opened = await client.open_share(api, link.encode(), passcode, info)

    for f in opened.payload.fields:
        shown = ov.totp_code(ov.parse_totp_uri(f.value), int(time.time() * 1000)).code if f.k == "totp" else f.value
        # render as plain text; hide f.protected values until shown
        print(f"{f.label}: {shown}")


async def main(args: list[str]) -> None:
    client = make_client()
    account = await sign_in(client)
    try:
        if args == ["list"]:
            await list_shares(account)
        elif args[:1] == ["text"] and len(args) == 2:
            print(await share_text(account, args[1]))
            print("passcode: tiger lily 42")
        elif args[:1] == ["open"] and len(args) == 2:
            api = account.server_config().api  # or the share host's API, without an account
            await open_link(client, api, args[1])
        else:
            sys.exit(__doc__)
    finally:
        await account.sign_out(False)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
