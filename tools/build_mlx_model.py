#!/usr/bin/env python3
"""Build the local MLX model used by the MLX engine (Apple Silicon only).

Converts the official Gemma 4 E2B QAT weights to MLX 4-bit with mlx-vlm 0.6.3
(the same version the app loads with — convert/load must match) and stores it
where the MLX engine looks for it. The model is kept local; nothing is uploaded.

    uv run python tools/build_mlx_model.py

~9.5 GB is downloaded once, producing a ~3.3 GB model. Override the source or
destination with AUTO_TRANSLATE_MLX_SRC / AUTO_TRANSLATE_MLX_MODEL.
"""

import os
import sys

# Resolve the destination from the engine so both stay in sync.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engines.mlx_engine import DEFAULT_MODEL  # noqa: E402

SRC = os.environ.get(
    "AUTO_TRANSLATE_MLX_SRC", "google/gemma-4-E2B-it-qat-q4_0-unquantized"
)
OUT = os.environ.get("AUTO_TRANSLATE_MLX_MODEL", DEFAULT_MODEL)


def main():
    if os.path.isdir(OUT) and os.path.exists(os.path.join(OUT, "config.json")):
        print(f"Already built: {OUT}")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    from mlx_vlm.convert import convert

    print(f"Converting {SRC}\n        -> {OUT}  (MLX 4-bit, group_size=64)")
    print("Downloading ~9.5 GB on first run; this takes a few minutes…")
    convert(
        hf_path=SRC, mlx_path=OUT, quantize=True, q_bits=4, q_group_size=64,
        dtype="bfloat16", trust_remote_code=True,
    )
    print("Done. Launch the app and pick 'Gemma 4 E2B (MLX)' in the engine menu.")


if __name__ == "__main__":
    main()
