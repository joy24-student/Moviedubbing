from __future__ import annotations

import hashlib

from aidub.adapters.diarization_pyannote import SpeakerDiarizationResult
from aidub.contracts.jobs import JobDescriptor
from aidub.domain.time import AudioSamplePosition, AudioSampleRange
from aidub.workers.supervisor import LocalWorkerSupervisor


def make_diarize_job(job_id: str) -> JobDescriptor:
    audio_range = AudioSampleRange(
        start=AudioSamplePosition(sample_index=0, sample_rate=48_000),
        sample_count=96_000,
    )
    return JobDescriptor(
        job_id=job_id,
        idempotency_key=hashlib.sha256(job_id.encode()).hexdigest(),
        project_id="prj_diar_worker",
        job_type="speech.diarize",
        parameters={
            "audio_range": audio_range.model_dump(mode="json"),
            "source_audio_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "options": {"device": "cpu"},
        },
    )


def test_diarization_worker_executes_speech_diarize_job() -> None:
    with LocalWorkerSupervisor() as supervisor:
        job = make_diarize_job("job_diar_001")
        supervisor.submit(job)
        result = supervisor.wait(timeout_seconds=10.0)

        assert result.succeeded
        assert "result_json" in result.metrics
        diar_result = SpeakerDiarizationResult.model_validate_json(
            str(result.metrics["result_json"])
        )
        assert diar_result.engine.engine_id == "pyannote-diarization"
        assert len(diar_result.segments) > 0
