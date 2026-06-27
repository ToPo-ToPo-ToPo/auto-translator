#!/usr/bin/env python3
"""Build a local MLX model used by the MLX engines (Apple Silicon only).

Converts the official Gemma 4 QAT weights to MLX 4-bit with mlx-vlm 0.6.3 (the
same version the app loads with — convert/load must match) and stores it where
the MLX engine looks for it. Models are kept local; nothing is uploaded.

    uv run python tools/build_mlx_model.py e2b   # default, ~9.5 GB -> ~3.3 GB
    uv run python tools/build_mlx_model.py e4b   # higher quality, ~16 GB -> ~5 GB
    uv run python tools/build_mlx_model.py all

Override the source/destination with AUTO_TRANSLATE_MLX_SRC / the engine's model
env var.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engines.mlx_engine import DEFAULT_MODEL as E2B_OUT       # noqa: E402
from engines.mlx_e4b_engine import DEFAULT_MODEL as E4B_OUT   # noqa: E402

VARIANTS = {
    "e2b": ("google/gemma-4-E2B-it-qat-q4_0-unquantized", E2B_OUT, "~9.5 GB"),
    "e4b": ("google/gemma-4-E4B-it-qat-q4_0-unquantized", E4B_OUT, "~16 GB"),
}


def build(src, out, dl):
    if os.path.isdir(out) and os.path.exists(os.path.join(out, "config.json")):
        print(f"Already built: {out}")
        return
    os.makedirs(os.path.dirname(out), exist_ok=True)
    from mlx_vlm.convert import convert

    print(f"Converting {src}\n        -> {out}  (MLX 4-bit, group_size=64)")
    print(f"Downloading {dl} on first run; this takes a few minutes…")
    convert(
        hf_path=src, mlx_path=out, quantize=True, q_bits=4, q_group_size=64,
        dtype="bfloat16", trust_remote_code=True,
    )
    print(f"Done: {out}")


def main():
    which = (sys.argv[1] if len(sys.argv) > 1 else "e2b").lower()
    targets = list(VARIANTS) if which == "all" else [which]
    if any(t not in VARIANTS for t in targets):
        sys.exit("usage: build_mlx_model.py [e2b|e4b|all]")
    src_override = os.environ.get("AUTO_TRANSLATE_MLX_SRC")
    for t in targets:
        src, out, dl = VARIANTS[t]
        build(src_override or src, out, dl)
    print("Done. Launch the app and pick the MLX engine in the menu.")


if __name__ == "__main__":
    main()
