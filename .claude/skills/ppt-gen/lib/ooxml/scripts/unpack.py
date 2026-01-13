#!/usr/bin/env python3
"""Unpack and format XML contents of Office files (.docx, .pptx, .xlsx)"""

import random
import sys
import defusedxml.minidom
import zipfile
from pathlib import Path


def unpack_office_file(input_file, output_dir):
    """Extract and format Office file to directory.

    Args:
        input_file: Path to Office file (.docx/.pptx/.xlsx)
        output_dir: Path to output directory

    Returns:
        For .docx files, returns a suggested RSID for tracked changes.
        For other files, returns None.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(input_file).extractall(output_path)

    # Pretty print all XML files
    xml_files = list(output_path.rglob("*.xml")) + list(output_path.rglob("*.rels"))
    for xml_file in xml_files:
        content = xml_file.read_text(encoding="utf-8")
        dom = defusedxml.minidom.parseString(content)
        xml_file.write_bytes(dom.toprettyxml(indent="  ", encoding="ascii"))

    # For .docx files, suggest an RSID for tracked changes
    if str(input_file).endswith(".docx"):
        suggested_rsid = "".join(random.choices("0123456789ABCDEF", k=8))
        return suggested_rsid
    return None


# CLI 호환성 유지
if __name__ == "__main__":
    assert len(sys.argv) == 3, "Usage: python unpack.py <office_file> <output_dir>"
    input_file, output_dir = sys.argv[1], sys.argv[2]
    rsid = unpack_office_file(input_file, output_dir)
    if rsid:
        print(f"Suggested RSID for edit session: {rsid}")
