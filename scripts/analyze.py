#!/usr/bin/env python3
"""
analyze.py — 商品图视觉分析

功能：
- 接收商品图片（本地路径或 URL），调用视觉大模型分析
- 返回结构化卖点 JSON，供 generate.py / overlay.py 直接使用

供应商优先级（自动降级）：
  1. 阿里云通义 VL（DASHSCOPE_API_KEY / ALIYUN_API_KEY）→ qwen-vl-max
  2. 字节豆包视觉（ARK_API_KEY）                        → doubao-vision-pro-32k
  3. OpenAI（OPENAI_API_KEY）                           → gpt-4o

若三者均未配置，退出码 2，并输出配置指引。

用法：
  python3 analyze.py ./product.jpg
  python3 analyze.py ./front.jpg ./back.jpg          # 多张图（正面+背面）
  python3 analyze.py https://example.com/product.jpg
  python3 analyze.py ./product.jpg --provider tongyi
  python3 analyze.py ./product.jpg --lang en
  python3 analyze.py ./product.jpg --output ./output/product.json

依赖：
  pip install openai
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai 库未安装，请运行: pip install openai", file=sys.stderr)
    sys.exit(1)

# ── 供应商配置 ────────────────────────────────────────────────────────────────

VISION_PROVIDERS = [
    {
        "id":            "tongyi",
        "name":          "阿里云通义千问 VL",
        "env_key":       "DASHSCOPE_API_KEY",
        "env_key_alt":   "ALIYUN_API_KEY",          # 兼容旧变量名
        "env_url":       "DASHSCOPE_BASE_URL",
        "env_model":     "DASHSCOPE_VISION_MODEL",
        "default_model": "qwen-vl-max",
        "default_url":   "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
    {
        "id":            "doubao",
        "name":          "字节豆包视觉",
        "env_key":       "ARK_API_KEY",
        "env_key_alt":   "",
        "env_url":       "ARK_BASE_URL",
        "env_model":     "ARK_VISION_MODEL",
        "default_model": "doubao-vision-pro-32k",
        "default_url":   "https://ark.cn-beijing.volces.com/api/v3",
    },
    {
        "id":            "openai",
        "name":          "OpenAI GPT-4o",
        "env_key":       "OPENAI_API_KEY",
        "env_key_alt":   "",
        "env_url":       "OPENAI_BASE_URL",
        "env_model":     "OPENAI_VISION_MODEL",
        "default_model": "gpt-4o",
        "default_url":   "https://api.openai.com/v1",
    },
]


# ── 分析 Prompt ────────────────────────────────────────────────────────────────

ANALYSIS_PROMPT_ZH = """\
你是一位拥有15年以上电商经验的顶级视觉分析师和爆款文案策划师。

请仔细观察图片中的商品，按以下 JSON 格式输出分析结果，只输出 JSON，不要输出其他内容：

```json
{
  "product_name": "商品详细名称，包含品类、材质、款型等关键词",
  "product_description_for_prompt": "英文描述，用于图像生成 Prompt，包含颜色/款型/印花/材质等视觉细节，50词以内",
  "product_type": "服装 | 3C数码 | 家居 | 美妆 | 食品 | 其他",
  "garment_position": "top | bottom | full-body | non-apparel（非服装统一填 non-apparel）",
  "visual_features": ["视觉特征1", "视觉特征2"],
  "selling_points": [
    {"icon": "fabric|fit|design|comfort|quality|function|scene", "zh": "中文卖点标题", "en": "English title", "zh_desc": "中文说明≤15字", "en_desc": "English desc ≤12 words", "visual_keywords": ["English keyword1", "English keyword2"]}
  ],
  "target_audience": "目标人群描述",
  "target_scenes": ["使用场景1", "使用场景2"],
  "product_style": "商品风格（如：法式浪漫 / 日系可爱 / 简约商务 / 运动休闲）",
  "color": "精确英文色值描述（如 pure white、lavender purple）",
  "material": "主要材质（若可识别）",
  "style": "版型描述（宽松oversized、修身等）",
  "print_design": "印花/设计描述",
  "print_design_lock": "精确约束短语，要求 exact same print pattern, color and position must not change",
  "product_name_zh": "中文商品名（简短版，用于文案叠加）"
}
```

