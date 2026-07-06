"""MLX engine — Gemma 4 E2B (Apple Silicon, via mlx-vlm). See _mlx_common.py.

Build the local model once:  uv run python tools/build_mlx_model.py e2b
Override the location/model:  AUTO_TRANSLATE_MLX_MODEL (local path or HF repo id)
"""

from engines._mlx_common import MlxModel, is_applicable  # noqa: F401

_engine = MlxModel(
    name="mlx",
    label="Gemma 4 E2B (MLX)",
    subdir="gemma-4-E2B-it-qat-mlx-4bit",
    hf_repo="ToPo-ToPo/gemma-4-E2B-it-qat-mlx-4bit",
    env_var="AUTO_TRANSLATE_MLX_MODEL",
    size_gb=3.3,
)

NAME = _engine.NAME
LABEL = _engine.LABEL
LOCAL_PATH = _engine.local_path
HF_REPO = _engine.hf_repo
is_available = _engine.is_available
unavailable_reason = _engine.unavailable_reason
pending_download = _engine.pending_download
translate = _engine.translate
alternatives = _engine.alternatives
rephrase = _engine.rephrase
unload = _engine.unload
