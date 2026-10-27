"""Fetch only the England files from a pinned, checksummed public Wyscout mirror."""

import argparse
from hashlib import sha256
import io
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile


SNAPSHOT = "ebc4c54c1093c420a81ce442c69e4186fab33bb4"
BASE_URL = f"https://raw.githubusercontent.com/koenvo/wyscout-soccer-match-event-dataset/{SNAPSHOT}/raw_data"
FILES = {
    "events": ("877e015b716ffdeea18f04418e3f24fed307ed03c37ff305cabe1f47c4822a45",
               "301599543aa1a7fa457bb8ef33c9fe860bf81dca65d418d618d68abcda3defad"),
    "matches": ("c8f92bb7533e5c127e043cee764c991b5c25b4f5e70a65be931baae0b1765ce9",
                "620725c2e6a58b4db3e574ed6c559136477451d81af543f8a06bd85c3da3fe29"),
}


def extract_england(archive: bytes, kind: str) -> bytes:
    archive_hash, file_hash = FILES[kind]
    if sha256(archive).hexdigest() != archive_hash:
        raise ValueError(f"{kind}: archive checksum mismatch")
    name = f"{kind}_England.json"
    with ZipFile(io.BytesIO(archive)) as zipped:
        members = [member for member in zipped.namelist() if member.split("/")[-1] == name]
        if len(members) != 1:
            raise ValueError(f"{kind}: expected one England file")
        contents = zipped.read(members[0])
    if sha256(contents).hexdigest() != file_hash:
        raise ValueError(f"{kind}: extracted checksum mismatch")
    return contents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    # Both archives together are about 78 MB; no paid API or credentials needed.
    targets = {kind: args.directory / f"{kind}_England.json" for kind in FILES}
    if any(path.exists() for path in targets.values()):
        parser.error("target exists; use a new directory")
    contents = {}
    for kind in FILES:
        with urlopen(f"{BASE_URL}/{kind}.zip", timeout=120) as response:
            contents[kind] = extract_england(response.read(), kind)
    args.directory.mkdir(parents=True, exist_ok=True)
    for kind, path in targets.items():
        with path.open("xb") as output:
            output.write(contents[kind])
    print(f"Downloaded EPL 2017/18 to {args.directory}. Data: Wyscout / Pappalardo & Massucco, CC BY 4.0.")


if __name__ == "__main__":
    main()
