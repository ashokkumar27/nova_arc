from __future__ import annotations

from dataclasses import dataclass

from nova_arc.adapters.perception.runtime_perception import RuntimePerceptionAdapter
from nova_arc.adapters.planning.runtime_planner import RuntimePlannerAdapter
from nova_arc.adapters.surfaces.streamlit_surface import StreamlitSurfaceAdapter
from nova_arc.backend.client import BackendClient
from nova_arc.backend.service import CommandCenterBackend
from nova_arc.bridges.router import BridgeRouter, build_bridge_router
from nova_arc.config import AppConfig
from nova_arc.core.harness import MissionHarness
from nova_arc.core.pack_loader import PackLoader
from nova_arc.tools.factory import build_registry


@dataclass
class RuntimeBundle:
    config: AppConfig
    backend_client: BackendClient
    bridges: BridgeRouter
    harness: MissionHarness
    profile: object


def build_backend_client(config: AppConfig, service: CommandCenterBackend | None = None, use_http: bool = True) -> BackendClient:
    if service is not None:
        return BackendClient(service=service)
    if use_http:
        return BackendClient(backend_url=config.backend_url)
    return BackendClient(service=CommandCenterBackend(db_path=config.backend_db_path))


def build_runtime_bundle(
    pack_id: str,
    mode: str,
    config: AppConfig | None = None,
    backend_client: BackendClient | None = None,
    service: CommandCenterBackend | None = None,
    use_http_backend: bool = True,
) -> RuntimeBundle:
    config = config or AppConfig.from_env()
    backend_client = backend_client or build_backend_client(config=config, service=service, use_http=use_http_backend)
    profile = PackLoader("nova_arc/packs").load(pack_id)
    bridges = build_bridge_router(mode=mode, config=config, backend_client=backend_client)
    harness = MissionHarness(
        profile=profile,
        perception_adapter=RuntimePerceptionAdapter(bridges.retrieval, backend_client=backend_client, voice_bridge=bridges.voice),
        planner_adapter=RuntimePlannerAdapter(bridges.planner),
        tool_registry=build_registry(
            backend_client=backend_client,
            pack_id=pack_id,
            config=config,
            browser_bridge=bridges.browser,
            retrieval_bridge=bridges.retrieval,
        ),
        surface_adapter=StreamlitSurfaceAdapter(),
        auto_approve=True,
    )
    return RuntimeBundle(config=config, backend_client=backend_client, bridges=bridges, harness=harness, profile=profile)


def run_mission(
    pack_id: str,
    scenario: str,
    transcript: str,
    context: str,
    mode: str,
    config: AppConfig | None = None,
    backend_client: BackendClient | None = None,
    service: CommandCenterBackend | None = None,
    use_http_backend: bool = True,
    reset_backend: bool = False,
):
    bundle = build_runtime_bundle(
        pack_id=pack_id,
        mode=mode,
        config=config,
        backend_client=backend_client,
        service=service,
        use_http_backend=use_http_backend,
    )
    bundle.backend_client.bootstrap(reset=reset_backend, pack_id=pack_id)
    output = bundle.harness.run(
        {
            "scenario": scenario,
            "context": context,
            "transcript": transcript,
            "input_type": "voice",
        }
    )
    output["debug"] = {
        "planner_usage": getattr(bundle.harness.planner, "last_usage", {}) or {},
        "planner_raw_output": getattr(bundle.harness.planner, "last_raw_output", None),
        "planner_error": getattr(bundle.harness.planner, "last_error", None),
        "planner_request": getattr(bundle.harness.planner, "last_request", {}),
        "voice_response": getattr(bundle.harness.perception, "last_voice_response", {}),
        "retrieval_response": getattr(bundle.harness.perception, "last_retrieval_response", {}),
    }
    output["bridge_health"] = bundle.bridges.health()
    output["runtime_mode"] = mode
    output["runtime"] = {
        "planner_model_id": getattr(bundle.bridges.planner, "model_id", "demo"),
        "voice_model_id": getattr(bundle.bridges.voice, "model_id", "demo"),
        "embeddings_model_id": getattr(bundle.bridges.retrieval, "model_id", "demo"),
    }
    output["backend_health"] = bundle.backend_client.health()
    return output
