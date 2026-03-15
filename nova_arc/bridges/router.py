from __future__ import annotations

from dataclasses import dataclass

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


def build_bridge_router(mode: str = "demo", enable_bedrock: bool = False) -> BridgeRouter:
    return BridgeRouter(
        planner=BedrockConverseBridge(enabled=enable_bedrock and mode != "demo"),
        retrieval=MultimodalEmbeddingBridge(),
        voice=NovaSonicBridge(),
        browser=NovaActBridge(),
    )
