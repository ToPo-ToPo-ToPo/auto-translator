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
    hf_repo="ToPo-ToPo/gemma-4-E4B-it-qat-mlx-4bit",
    env_var="AUTO_TRANSLATE_MLX_E4B_MODEL",
    size_gb=5.0,
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
