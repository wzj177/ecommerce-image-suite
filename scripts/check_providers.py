#!/usr/bin/env python3
"""
check_providers.py
检测已配置的图像生成供应商，输出 JSON 结果。
配置来源：环境变量（*_API_KEY / *_BASE_URL）
"""

import os
import json

PROVIDERS = [
    {"id": "openai",     "name": "DALL·E 3",           "company": "OpenAI",          "env": "OPENAI_API_KEY",     "env_url": "OPENAI_BASE_URL"},
    {"id": "gemini",     "name": "Gemini Imagen 3",     "company": "Google",          "env": "GEMINI_API_KEY",     "env_url": "GEMINI_BASE_URL"},
    {"id": "stability",  "name": "Stable Image Core",   "company": "Stability AI",    "env": "STABILITY_API_KEY",  "env_url": "STABILITY_BASE_URL"},
    {"id": "tongyi",     "name": "千问 qwen-image-2.0",  "company": "阿里云 DashScope", "env": "DASHSCOPE_API_KEY",  "env_url": "DASHSCOPE_BASE_URL"},
    {"id": "doubao",     "name": "豆包 Seedream",        "company": "字节跳动",         "env": "ARK_API_KEY",        "env_url": "ARK_BASE_URL"},
]


def check_providers():
    result = []
    for p in PROVIDERS:
        key = os.environ.get(p["env"], "").strip()
        url = os.environ.get(p["env_url"], "").strip()
        result.append({
            **p,
            "configured": len(key) > 5,
            "key_preview": f"{key[:8]}..." if key else "",
            "custom_url": url or None,
        })
    return result


if __name__ == "__main__":
    providers = check_providers()
    configured = [p for p in providers if p["configured"]]

    print(json.dumps({
        "all": providers,
        "configured": configured,
        "count": len(configured),
    }, ensure_ascii=False, indent=2))
