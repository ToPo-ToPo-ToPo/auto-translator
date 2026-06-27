"""MLX engine — Gemma 4 E2B (Apple Silicon, via mlx-vlm). See _mlx_common.py.

Build the local model once:  uv run python tools/build_mlx_model.py e2b
Override the location/model:  AUTO_TRANSLATE_MLX_MODEL (local path or HF repo id)
"""

from engines._mlx_common import MlxModel

_engine = MlxModel(
    name="mlx",
    label="Gemma 4 E2B (MLX)",
    subdir="gemma-4-E2B-it-qat-mlx-4bit",
    env_var="AUTO_TRANSLATE_MLX_MODEL",
    build_arg="e2b",
)

NAME = _engine.NAME
LABEL = _engine.LABEL
DEFAULT_MODEL = _engine.DEFAULT_MODEL
is_available = _engine.is_available
unavailable_reason = _engine.unavailable_reason
translate = _engine.translate
