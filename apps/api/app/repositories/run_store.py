from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.repositories.db import SessionLocal
from app.repositories.models import AnalysisRunRecord, EvalRunRecord


class RunStore:
    def save_analysis_run(self, *, run_id: str, trace_id: str, ruleset_version: str, corpus_version: str, input_schema_version: str, payload: dict) -> None:
        with SessionLocal() as session:
            session.add(
                AnalysisRunRecord(
                    run_id=run_id,
                    ruleset_version=ruleset_version,
                    corpus_version=corpus_version,
                    input_schema_version=input_schema_version,
                    trace_id=trace_id,
                    run_payload=payload,
                )
            )
            session.commit()

    def get_analysis_run(self, run_id: str) -> dict | None:
        with SessionLocal() as session:
            record = session.execute(select(AnalysisRunRecord).where(AnalysisRunRecord.run_id == run_id)).scalar_one_or_none()
            return record.run_payload if record else None

    def save_eval_run(self, *, eval_run_id: str, pack_id: str, layer1_payload: dict, layer2_metrics: Sequence[dict], notes: Sequence[str]) -> None:
        with SessionLocal() as session:
            session.add(
                EvalRunRecord(
                    eval_run_id=eval_run_id,
                    pack_id=pack_id,
                    layer1_payload=layer1_payload,
                    layer2_metrics=list(layer2_metrics),
                    notes=list(notes),
                )
            )
            session.commit()

    def get_eval_run(self, eval_run_id: str) -> dict | None:
        with SessionLocal() as session:
            record = session.execute(select(EvalRunRecord).where(EvalRunRecord.eval_run_id == eval_run_id)).scalar_one_or_none()
            if record is None:
                return None
            return {
                "evalRunId": record.eval_run_id,
                "packId": record.pack_id,
                "layer1": record.layer1_payload,
                "layer2Metrics": record.layer2_metrics,
                "notes": record.notes,
            }


run_store = RunStore()

