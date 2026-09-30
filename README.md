# Fixture Builder

Home Assistant add-on that turns a DMX control table (PDF or photo) into dmXLAN fixture syntax.

Upload a table, preview the generated `.txt`, download it, or append it to the fixture library on HA.

## Local test (Mac)

```bash
cp .env.example .env
# put your OpenAI key in .env

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q

docker compose up --build
```

Open [http://127.0.0.1:8099](http://127.0.0.1:8099). The compose file mounts `../Fixture Library` as `/library`.

## Install on Home Assistant

1. Copy the add-on onto the HA machine:

```bash
./scripts/pack-ha-addon.sh --scp
```

Or manually:

```bash
scp -r "/Users/niels/Documents/dmXLAN Files/fixture-builder" root@homeassistant.local:/addons/fixture_builder
```

2. In Home Assistant: **Settings → Add-ons → Add-on Store → ⋮ → Reload**.
3. Open the local add-on **Fixture Builder**, set `openai_api_key`, and optionally point `library_path` at `/share/dmxlan`.
4. Copy your manufacturer `.txt` files into `/share/dmxlan` (Samba/share) if you want append-to-library.
5. Start the add-on. It appears in the sidebar.

dmXLAN does not auto-reload the library. After writing a file, copy it into the folder dmXLAN actually reads.

## Syntax rules the tool enforces

- `range = start, end, label` always has two DMX numbers
- Labels that start with a digit are quoted: `range = 0, 255, "7200K - 3200K"`
- Fine channels use `option = skip`
- Preview must validate before the library is written
