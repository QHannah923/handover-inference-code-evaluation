# 2026-11-20：Sol high保持不变；采用用户确认的语义、菜单矛盾和免费扩展定义。
PROFILE = "verified_failure_fallback"
MODEL_NAME = "gpt-6.1-sol"
REASONING_EFFORT = "high"
MODEL_WEIGHT = 0.80
RULE_WEIGHT = 0.20
STRONG_RULE_THRESHOLD = 0.95

# 明确模型配置。Luna作为之后可单独对比的候选，此处不自动降级或并跑。
MODEL_REASONING_EFFORTS = {
    "gpt-6-astra": "low",
    "gpt-6.1-sol": "high",
    "gpt-6-luna": "xhigh",
}

def completion_parameters(model_name=None):
    """有推理强度时不发送temperature；参数按实际调用模型生成。"""
    if model_name is None:
        return {"reasoning_effort": REASONING_EFFORT}
    if model_name in MODEL_REASONING_EFFORTS:
        return {"reasoning_effort": MODEL_REASONING_EFFORTS[model_name]}
    return {"temperature": 0}
