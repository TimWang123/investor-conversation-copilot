from __future__ import annotations

from app.services.llm_gateway import build_llm_gateway


def test_build_llm_gateway_supports_qwen_provider() -> None:
    gateway = build_llm_gateway(
        provider="qwen",
        moonshot_api_key="",
        moonshot_base_url="https://api.moonshot.cn/v1",
        moonshot_model="kimi-latest",
        qwen_api_key="test-qwen-key",
        qwen_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        qwen_model="qwen-plus",
    )

    assert gateway is not None
    status = gateway.status()
    assert status["provider"] == "qwen"
    assert status["enabled"] is True
    assert status["model"] == "qwen-plus"
