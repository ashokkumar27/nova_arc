from __future__ import annotations

from dataclasses import dataclass

from nova_arc.config import AppConfig

from .bedrock_bridge import BedrockConverseBridge
from .embedding_bridge import MultimodalEmbeddingBridge
from .nova_act_bridge import NovaActBridge
from .sonic_bridge import NovaSonicBridge


@dataclass
class BridgeRouter:
    planner: object
    retrieval: object
    voice: object
    browser: object

    def health(self) -> dict:
        return {
            "planner": self.planner.health(),
            "retrieval": self.retrieval.health(),
            "voice": self.voice.health(),
            "browser": self.browser.health(),
        }


def build_bridge_router(mode: str = "demo", config: AppConfig | None = None, backend_client=None) -> BridgeRouter:
    config = config or AppConfig.from_env()
    planner_live = mode in {"live_bedrock", "live_bridge"}
    voice_live = mode == "live_bridge"
    return BridgeRouter(
        planner=BedrockConverseBridge(config=config, enabled=planner_live),
        retrieval=MultimodalEmbeddingBridge(
            backend_client=backend_client,
            config=config,
            enabled=planner_live and config.enable_live_embeddings,
        ),
        voice=NovaSonicBridge(config=config, enabled=voice_live),
        browser=NovaActBridge(backend_client=backend_client, config=config),
    )
