"""Reaches the account server without signing in: a quick test that the binding loads and the
network works.

    python examples/check.py
"""

import asyncio

from _common import ISSUER, make_client


async def main() -> None:
    account = await make_client().connect(ISSUER)
    print(f"Connected to {ISSUER} (API {account.server_config().api}); signed in: {account.is_signed_in()}")


if __name__ == "__main__":
    asyncio.run(main())
