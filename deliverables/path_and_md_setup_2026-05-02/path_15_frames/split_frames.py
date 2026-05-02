#!/usr/bin/env python3
"""Split path_seqaligned.pdb (15-MODEL multi-frame PDB) into 15 single-model files.

Produces frames/frame_01.pdb through frames/frame_15.pdb, each a standalone PDB
that PyMOL / ChimeraX / VMD can open directly.

Usage:
    cd path_15_frames/
    python3 split_frames.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "path_seqaligned.pdb"
OUT = HERE / "frames"
OUT.mkdir(exist_ok=True)


def main() -> None:
    text = SRC.read_text()
    blocks: list[list[str]] = []
    cur: list[str] = []
    in_model = False
    for line in text.splitlines():
        if line.startswith("MODEL"):
            in_model = True
            cur = [line]
        elif line.startswith("ENDMDL"):
            cur.append(line)
            blocks.append(cur)
            in_model = False
        elif in_model:
            cur.append(line)
    assert len(blocks) == 15, f"expected 15 frames, got {len(blocks)}"

    for i, blk in enumerate(blocks, start=1):
        f = OUT / f"frame_{i:02d}.pdb"
        with open(f, "w") as fh:
            fh.write(f"REMARK   1 Frame {i:02d}/15 of TrpB O->C PATHMSD reference path.\n")
            fh.write("REMARK   1 Source: build_seqaligned_path.py 2026-04-23 sequence-aligned.\n")
            fh.write("REMARK   1 112 Calpha (88 COMM 97-184 + 24 base 282-305 in 1WDW numbering).\n")
            fh.write("REMARK   1 Frame 01 = O endpoint (1WDW-B Pf).\n")
            fh.write("REMARK   1 Frame 15 = C endpoint (3CEP-B St, Kabsch-aligned to 1WDW).\n")
            fh.write("REMARK   1 Frames 02-14 = linear interpolation between aligned O and C.\n")
            fh.write("REMARK   1 ALA placeholder residue: PATHMSD only uses Calpha coordinates.\n")
            fh.write("\n".join(blk) + "\n")
            fh.write("END\n")
        print(f"wrote {f.name}")


if __name__ == "__main__":
    main()
