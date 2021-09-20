import json
import sys
import xml.etree.ElementTree as ET
from typing import TypedDict


class Entry(TypedDict):
    text: str
    begin: str
    end: str


def main():
    ttml_text = sys.stdin.read()

    # Normalize whitespaces
    ttml_text = ttml_text.replace("<br />", " ")
    ttml_text = ttml_text.replace("\xa0", " ")

    # Parse XML and iterate throuth <p>
    tree = ET.fromstring(ttml_text)
    entries: list[Entry] = []
    for p in tree.iter("{http://www.w3.org/ns/ttml}p"):
        entries.append(
            dict(text=p.text or "", begin=p.attrib["begin"], end=p.attrib["end"])
        )

    # Emit
    print(json.dumps(entries, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
