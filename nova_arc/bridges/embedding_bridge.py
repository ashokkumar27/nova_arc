from __future__ import annotations

from typing import Dict
import json
import math

from nova_arc.config import AppConfig

from .contracts import BridgeRequest, BridgeResponse, RuntimeBridge


class MultimodalEmbeddingBridge(RuntimeBridge):
    backend_name = "nova-multimodal-embeddings"

    def __init__(self, backend_client, config: AppConfig, enabled: bool = False):
        self.backend_client = backend_client
        self.config = config
        self.enabled = enabled
        self.model_id = config.nova_embeddings_model_id
        self._client = None
        if enabled:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "bedrock-runtime",
                region_name=config.aws_region,
                config=Config(connect_timeout=config.bedrock_timeout_seconds, read_timeout=config.bedrock_timeout_seconds, retries={"max_attempts": 1}),
            )

    def health(self) -> dict:
        detail = "local compatible retrieval active"
        if self.enabled:
            detail = "Bedrock embeddings retrieval active"
        return {
            "ok": True,
            "backend": self.backend_name,
            "detail": detail,
            "model_id": self.model_id,
        }

    def invoke(self, request: BridgeRequest) -> BridgeResponse:
        query = request.payload.get("query", {})
        query_text = query.get("content", "")
        try:
            result = self.backend_client.search_evidence(
                pack_id=request.pack_id,
                query_text=query_text,
                top_k=int(query.get("top_k", 4)),
            )
            if self.enabled and self._client is not None:
                result = self._rerank_with_bedrock(result, query_text)
            return BridgeResponse(True, self.backend_name, request.operation, result)
        except Exception as exc:
            return BridgeResponse(False, self.backend_name, request.operation, {}, error=f"{type(exc).__name__}: {exc}")

    def _embed_text(self, text: str) -> list[float]:
        body = {
            "inputText": text,
            "embeddingConfig": {"outputEmbeddingLength": 256},
        }
        response = self._client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body).encode("utf-8"),
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read())
        embeddings = payload.get("embeddingsByType", {}) or {}
        vector = embeddings.get("text")
        if not vector:
            raise ValueError("Embeddings response did not contain a text vector.")
        return vector

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)

    def _rerank_with_bedrock(self, result: Dict[str, object], query_text: str) -> Dict[str, object]:
        query_vector = self._embed_text(query_text)
        matches = result.get("matches", [])
        reranked = []
        for match in matches:
            candidate_text = " ".join(
                [
                    match.get("title", ""),
                    match.get("snippet", ""),
                    json.dumps(match.get("metadata", {}), sort_keys=True),
                ]
            )
            similarity = self._cosine_similarity(query_vector, self._embed_text(candidate_text))
            match["score"] = round(min(0.99, max(match.get("score", 0.0), 0.5 + similarity / 2)), 2)
            reranked.append(match)
        reranked.sort(key=lambda item: item["score"], reverse=True)
        result["matches"] = reranked
        result.setdefault("trace", {})["embedding_model_id"] = self.model_id
        return result