selling_points 请提炼 3-5 条，优先级：材质 > 版型 > 设计感 > 舒适性 > 使用场景。从图片可见特征推断，不要凭空捏造。"""

ANALYSIS_PROMPT_EN = """\
You are a top-tier e-commerce visual analyst and product marketing expert with 15+ years of experience.

Examine the product image carefully and output ONLY the following JSON, no other text:

```json
{
  "product_name": "Detailed product name with category, material, style keywords",
  "product_description_for_prompt": "English description for image generation prompt, include color/style/print/material visual details, within 50 words",
  "product_type": "Apparel | Electronics | Home | Beauty | Food | Other",
  "garment_position": "top | bottom | full-body | non-apparel (use non-apparel for all non-clothing products)",
  "visual_features": ["feature1", "feature2"],
  "selling_points": [
    {"icon": "fabric|fit|design|comfort|quality|function|scene", "zh": "Chinese title", "en": "English title", "zh_desc": "Chinese desc ≤15 chars", "en_desc": "English desc ≤12 words", "visual_keywords": ["English keyword1", "English keyword2"]}
  ],
  "target_audience": "Target audience description",
  "target_scenes": ["scene1", "scene2"],
  "product_style": "Product style (e.g. Romantic French / Casual Sporty / Minimalist Office)",
  "color": "Precise color (e.g. pure white, lavender purple)",
  "material": "Main material (if identifiable)",
  "style": "Fit description (oversized, slim-fit, etc.)",
  "print_design": "Print/design description",
  "print_design_lock": "Exact constraint phrase with: exact same print pattern, color and position must not change",
  "product_name_zh": "Short Chinese product name for overlay text"
}
```

Provide 3-5 selling_points, priority: material > fit > design > comfort > scene. Derived from visible features only."""


# ── 图片处理 ────────────────────────────────────────────────────────────────────

def image_to_url(path_or_url: str) -> str:
    """本地文件 → base64 data URI；HTTP URL → 直接返回。"""
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    path = Path(path_or_url)
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在：{path_or_url}")
    suffix = path.suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif",
    }
    mime = mime_map.get(suffix, "image/jpeg")
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def extract_json(text: str) -> dict:
    """从模型输出中提取 JSON（兼容 ```json 包裹和裸 JSON）。"""
    raw = text.strip()
    # 去掉 ```json ... ``` 包裹
    if "```json" in raw:
        raw = raw.split("```json", 1)[1]
    if "```" in raw:
        raw = raw.split("```", 1)[0]
    raw = raw.strip()
    # 找到最外层 { }
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"模型输出中未找到 JSON：\n{text}")
    return json.loads(raw[start:end])


# ── 供应商选择 ────────────────────────────────────────────────────────────────

def get_api_key(provider: dict) -> str:
    """读取 API Key，支持主变量名和兼容变量名。"""
    key = os.environ.get(provider["env_key"], "").strip()
    if not key and provider.get("env_key_alt"):
        key = os.environ.get(provider["env_key_alt"], "").strip()
    return key


def auto_select_provider() -> tuple[dict, str] | None:
    """按优先级自动选择已配置的视觉供应商，返回 (provider, api_key) 或 None。"""
    for p in VISION_PROVIDERS:
        key = get_api_key(p)
        if len(key) > 5:
            return p, key
    return None


# ── 核心分析函数 ───────────────────────────────────────────────────────────────

