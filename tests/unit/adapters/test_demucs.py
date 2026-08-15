from __future__ import annotations

from pathlib import Path

import pytest

from aidub.adapters.separation_demucs import (
    DemucsSeparationAdapter,
    DemucsSeparationOptions,
    StemKind,
)


def test_demucs_options_validation() -> None:
    options = DemucsSeparationOptions(
        model_name="htdemucs",
        device="cpu",
        shifts=2,
    )
    assert options.device == "cpu"
    assert options.shifts == 2

    with pytest.raises(ValueError, match="unsupported device"):
        DemucsSeparationOptions(device="npu")


def test_demucs_adapter_synthetic_separation(tmp_path: Path) -> None:
    adapter = DemucsSeparationAdapter(DemucsSeparationOptions(device="cpu"))
    out_dir = tmp_path / "stems"

    result = adapter.separate("dummy_input.wav", str(out_dir))

    assert result.engine.engine_id == "demucs-separation"
    assert len(result.stems) == 4
    assert result.me_preserved is True

    dialogue_stem = result.get_stem(StemKind.DIALOGUE)
    assert dialogue_stem is not None
    assert Path(dialogue_stem.stem_path).exists()
