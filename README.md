# Fixture Builder

Home Assistant add-on that turns a DMX control table (PDF or photo) into dmXLAN fixture syntax.

Upload a table, preview the generated `.txt`, download it, or append it to the fixture library on HA.

## Install from GitHub (recommended)

1. In Home Assistant: **Settings → Add-ons → Add-on Store → ⋮ → Repositories**
2. Add:

```text
https://github.com/NielsDimmen/fixture-builder
```

3. Reload the store, open **Fixture Builder**, set `openai_api_key`, start the add-on.
4. Optional: copy manufacturer `.txt` files into `/share/dmxlan` if you want append-to-library.

This repository is a valid Home Assistant app repository (`repository.yaml` + `fixture_builder/` add-on folder).

## Local install without GitHub

```bash
./scripts/pack-ha-addon.sh --scp
```

Then reload the Add-on Store and install the local **Fixture Builder**.

## Local test on Mac

```bash
cp .env.example .env
# put your OpenAI key in .env

python3 -m venv .venv
source .venv/bin/activate
pip install -r fixture_builder/requirements.txt pytest
pytest -q

docker compose up --build
```

Open [http://127.0.0.1:8099](http://127.0.0.1:8099). Compose mounts `../Fixture Library` as `/library`.

dmXLAN does not auto-reload the library. After writing a file, copy it into the folder dmXLAN actually reads.

## Syntax rules the tool enforces

- `range = start, end, label` always has two DMX numbers
- Labels that start with a digit are quoted: `range = 0, 255, "7200K - 3200K"`
- Fine channels use `option = skip`
- Preview must validate before the library is written