def analyze(image_paths_or_urls: list, provider: dict, api_key: str,
            lang: str = "zh", cli_model: str = "", cli_url: str = "") -> dict:
    """
    调用视觉 API 分析商品图片（支持多张），返回结构化卖点 dict。
    失败时返回 {"error": "...", "raw": "原始回复"}。
    """
    model = cli_model or os.environ.get(provider["env_model"], "") or provider["default_model"]
    base_url = cli_url or os.environ.get(provider["env_url"], "") or provider["default_url"]

    prompt = ANALYSIS_PROMPT_ZH if lang == "zh" else ANALYSIS_PROMPT_EN

    n = len(image_paths_or_urls)
    print(f"   正在分析商品图片 {n} 张（供应商: {provider['name']}  模型: {model}）...", file=sys.stderr)

    # 构建多图 content 列表：所有图片先行，prompt 文本末尾
    content = []
    for path_or_url in image_paths_or_urls:
        image_url = image_to_url(path_or_url)
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    content.append({"type": "text", "text": prompt})

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=2048,
            temperature=0.1,
        )
    except Exception as e:
        return {"error": f"API 调用失败: {e}"}

    raw = completion.choices[0].message.content.strip()

    try:
        result = extract_json(raw)
        print("   商品分析完成", file=sys.stderr)
        return result
    except (json.JSONDecodeError, ValueError):
        print("   JSON 解析失败，返回原始文本", file=sys.stderr)
        return {"error": "JSON 解析失败", "raw": raw}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="商品图片视觉分析脚本")
    parser.add_argument("images",     nargs="+", help="商品图片路径（本地文件）或 HTTP URL，支持多张（空格分隔）")
    parser.add_argument("--provider", default="",   help="指定供应商：tongyi / doubao / openai（不填则自动降级）")
    parser.add_argument("--api-key",  default="",   help="API Key（也可通过环境变量传入）")
    parser.add_argument("--base-url", default="",   help="自定义 Base URL（也可通过 *_BASE_URL 环境变量传入）")
    parser.add_argument("--model",    default="",   help="指定视觉模型名称")
    parser.add_argument("--lang",     default="zh", choices=["zh", "en"], help="输出语言（默认 zh）")
    parser.add_argument("--output",   default="",   help="输出 JSON 文件路径（不填则打印到 stdout）")
    args = parser.parse_args()

    # 选择供应商
    if args.provider:
        matched = next((p for p in VISION_PROVIDERS if p["id"] == args.provider), None)
        if not matched:
            print(f"ERROR: 未知供应商 '{args.provider}'，可选：tongyi / doubao / openai", file=sys.stderr)
            sys.exit(1)
        api_key = args.api_key or get_api_key(matched)
        if len(api_key) <= 5:
            print(
                f"ERROR: 供应商 '{args.provider}' 未配置 API Key。\n"
                f"请通过 --api-key 参数或环境变量 {matched['env_key']} 传入。",
                file=sys.stderr,
            )
            sys.exit(1)
        provider = matched
    else:
        found = auto_select_provider()
        if found is None:
            print(
                "ERROR: 未检测到任何视觉识别 API Key，无法分析商品图片。\n\n"
                "请至少配置以下供应商之一：\n"
                "  export DASHSCOPE_API_KEY=\"sk-...\"   # 阿里云通义（推荐，国内直连）\n"
                "  export ARK_API_KEY=\"...\"             # 字节豆包（国内直连）\n"
                "  export OPENAI_API_KEY=\"sk-...\"      # OpenAI（需代理）\n\n"
                "配置后执行 source ~/.zshrc 使其生效。",
                file=sys.stderr,
            )
            sys.exit(2)
        provider, api_key = found

    # 执行分析
    result = analyze(
        image_paths_or_urls=args.images,
        provider=provider,
        api_key=api_key,
        lang=args.lang,
        cli_model=args.model,
        cli_url=args.base_url,
    )

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        if "raw" in result:
            print(f"原始输出：\n{result['raw']}", file=sys.stderr)
        sys.exit(1)

    result_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result_json, encoding="utf-8")
        print(f"✅ 分析完成，已写入：{args.output}", file=sys.stderr)
    else:
        print(result_json)


if __name__ == "__main__":
    main()
