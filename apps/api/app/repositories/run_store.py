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

    def save_analysis_run_evidence_explainability(self, *, run_id: str, evidence_id: str, payload: dict) -> dict | None:
        with SessionLocal() as session:
            record = session.execute(select(AnalysisRunRecord).where(AnalysisRunRecord.run_id == run_id)).scalar_one_or_none()
            if record is None:
                return None
            run_payload = dict(record.run_payload or {})
            explainability_by_id = dict(run_payload.get("evidenceExplainabilityById", {}))
            explainability_by_id[evidence_id] = payload
            run_payload["evidenceExplainabilityById"] = explainability_by_id
            record.run_payload = run_payload
            session.commit()
            return payload

    def save_analysis_run_uncertainty_flags_explainability(self, *, run_id: str, payload: dict) -> dict | None:
        with SessionLocal() as session:
            record = session.execute(select(AnalysisRunRecord).where(AnalysisRunRecord.run_id == run_id)).scalar_one_or_none()
            if record is None:
                return None
            run_payload = dict(record.run_payload or {})
            run_payload["uncertaintyFlagsExplainability"] = payload
            record.run_payload = run_payload
            session.commit()
            return payload

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

    def get_benchmark_cache(self, eval_run_id: str) -> dict | None:
        with SessionLocal() as session:
            record = session.execute(select(EvalRunRecord).where(EvalRunRecord.eval_run_id == eval_run_id)).scalar_one_or_none()
            if record is None:
                return None
            payload = record.layer1_payload or {}
            if payload.get("kind") != "engine_benchmark_cache":
                return None
            return payload.get("result")

    def save_benchmark_cache(self, *, eval_run_id: str, pack_id: str, payload: dict, notes: Sequence[str]) -> None:
        with SessionLocal() as session:
            existing = session.execute(select(EvalRunRecord).where(EvalRunRecord.eval_run_id == eval_run_id)).scalar_one_or_none()
            if existing is not None:
                existing.pack_id = pack_id
                existing.layer1_payload = {
                    "kind": "engine_benchmark_cache",
                    "result": payload,
                }
                existing.layer2_metrics = []
                existing.notes = list(notes)
                session.commit()
                return

            session.add(
                EvalRunRecord(
                    eval_run_id=eval_run_id,
                    pack_id=pack_id,
                    layer1_payload={
                        "kind": "engine_benchmark_cache",
                        "result": payload,
                    },
                    layer2_metrics=[],
                    notes=list(notes),
                )
            )
            session.commit()


run_store = RunStore()
