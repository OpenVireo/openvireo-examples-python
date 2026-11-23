# OpenVireo examples: Python

Runnable examples for the [OpenVireo](https://openvireo.com) Python binding (`openvireo`), one file per
guide on [developer.openvireo.com](https://developer.openvireo.com). Each file holds the code from its
guide's **Python** tab, wrapped in a program you can run.

Examples in other languages: [TypeScript](https://github.com/openvireo/openvireo-examples-typescript) · [Kotlin](https://github.com/openvireo/openvireo-examples-kotlin) · [Java](https://github.com/openvireo/openvireo-examples-java) · [Swift](https://github.com/openvireo/openvireo-examples-swift) · [C++](https://github.com/openvireo/openvireo-examples-cpp) · [ov CLI](https://github.com/openvireo/openvireo-examples-cli)

## Run them

You need Python 3.10 or newer and [uv](https://docs.astral.sh/uv/). `uv sync` installs `openvireo`
1.1.0 from the wheels on the [core release](https://github.com/openvireo/openvireo-core/releases/tag/v1.1.0)
(it isn't on PyPI yet).

```sh
git clone https://github.com/openvireo/openvireo-examples-python
cd openvireo-examples-python
uv sync
uv run examples/check.py
```

Set your account in the environment. `OV_SECRET_KEY` is only needed the first time on a device;
`OV_ISSUER` picks an account server other than `https://accounts.openvireo.com`.

```sh
export OV_EMAIL=you@example.com OV_PASSWORD='...' OV_SECRET_KEY='A3-...'
```

```sh
uv run examples/first_program.py "ov://Personal/GitHub/username"
uv run examples/vaults_and_sharing.py
```

With pip instead of uv:

```sh
pip install "openvireo[keyring]==1.1.0" \
  --find-links https://github.com/openvireo/openvireo-core/releases/expanded_assets/v1.1.0
python examples/first_program.py
```

## The examples

| Example | What it does | Guide |
|---|---|---|
| [`first_program.py`](examples/first_program.py) | Sign in, list the vaults, read one field, sign out | [A first program](https://developer.openvireo.com/sdk/#a-first-program) |
| [`hosted_account.py`](examples/hosted_account.py) | Connect, sign up, sign in with two-step codes, lock, devices, account deletion | [Hosted accounts](https://developer.openvireo.com/sdk/guides/hosted-account/) |
| [`vaults_and_sharing.py`](examples/vaults_and_sharing.py) | List, open, read, write and edit vaults; share, revoke, organisations | [Vaults and sharing](https://developer.openvireo.com/sdk/guides/vaults-and-sharing/) |
| [`events.py`](examples/events.py) | Follow live changes from other devices | [Events](https://developer.openvireo.com/sdk/guides/events/) |
| [`offline.py`](examples/offline.py) | Edit offline, merge when back online | [Offline](https://developer.openvireo.com/sdk/guides/offline/) |
| [`move_to_account.py`](examples/move_to_account.py) | Import a `.kdbx` file as a new vault or merge it into one | [Moving to an account](https://developer.openvireo.com/sdk/guides/move-to-account/) |
| [`recovery.py`](examples/recovery.py) | Inspect a recovery link, reset, restore the old vaults | [Recovery](https://developer.openvireo.com/sdk/guides/recovery/) |
| [`self_hosted_sync.py`](examples/self_hosted_sync.py) | Pair with a self-hosted sync server and sync a `.kdbx` file | [Self-hosted sync](https://developer.openvireo.com/sdk/guides/self-hosted-sync/) |
| [`service_accounts.py`](examples/service_accounts.py) | Create a service account; read, inject and write with its token | [Service accounts](https://developer.openvireo.com/sdk/guides/service-accounts/) |
| [`share_links.py`](examples/share_links.py) | Share an item or text by link, list and revoke links, open one | [Share links](https://developer.openvireo.com/sdk/guides/share-links/) |

Each file has one function per section of its guide. Running an example does something safe and
mostly read-only; the functions that change an account for good (deleting it, revoking access,
rotating keys) are there to read and copy, and the programs don't call them. Try the rest on a test
account. `check` reaches the account server without signing in, to test the setup.

## Checks

CI type-checks every example against the binding's stubs with pyright and imports each file, on
Linux and macOS, on every push and weekly:

```sh
uv run pyright
```

## License

MIT. Copy the code into your own programs.
