"""Download immutable KiCad sources into an ignored cache and verify their hashes."""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

root = Path(__file__).resolve().parents[1]
cache = root / ".source-cache"
cache.mkdir(exist_ok=True)
manifest = json.loads((root / "manifest.json").read_text())
for sample in manifest["samples"]:
    source = json.loads((root / sample["provenance"]).read_text())
    files = [(source["path"], source["sourceSha256"], "kicad_pcb")]
    if "projectSource" in source:
        project = source["projectSource"]
        files.append((project["path"], project["sha256"], "kicad_pro"))
    for path, expected, suffix in files:
        target = cache / f"{source['id']}.{suffix}"
        if target.exists():
            raw = target.read_bytes()
        else:
            url = f"https://raw.githubusercontent.com/{source['repo']}/{source['commit']}/{quote(path)}"
            with urlopen(url, timeout=60) as response:
                raw = response.read()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError(f"{target.name}: source hash mismatch {actual}")
        target.write_bytes(raw)
        print(f"Verified {target.name}: {actual}")
