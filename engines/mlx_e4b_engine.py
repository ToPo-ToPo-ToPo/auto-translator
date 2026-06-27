"""MLX engine — Gemma 4 E4B (Apple Silicon, via mlx-vlm). Higher quality, more
RAM than E2B (~6 GB). See _mlx_common.py.

Build the local model once:  uv run python tools/build_mlx_model.py e4b
Override the location/model:  AUTO_TRANSLATE_MLX_E4B_MODEL (local path or HF repo id)
"""

from engines._mlx_common import MlxModel, is_applicable  # noqa: F401

_engine = MlxModel(
    name="mlx-e4b",
    label="Gemma 4 E4B (MLX)",
    subdir="gemma-4-E4B-it-qat-mlx-4bit",
    env_var="AUTO_TRANSLATE_MLX_E4B_MODEL",
    build_arg="e4b",
)

NAME = _engine.NAME
LABEL = _engine.LABEL
DEFAULT_MODEL = _engine.DEFAULT_MODEL
is_available = _engine.is_available
unavailable_reason = _engine.unavailable_reason
translate = _engine.translate
