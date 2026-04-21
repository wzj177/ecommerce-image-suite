#!/usr/bin/env python3
"""
generate.py
调用图像生成 API，支持 5 个供应商，文案由生图模型直接排版渲染，输出最终图片。

用法：
  python3 generate.py \
    --product '{"product_description_for_prompt": "white T-shirt...", "selling_points": [...]}' \
    --provider openai \
    --api-key "sk-..." \
    --base-url "https://custom-proxy.example.com/v1" \
    --model "dall-e-3" \
    --lang zh \
    --types white_bg,key_features,material \
    --output-dir ./output/

也可通过环境变量传入 key / base-url / model：
  OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL (默认 dall-e-3)
  GEMINI_API_KEY / GEMINI_BASE_URL / GEMINI_MODEL (默认 gemini-3.1-flash-image-preview)
  STABILITY_API_KEY / STABILITY_BASE_URL / STABILITY_MODEL (默认 core)
  DASHSCOPE_API_KEY / DASHSCOPE_BASE_URL / DASHSCOPE_MODEL (默认 qwen-image-2.0-pro)
  ARK_API_KEY / ARK_BASE_URL / ARK_IMAGE_MODEL (默认 doubao-seedream-4-5-251128)
"""

import argparse
import base64
import datetime
import json
import os
import sys
from pathlib import Path

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # 全局禁用 SSL 验证（绕过企业代理/证书问题）
    _orig_session_request = requests.Session.request
    def _no_ssl_verify(self, method, url, **kwargs):
        kwargs.setdefault("verify", False)
        return _orig_session_request(self, method, url, **kwargs)
    requests.Session.request = _no_ssl_verify
except ImportError:
    print("请先安装 requests：pip install requests", file=sys.stderr)
    sys.exit(1)


# ── 错误日志工具 ────────────────────────────────────────────────────────────

def _mask_auth(headers: dict) -> dict:
    """将 Authorization / x-goog-api-key 打码，仅保留前6位和后4位。"""
    masked = {}
    for k, v in headers.items():
        if k.lower() in ("authorization", "x-goog-api-key") and isinstance(v, str) and v:
            if k.lower() == "authorization":
                parts = v.split(" ", 1)
                token = parts[1] if len(parts) == 2 else v
                prefix = (parts[0] + " ") if len(parts) == 2 else ""
            else:
                token, prefix = v, ""
            visible = f"{token[:6]}...{token[-4:]}" if len(token) > 10 else "***"
            masked[k] = prefix + visible
        else:
            masked[k] = v
    return masked


def _write_error_log(output_dir: Path, provider: str, type_id: str,
                     prompt: str, exc: Exception) -> Path:
    """将 API 调用失败的完整链路写入 JSON 日志，返回日志路径。

    日志保存到 {output_dir}/error_logs/{timestamp}_{provider}_{type_id}.json
    包含：时间戳、provider、type_id、prompt 预览、完整请求体（脱敏）、
    完整响应体（含错误信息）、异常类型。
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = output_dir / "error_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{ts}_{provider}_{type_id}.json"

    log: dict = {
        "timestamp": datetime.datetime.now().isoformat(),
        "provider": provider,
        "type_id": type_id,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "prompt_length": len(prompt),
        "prompt": prompt,        # 完整 prompt，方便直接复制到 API 测试工具
        "request": None,
        "response": None,
    }

    # 仅当是 HTTP 错误时才有请求/响应详情
    http_resp = getattr(exc, "response", None)
    if http_resp is not None:
        req = http_resp.request

        # ── 请求体 ──
        req_body: object = None
        if req.body:
            raw = req.body if isinstance(req.body, str) else req.body.decode("utf-8", errors="replace")
            try:
                req_body = json.loads(raw)
            except Exception:
                req_body = raw

        log["request"] = {
            "method": req.method,
            "url": req.url,
            "headers": _mask_auth(dict(req.headers)),
            "body": req_body,
        }

        # ── 响应体 ──
        resp_body: object = None
        try:
            resp_body = http_resp.json()
        except Exception:
            resp_body = http_resp.text[:4000]

        log["response"] = {
            "status_code": http_resp.status_code,
            "headers": dict(http_resp.headers),
            "body": resp_body,
        }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    return log_path


# ── Default URLs ───────────────────────────────────────────────────────────

DEFAULT_URLS = {
    "openai":    "https://api.openai.com/v1/images/generations",
    "gemini":    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent",
    "stability": "https://api.stability.ai/v2beta/stable-image/generate/core",
    "tongyi":    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
    "doubao":    "https://ark.cn-beijing.volces.com/api/v3/images/generations",
}


# ── 图片类型 → 中文文件名映射 ────────────────────────────────────────────────

TYPE_NAMES_ZH = {
    "white_bg":      "白底主图",
    "key_features":  "核心卖点图",
    "selling_pt":    "卖点图",
    "material":      "材质图",
    "lifestyle":     "场景展示图",
    "model":         "模特展示图",
    "multi_scene":   "多场景拼图",
    "three_angle_view": "三角度拼图",
}


# ── Prompt 构建 ────────────────────────────────────────────────────────────

def _sp_title(sp, i, lang):
    """获取第 i 个卖点的标题。"""
    try:
        pt = sp[i]
    except IndexError:
        return ""
    if lang == "zh":
        return pt.get("zh_title", pt.get("zh", ""))
    return pt.get("en_title", pt.get("en", ""))


def _sp_desc(sp, i, lang):
    """获取第 i 个卖点的描述。"""
    try:
        pt = sp[i]
    except IndexError:
        return ""
    if lang == "zh":
        return pt.get("zh_desc", pt.get("description", pt.get("zh", "")))
    return pt.get("en_desc", pt.get("en", ""))


def _sp_visual_detail(sp, i) -> str:
    """获取第 i 个卖点用于放大镜特写的视觉细节描述（英文）。
    优先取 visual_keywords（应为英文关键词列表），其次取 en_desc，再取 en 标题。
    禁止回退到 zh / description（中文字段），防止中文字符混入英文 Prompt 导致 AI 误解。"""
    try:
        pt = sp[i]
    except IndexError:
        return ""
    kw = pt.get("visual_keywords", [])
    if kw:
        return ", ".join(str(k) for k in kw[:2])
    # 级联英文字段，不回退到中文
    return pt.get("en_desc", pt.get("en", ""))


def _infer_pairing(garment_position: str) -> str:
    """根据商品分析结果中的 garment_position 返回搭配描述。

    top → 搭配下装；bottom → 搭配上衣；full-body / non-apparel → 无搭配。
    """
    if garment_position == "top":
        return "paired with light blue denim shorts"
    elif garment_position == "bottom":
        return "paired with a simple white T-shirt"
    # full-body / non-apparel → 不需要额外搭配
    return ""


def _scene_to_env(scene_zh: str, product_type: str = "") -> str:
    """将中文目标场景词映射为英文环境描述，用于 lifestyle / multi_scene prompt。
    product_type 用于在场景词模糊时推断类别默认环境（兜底）。"""
    s = scene_zh
    # ── 服装/通用生活场景 ──
    if any(k in s for k in ("居家", "睡", "卧室", "内衣", "睡衣", "室内", "家中", "闺蜜")):
        return "cozy bedroom interior, soft ambient lamp light, satin bedding, intimate home setting"
    if any(k in s for k in ("海边", "沙滩", "度假", "海滩", "海岛")):
        return "tropical beach, golden sand, turquoise ocean backdrop, sunlit coastal scene"
    if any(k in s for k in ("约会", "浪漫", "晚宴", "romantic", "date", "情侣")):
        return "intimate romantic restaurant terrace, warm candlelight, evening ambient glow"
    if any(k in s for k in ("运动", "健身", "瑜伽", "跑步", "gym", "sport")):
        return "modern fitness studio or park path, natural light, clean athletic atmosphere"
    if any(k in s for k in ("派对", "聚会", "party", "gathering", "社交")):
        return "chic social venue, warm ambient lighting, stylish gathering atmosphere"
    if any(k in s for k in ("办公", "通勤", "上班", "商务", "office", "work")):
        return "modern office or minimalist café workspace, clean professional atmosphere"
    if any(k in s for k in ("校园", "学校", "课堂", "campus", "school")):
        return "sunny campus green lawn or café, shallow depth of field, youthful atmosphere"
    if any(k in s for k in ("户外", "公园", "街头", "城市", "散步", "逛街", "出行")):
        return "lush outdoor park or urban street, golden hour natural light, soft bokeh"
    if any(k in s for k in ("旅行", "出游", "旅游", "travel", "trip")):
        return "scenic travel destination, open air, natural bright light, wanderlust vibe"
    if any(k in s for k in ("咖啡", "下午茶", "café", "coffee")):
        return "cozy café interior, wooden table, warm natural window light, lifestyle mood"
    # ── 非服装/家居/电器 场景 ──
    if any(k in s for k in ("客厅", "沙发", "起居", "living room")):
        return "bright modern living room, clean sofa and wooden floor, warm natural light"
    if any(k in s for k in ("厨房", "餐厅", "烹饪", "kitchen")):
        return "clean modern kitchen counter, marble surface, soft overhead lighting"
    if any(k in s for k in ("书房", "书桌", "学习", "阅读", "study", "desk")):
        return "tidy home study room, wooden desk, soft warm desk lamp, bookshelf background"
    if any(k in s for k in ("办公桌", "工作台", "workspace")):
        return "minimalist office desk setup, clean workspace, natural window light"
    if any(k in s for k in ("床头", "睡前", "bedside")):
        return "serene bedroom setting, bedside table, soft ambient lamp glow"
    if any(k in s for k in ("清洁", "打扫", "吸尘", "拖地", "clean")):
        return "bright clean home interior, polished floor, natural daylight, tidying scene"
    if any(k in s for k in ("装修", "家装", "布置", "decor", "interior")):
        return "stylish home interior during decoration, warm ambient light, modern furniture"
    if any(k in s for k in ("庭院", "花园", "园艺", "garden", "outdoor work", "户外劳作")):
        return "sunlit backyard garden, lush green plants, natural bright outdoor daylight"
    # ── 类别兜底（scene 词模糊时按 product_type 给默认场景）──
    pt = product_type.lower()
    if any(k in pt for k in ("家居", "home", "furniture", "家具")):
        return "bright Scandinavian-style living room, clean surfaces, warm natural light"
    if any(k in pt for k in ("3c", "数码", "电器", "electronics", "appliance")):
        return "clean minimalist workspace or kitchen counter, soft studio-style lighting"
    if any(k in pt for k in ("美妆", "beauty", "cosmetic", "护肤")):
        return "elegant vanity desk, soft diffused light, fresh white background, beauty mood"
    if any(k in pt for k in ("食品", "food", "零食", "beverage")):
        return "warm kitchen countertop with natural ingredients, rustic wooden surface, fresh daylight"
    # 全局默认
    return "bright authentic lifestyle setting, natural light, shallow depth of field"


def _get_scene_env(target_scene_envs: list, index: int,
                   target_scenes: list, product_type: str = "") -> str:
    """获取指定 index 的英文场景环境描述。
    优先读取 target_scene_envs（Agent 预翻译的英文环境描述），
    降级到 _scene_to_env() 中文关键词映射。"""
    if target_scene_envs and index < len(target_scene_envs):
        env = (target_scene_envs[index] or "").strip()
        if env:
            return env
    if target_scenes and index < len(target_scenes):
        return _scene_to_env(target_scenes[index], product_type)
    return _scene_to_env("", product_type)


def _infer_model_subject(target_audience: str, model_ethnicity: str = "") -> str:
    """根据 target_audience 和 model_ethnicity 推断模特性别/年龄/种族描述。

    Args:
        target_audience: 目标人群描述（如"18-30岁年轻女性"）
        model_ethnicity: 模特种族偏好（asian/western/mixed，默认为asian）

    Returns:
        模特描述字符串
    """
    s = target_audience.lower() if target_audience else ""

    # 判断性别
    if any(k in s for k in ("男", "男士", "男性", "先生", "men", "male", "gentleman", "boy")):
        gender = "male"
    else:
        gender = "female"

    # 判断年龄
    if any(k in s for k in ("儿童", "小孩", "宝宝", "孩子", "children", "child", "kids",
                            "6岁", "8岁", "10岁", "12岁")):
        age_desc = "child model aged 6-12"
    else:
        age_desc = "adult model"

    # 判断种族
    ethnicity = model_ethnicity.lower() if model_ethnicity else "asian"
    if ethnicity == "western":
        race = "Caucasian"
    elif ethnicity == "mixed":
        race = "ethnically diverse"
    else:  # asian 或默认
        race = "Asian"

    # 组合描述
    if age_desc == "child model aged 6-12":
        return f"{race} {age_desc}"
    else:
        return f"{race} {gender} model"


# ── 输入图类型 → 白底主图构图描述 ──────────────────────────────────────────────

INPUT_TYPE_COMPOSITIONS = {
    # 单张平铺正面
    "flat_lay": (
        "displayed flat on pure white background (RGB 255,255,255), "
        "front view, slight 5-degree product tilt, natural fabric drape, subtle soft shadow beneath"
    ),
    # 正面 + 背面平铺（取正面构图，可展现正面全貌）
    "flat_lay_front_back": (
        "displayed flat on pure white background (RGB 255,255,255), "
        "front view, slight 5-degree product tilt, natural fabric drape, subtle soft shadow beneath, "
        "showcasing the full front design and silhouette"
    ),
    # 单张挂拍
    "hanging": (
        "hanging naturally on an invisible hook on pure white background (RGB 255,255,255), "
        "full length, front view, fabric draping naturally"
    ),
    # 挂拍正面 + 背面
    "hanging_front_back": (
        "hanging naturally on an invisible hook on pure white background (RGB 255,255,255), "
        "full length, front view, fabric draping naturally"
    ),
    # 模特实拍（AI 去除模特，仅保留商品）
    "model": (
        "product isolated on pure white background (RGB 255,255,255), "
        "front view, product shape preserved, no model"
    ),
}

# 每种图类型优先选用哪张输入图（按 index）
# front=0, back=1；当 back 图不存在时自动回退到 front
TYPE_IMAGE_SLOT = {
    "white_bg":      0,   # 正面
    "key_features":  0,   # 正面
    "selling_pt":    0,   # 正面
    "material":      1,   # 背面/细节面（纹理更清晰）
    "lifestyle":     0,
    "model":         0,
    "multi_scene":   0,
    "three_angle_view": 0,  # 使用正面图，AI生成三角度
}


def build_prompt(type_id: str, desc: str, selling_points: list,
                 model_style: str = "standard", has_model_ref: bool = False,
                 lang: str = "zh", garment_position: str = "non-apparel",
                 print_design_lock: str = "", has_product_ref: bool = False,
                 input_image_type: str = "flat_lay",
                 template_set: int = 1,
                 key_features_style: str = "",
                 per_type_templates: dict = None,
                 target_scenes: list = None,
                 product_style: str = "",
                 target_audience: str = "",
                 target_scene_envs: list = None,
                 product_type: str = "",
                 model_ethnicity: str = "asian") -> str:
    """构建图片 Prompt。template_set 1-5 对应 5 套视觉风格模板。
    target_scenes:     来自商品分析的目标场景列表（中文），如 ['居家休闲', '约会出行']
    target_scene_envs: Agent 预翻译的英文场景环境列表，与 target_scenes 一一对应
    product_style:     商品风格标签，如 '居家睡衣' / '运动休闲'，用于 lifestyle 标题
    target_audience:   目标用户描述，用于推断模特性别/年龄
    product_type:      商品大类，如 '服装' / '家居' / '3C数码'，用于场景兜底推断
    model_ethnicity:   模特种族，asian/western/mixed，默认为 asian
    """

    QUALITY = (
        "shot on Sony A7R V, 85mm f/2.0 lens, natural diffused studio lighting, "
        "authentic commercial product photography, true-to-life colors no heavy post-processing, "
        "realistic fabric texture and natural drape, professional e-commerce visual style. "
        "CRITICAL: Keep the EXACT same product design, color, print, proportions and all details. "
        "Do NOT alter any design element. "
        "Do NOT redesign, recolor, replace, or rotate the product into a different structure."
    )

    PRODUCT_REF_LOCK = (
        "CRITICAL HIGHEST PRIORITY: Product reference image is provided. "
        "You MUST use the reference image as the EXACT basis for the product. "
        "Keep EXACT same: silhouette, print pattern, print position, all colors, neckline, sleeves, hem, fabric texture. "
        "DO NOT change: the print design, color scheme, silhouette shape, fabric appearance. "
        "You may ONLY change: background scene, camera angle, lighting, model pose. "
        "The product must look IDENTICAL to the reference image - same dress, same pattern, same colors."
    )

    # 语言约束：Gemini/OpenAI 需要明确指定文本语言
    if lang == "zh":
        TEXT_RENDER = (
            "EXTREMELY IMPORTANT: Render ALL text in Simplified Chinese ONLY. "
            "Use clean modern bold sans-serif typography (思源黑体 / Alibaba PuHuiTi or similar). "
            "Text must be perfectly sharp, highly legible, excellent hierarchy, proper kerning. "
            "Use subtle drop shadow (black 30% opacity) for readability. "
            "Professional commercial layout, balanced spacing, no distortion, no overlapping."
        )
    else:  # lang == "en"
        TEXT_RENDER = (
            "EXTREMELY IMPORTANT: Render ALL text in English ONLY. "
            "Use clean modern bold sans-serif typography (Helvetica Neue, Arial, or similar). "
            "Text must be perfectly sharp, highly legible, excellent hierarchy, proper kerning. "
            "Use subtle drop shadow (black 30% opacity) for readability. "
            "Professional commercial layout, balanced spacing, no distortion, no overlapping."
        )

    target_scenes = target_scenes or []
    target_scene_envs = target_scene_envs or []

    # 根据 target_audience 和 model_ethnicity 推断模特描述
    _model_subject = _infer_model_subject(target_audience, model_ethnicity)

    sp = selling_points
    kf_heading = "为什么选择我们" if lang == "zh" else "WHY CHOOSE US"
    kf_labels = [_sp_title(sp, i, lang) for i in range(3)]

    # 卖点图文案：纯级联，不硬编码品类专属兜底文字
    sp_heading = _sp_title(sp, 1, lang) or _sp_title(sp, 0, lang)
    sp_sub1 = _sp_desc(sp, 1, lang) or _sp_desc(sp, 0, lang)
    sp_sub2 = _sp_desc(sp, 2, lang) or _sp_desc(sp, 1, lang)

    # 材质图文案：纯级联
    mat_heading = _sp_title(sp, 0, lang)
    mat_sub1 = _sp_desc(sp, 0, lang)
    mat_sub2 = _sp_desc(sp, 2, lang) or _sp_desc(sp, 1, lang)

    # 场景展示图文案：从目标场景 + 卖点动态生成，禁止写死品类专属文案
    _ts = [s for s in target_scenes if s]
    ls_heading = (
        (product_style[:20] if product_style else None)
        or _sp_title(sp, 2, lang)
        or _sp_title(sp, 0, lang)
        or ("多场景百搭" if lang == "zh" else "VERSATILE EVERYDAY STYLE")
    )
    ls_sub1 = (
        _ts[0][:15] if _ts
        else _sp_title(sp, 0, lang)
        or ("精选面料" if lang == "zh" else "Premium Quality")
    )
    ls_sub2 = (
        _ts[1][:15] if len(_ts) > 1
        else _sp_title(sp, 1, lang)
        or ("品质设计" if lang == "zh" else "Elegant Design")
    )

    MODEL_REF_LOCK = (
        f"CRITICAL: Two reference images are provided. "
        f"First image: Model reference — MUST use EXACTLY the same "
        f"{_model_subject}: identical face, skin tone, hair, body shape, "
        f"expression and ethnicity. Do not replace or change the model. "
        f"Second image: Product reference — MUST use EXACTLY the same "
        f"garment design: silhouette, print pattern, print position, all colors, neckline, sleeves, hem, fabric texture. "
        f"The model must WEAR the EXACT SAME garment from the second image. "
        f"Do NOT change the garment design, color, or style."
    )

    # 根据分析结果中的 garment_position 决定搭配
    pairing = _infer_pairing(garment_position)
    is_apparel = garment_position != "non-apparel"
    outfit = (f"wearing {desc} {pairing}".rstrip() if is_apparel
              else f"showcasing {desc}")

    # 多场景拼图标题：从目标场景动态生成，禁止写死品类专属文案
    ms_heading = (
        _sp_title(sp, 2, lang)
        or ("一件多穿，随心切换" if lang == "zh" else "VERSATILE FOR ANY OCCASION")
    )
    ms_left = _ts[0][:12] if _ts else ("居家休闲" if lang == "zh" else "Home Casual")
    ms_right = _ts[1][:12] if len(_ts) > 1 else ("日常出行" if lang == "zh" else "Daily Lifestyle")

    lock_tail = f" {print_design_lock}" if print_design_lock else ""
    ref_tail = f" {PRODUCT_REF_LOCK}" if has_product_ref else ""

    # 根据输入图类型选择白底主图构图
    white_bg_composition = INPUT_TYPE_COMPOSITIONS.get(
        input_image_type,
        "centered on pure white background, front 3/4 view, slight angle, subtle shadow beneath, 88% frame"
    )

    # 材质图：有背面图时用背面纹理描述，否则用正面
    material_view = (
        "back surface, showing reverse-side fabric detail"
        if input_image_type in ("flat_lay_front_back", "hanging_front_back")
        else "surface detail"
    )

    # ── 核心卖点图样式（独立于 template_set）─────────────────────────────────────
    # 优先级：key_features_style > per_type_templates > 默认
    kf_detail_a = _sp_visual_detail(sp, 0) or "fabric texture and stitching"
    kf_detail_b = _sp_visual_detail(sp, 1) or "design detail and craftsmanship"
    kf_detail_c = _sp_visual_detail(sp, 2) or "silhouette and fit"

    per_type_templates = per_type_templates or {}

    # 确定核心卖点图样式
    if key_features_style:
        kf_style = key_features_style
    elif "key_features" in per_type_templates:
        # 从 per_type_templates 转换模板编号到样式
        kf_tpl = per_type_templates["key_features"]
        if kf_tpl == 2:
            kf_style = "annotation"
        elif kf_tpl == 3:
            kf_style = "split"
        elif kf_tpl == 4:
            kf_style = "badge"
        elif kf_tpl == 5:
            kf_style = "gold_bubble"
        else:
            kf_style = "magnifier" if is_apparel else "icon_list"
    else:
        # 默认：服装用放大镜，非服装用图标列表
        kf_style = "magnifier" if is_apparel else "icon_list"

    # 根据确定的样式构建 prompt
    if kf_style == "icon_list":  # 信息图标列表
        key_features_prompt = (
            f"Modern minimalist infographic, light gray gradient bg. "
            f"Left: {desc} front view (45%). "
            f"Right: bold heading \"{kf_heading}\", "
            f"three vertical icon+text: \"{kf_labels[0]}\", \"{kf_labels[1]}\", \"{kf_labels[2]}\". "
            f"Premium layout. {TEXT_RENDER}{ref_tail} {QUALITY}"
        )
    elif kf_style == "annotation":  # 标注线指示
        key_features_prompt = (
            f"{desc}, editorial product photography, product centered on warm beige background. "
            f"Three elegant handwritten-style annotation lines from product details: "
            f"annotation 1 → \"{kf_labels[0]}\" ({kf_detail_a}); "
            f"annotation 2 → \"{kf_labels[1]}\" ({kf_detail_b}); "
            f"annotation 3 → \"{kf_labels[2]}\" ({kf_detail_c}). "
            f"Kinfolk magazine aesthetic, natural light and shadows, serif typeface. "
            f"{TEXT_RENDER}{ref_tail} {QUALITY}"
        )
    elif kf_style == "split":  # 分割板块
        key_features_prompt = (
            f"{desc}, ultra-minimalist product photography on pure black background. "
            f"Product in white spotlight center, single white hairline border frame. "
            f"Three feature labels in clean white sans-serif: "
            f"\"{kf_labels[0]}\", \"{kf_labels[1]}\", \"{kf_labels[2]}\". "
            f"Luxury fashion brand, zero clutter, monochrome palette. "
            f"{TEXT_RENDER}{ref_tail} {QUALITY}"
        )
    elif kf_style == "badge":  # 爆炸形徽章（活力爆款）
        key_features_prompt = (
            f"{desc}, high-energy commercial product photography, white background. "
            f"Bold sunburst starburst in yellow (#FFD700) behind product. "
            f"Three circular badge labels in vivid red (#E02E24), extra-bold font tilted -3deg: "
            f"\"{kf_labels[0]}!\", \"{kf_labels[1]}!\", \"{kf_labels[2]}!\". "
            f"Explosive high-saturation POP art energy. "
            f"{TEXT_RENDER}{ref_tail} {QUALITY}"
        )
    elif kf_style == "gold_bubble":  # 金色描边气泡（暗调质感）
        key_features_prompt = (
            f"{desc}, luxury dark product photography on deep charcoal (#1A1A2E) background. "
            f"Product lit with golden side light. "
            f"Three gold-bordered circular callout bubbles with feature labels: "
            f"\"{kf_labels[0]}\", \"{kf_labels[1]}\", \"{kf_labels[2]}\". "
            f"Premium fashion editorial dark aesthetic, gold accent (#C8A86C). "
            f"{TEXT_RENDER}{ref_tail} {QUALITY}"
        )
    else:  # magnifier - 放大镜气泡（默认）
        key_features_prompt = (
            f"{desc}, high-end product photography, centered floating composition, "
            f"clean softly blurred background; "
            f"featuring 3 circular magnifying glass insets (callout bubbles) connected by thin elegant lines "
            f"to specific parts of the main product: "
            f"Inset 1 (top-left): close-up of [{kf_detail_a}], label \"{kf_labels[0]}\"; "
            f"Inset 2 (top-right): close-up of [{kf_detail_b}], label \"{kf_labels[1]}\"; "
            f"Inset 3 (bottom-right): close-up of [{kf_detail_c}], label \"{kf_labels[2]}\". "
            f"Soft studio lighting, minimalist commercial design, sharp focus on product, bokeh background. "
            f"{TEXT_RENDER}{ref_tail} {QUALITY}"
        )

    # ── 卖点图 5 套模板 ──────────────────────────────────────────────────────
    _sp_model_lock = MODEL_REF_LOCK if has_model_ref else ""
    # 为模特展示图增加真实感细节，抑制 AI 僵硬感
    _MODEL_REALISM = " natural hair flyaway, subtle hand movement, authentic candid posture."
    if template_set == 2:    # 生活杂志：咖啡馆窗前
        selling_pt_prompt = (
            (
                f"Bright café window seat, morning natural light, warm wooden surface. "
                f"{desc} casually arranged in lifestyle context. Bold heading \"{sp_heading}\" upper left, "
                f"\"{sp_sub1}\", \"{sp_sub2}\". Kinfolk lifestyle mood. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"Bright café window seat, morning natural light, warm wooden surface. "
                f"{desc} placed as a lifestyle product hero. Bold heading \"{sp_heading}\" upper left, "
                f"\"{sp_sub1}\", \"{sp_sub2}\". Kinfolk product mood. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )
    elif template_set == 3:  # 极简高冷：纯白棚拍
        selling_pt_prompt = (
            (
                f"Pure white minimal studio, crisp shadows. {desc} centered on white surface. "
                f"Single bold heading \"{sp_heading}\" top, \"{sp_sub1}\", \"{sp_sub2}\" below. "
                f"No props, zero clutter. {TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"Pure white minimal studio, crisp directional shadows. {desc} centered on white surface, "
                f"product as hero object. Single bold heading \"{sp_heading}\" top, "
                f"\"{sp_sub1}\", \"{sp_sub2}\" below. No props, zero clutter. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )
    elif template_set == 4:  # 活力爆款：户外街头高饱和
        selling_pt_prompt = (
            (
                f"Vibrant outdoor urban street, high saturation colors, dynamic energy. "
                f"{desc} featured prominently. Bold heading \"{sp_heading}\", "
                f"\"{sp_sub1}\", \"{sp_sub2}\". Pop art energy. {TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"Vibrant high-energy commercial setting, high saturation colors. "
                f"{desc} showcased boldly as hero product. Bold heading \"{sp_heading}\", "
                f"\"{sp_sub1}\", \"{sp_sub2}\". Pop art energy. {TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )
    elif template_set == 5:  # 暗调质感：暗棚聚光灯
        selling_pt_prompt = (
            (
                f"Dark atmospheric studio, single beam spotlight illuminating {desc}. "
                f"Deep moody shadows, cinematic feel. "
                f"Bold gold heading \"{sp_heading}\", \"{sp_sub1}\", \"{sp_sub2}\" in white. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"Dark atmospheric studio, single beam spotlight illuminating {desc} product. "
                f"Product surface details highlighted, deep cinematic shadows. "
                f"Bold gold heading \"{sp_heading}\", \"{sp_sub1}\", \"{sp_sub2}\" in white. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )
    else:                    # 默认：动态场景+卖点文案
        _sp_env = _get_scene_env(target_scene_envs, 0, target_scenes, product_type)
        selling_pt_prompt = (
            (
                f"{_sp_env.capitalize()}, warm natural light. {desc} worn with relaxed natural pose. "
                f"Bold heading \"{sp_heading}\" upper left, two lines: \"{sp_sub1}\", \"{sp_sub2}\". "
                f"Commercial lifestyle mood. {TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"{_sp_env.capitalize()}, clean natural light. {desc} displayed prominently as hero product. "
                f"Bold heading \"{sp_heading}\" upper left, two lines: \"{sp_sub1}\", \"{sp_sub2}\". "
                f"Commercial product mood. {TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )

    # ── 材质图 5 套模板 ──────────────────────────────────────────────────────
    if template_set == 2:    # 生活杂志：木纹/大理石桌面
        material_prompt = (
            (
                f"{desc} laid flat on natural oak wood or white marble surface, "
                f"editorial flat lay, top-down bird's eye view, warm morning light. "
                f"Bold heading \"{mat_heading}\" upper right, \"{mat_sub1}\" mid, \"{mat_sub2}\" lower. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"{desc} placed on natural oak wood or white marble surface, "
                f"editorial top-down product shot, warm morning light, clean composition. "
                f"Bold heading \"{mat_heading}\" upper right, \"{mat_sub1}\" mid, \"{mat_sub2}\" lower. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )
    elif template_set == 3:  # 极简高冷：折叠/几何极简
        material_prompt = (
            (
                f"{desc} neatly folded in geometric layers on pure white surface, "
                f"crisp shadows emphasizing fold lines and fabric weight. "
                f"Single bold heading \"{mat_heading}\" right, \"{mat_sub1}\", \"{mat_sub2}\". "
                f"Architectural minimal aesthetic. {TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"{desc} precisely arranged on pure white surface, "
                f"crisp directional shadows emphasizing product geometry and construction. "
                f"Single bold heading \"{mat_heading}\" right, \"{mat_sub1}\", \"{mat_sub2}\". "
                f"Architectural minimal aesthetic. {TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )
    elif template_set == 4:  # 活力爆款：高饱和动态
        material_prompt = (
            (
                f"{desc} dramatically unfolded showing vivid fabric layers at dynamic angle, "
                f"high saturation colors, close-up angled shot. "
                f"Bold heading \"{mat_heading}\" corner, \"{mat_sub1}\", \"{mat_sub2}\" in red. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"{desc} showcased at a dynamic dramatic angle, bold close-up highlighting surface quality, "
                f"high saturation colors, energetic composition. "
                f"Bold heading \"{mat_heading}\" corner, \"{mat_sub1}\", \"{mat_sub2}\" in red. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )
    elif template_set == 5:  # 暗调质感：暗色背景金边光圈
        material_prompt = (
            (
                f"Extreme close-up of {desc} fabric ({material_view}) against deep black background, "
                f"golden rim lighting tracing fabric edge, dramatic contrast. "
                f"Bold gold heading \"{mat_heading}\" right, \"{mat_sub1}\", \"{mat_sub2}\" in white. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"Extreme close-up of {desc} surface finish and construction details against deep black background, "
                f"golden rim lighting tracing product edges, dramatic contrast. "
                f"Bold gold heading \"{mat_heading}\" right, \"{mat_sub1}\", \"{mat_sub2}\" in white. "
                f"{TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )
    else:                    # 默认：极macro特写
        material_prompt = (
            (
                f"Extreme macro fabric texture of {desc} ({material_view}), "
                f"dramatic side lighting, soft folds. Blurred natural background. "
                f"Bold heading \"{mat_heading}\" upper right, \"{mat_sub1}\" mid, \"{mat_sub2}\" lower. "
                f"Hyper detailed. {TEXT_RENDER}{ref_tail} {QUALITY}"
            ) if is_apparel else (
                f"Extreme close-up product detail shot of {desc}, "
                f"showcasing surface finish, construction quality and material texture. "
                f"Dramatic side lighting on {material_view}, clean neutral background. "
                f"Bold heading \"{mat_heading}\" upper right, \"{mat_sub1}\" mid, \"{mat_sub2}\" lower. "
                f"Hyper detailed product photography. {TEXT_RENDER}{ref_tail} {QUALITY}"
            )
        )

    # ── 场景展示图 5 套模板 ──────────────────────────────────────────────────
    # 优先使用 target_scene_envs（Agent 预翻译），降级到 _scene_to_env() 关键词映射
    _ls_primary_env = _get_scene_env(target_scene_envs, 0, target_scenes, product_type)
    _ls_secondary_env = _get_scene_env(target_scene_envs, 1, target_scenes, product_type)

    if template_set == 2:    # 生活杂志：自然光氛围感
        lifestyle_prompt = (
            (
                f"{_ls_primary_env.capitalize()}, natural golden light, soft bokeh. "
                f"{_model_subject} {outfit}, relaxed natural pose, the {desc} is the visual focus. "
                f"Bold heading \"{ls_heading}\" upper left, \"{ls_sub1}\" and \"{ls_sub2}\". "
                f"Magazine editorial warmth. {TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"{_ls_primary_env.capitalize()}, warm natural light. "
                f"{desc} placed naturally as the visual focus. "
                f"Bold heading \"{ls_heading}\" upper left, \"{ls_sub1}\" and \"{ls_sub2}\". "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )
    elif template_set == 3:  # 极简高冷：极简室内
        lifestyle_prompt = (
            (
                f"Clean minimal interior space, soft diffused natural light, architectural simplicity. "
                f"{_model_subject} {outfit}, simple elegant pose, the {desc} is the visual focus. "
                f"Bold heading \"{ls_heading}\" upper left, \"{ls_sub1}\" and \"{ls_sub2}\". "
                f"Minimal luxury feel. {TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"Clean minimal interior, white surfaces, minimal props. "
                f"{desc} placed as hero object. "
                f"Bold heading \"{ls_heading}\" upper left, \"{ls_sub1}\" and \"{ls_sub2}\". "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )
    elif template_set == 4:  # 活力爆款：高饱和动感
        lifestyle_prompt = (
            (
                f"Vibrant dynamic scene with saturated colors, energetic atmosphere. "
                f"{_model_subject} {outfit}, energetic pose, the {desc} pops with color. "
                f"Bold heading \"{ls_heading}\" upper left, \"{ls_sub1}\" and \"{ls_sub2}\". "
                f"Street fashion energy. {TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"Vibrant colorful lifestyle context, high energy atmosphere. "
                f"{desc} featured boldly as the visual focus. "
                f"Bold heading \"{ls_heading}\" upper left, \"{ls_sub1}\" and \"{ls_sub2}\". "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )
    elif template_set == 5:  # 暗调质感：暗调氛围
        lifestyle_prompt = (
            (
                f"Moody atmospheric scene, dramatic low-key lighting, deep shadows. "
                f"{_model_subject} {outfit}, cool editorial pose, the {desc} is the visual focus. "
                f"Bold heading \"{ls_heading}\" upper left in gold, \"{ls_sub1}\" and \"{ls_sub2}\" in white. "
                f"Night fashion mood. {TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"Moody dark atmospheric scene, cinematic low-key lighting. "
                f"{desc} featured in atmospheric dark context. "
                f"Bold heading \"{ls_heading}\" upper left, \"{ls_sub1}\" and \"{ls_sub2}\". "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )
    else:                    # 默认：根据商品目标场景动态生成
        lifestyle_prompt = (
            (
                f"{_ls_primary_env.capitalize()}, warm natural light, shallow DOF. "
                f"{_model_subject} {outfit}, the {desc} is the absolute visual focus. "
                f"Bold white heading \"{ls_heading}\" upper left with shadow, \"{ls_sub1}\" and \"{ls_sub2}\" lower left. "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"{_ls_primary_env.capitalize()}, natural light, shallow DOF. "
                f"{desc} placed prominently as the visual focus. "
                f"Bold white heading \"{ls_heading}\" upper left with shadow, \"{ls_sub1}\" and \"{ls_sub2}\" lower left. "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )

    # ── 模特展示图 5 套模板 ──────────────────────────────────────────────────
    # 简化prompt避免触发内容审查，专注于商品展示而非模特描述
    if model_style == "bodycon":  # bodycon 优先级高于 template_set
        model_prompt = (
            f"Full-body studio fashion shot, clean solid background. {_model_subject} wearing {outfit}. "
            f"Fitted silhouette showing garment shape. Professional commercial lighting. No text.{ref_tail} {QUALITY}"
            + _MODEL_REALISM + _sp_model_lock
        )
    elif template_set == 2:  # 生活杂志：坐姿咖啡厅休闲
        model_prompt = (
            f"Bright café interior with window. {_model_subject} sitting {outfit}. "
            f"Warm natural light, casual pose. The {desc} is clearly visible. No text.{ref_tail} {QUALITY}"
            + _MODEL_REALISM + _sp_model_lock
        )
    elif template_set == 3:  # 极简高冷：白底棚拍全身
        model_prompt = (
            f"Clean white seamless studio background. {_model_subject} full body standing {outfit}. "
            f"Even professional lighting. The {desc} is the focus. Minimalist commercial style. No text.{ref_tail} {QUALITY}"
            + _MODEL_REALISM + _sp_model_lock
        )
    elif template_set == 4:  # 活力爆款：街拍动态跳跃
        model_prompt = (
            f"Modern city street scene. {_model_subject} walking {outfit}. "
            f"Dynamic outdoor setting with natural lighting. The {desc} is clearly visible. No text.{ref_tail} {QUALITY}"
            + _MODEL_REALISM + _sp_model_lock
        )
    elif template_set == 5:  # 暗调质感：暗棚聚光灯
        model_prompt = (
            f"Professional dark studio with focused lighting. {_model_subject} standing {outfit}. "
            f"Single light source, clean dark background. The {desc} is clearly visible. No text.{ref_tail} {QUALITY}"
            + _MODEL_REALISM + _sp_model_lock
        )
    elif template_set == 6:  # 非对称布局：左侧大图+右侧细节
        model_prompt = (
            f"Clean white studio background. {_model_subject} full body wearing {outfit}. "
            f"Professional commercial lighting. The {desc} is clearly visible. No text.{ref_tail} {QUALITY}"
            + _MODEL_REALISM + _sp_model_lock
        )
    else:                    # 默认：动态场景户外/室内
        _model_env = _get_scene_env(target_scene_envs, 0, target_scenes, product_type)
        model_prompt = (
            f"{_model_env.capitalize()}. {_model_subject} wearing {outfit}. "
            f"The {desc} is clearly visible. Natural professional lighting. No text.{ref_tail} {QUALITY}"
            + _MODEL_REALISM + _sp_model_lock
        )

    # ── 多场景拼图 5 套模板 ──────────────────────────────────────────────────
    # 优先使用 target_scene_envs，降级到 _scene_to_env() 映射
    _ms_scene1 = _get_scene_env(target_scene_envs, 0, target_scenes, product_type)
    _ms_scene2 = _get_scene_env(target_scene_envs, 1, target_scenes, product_type)
    _ms_scene3 = _get_scene_env(target_scene_envs, 2, target_scenes, product_type)
    _ms_s1_label = _ts[0][:12] if len(_ts) > 0 else ms_left
    _ms_s2_label = _ts[1][:12] if len(_ts) > 1 else ms_right
    _ms_s3_label = _ts[2][:12] if len(_ts) > 2 else ""
    _ms_consistency = (
        f"CRITICAL: ALL panels show the EXACT SAME {desc} — "
        f"identical design, color, fabric texture, proportions. "
        f"Same consistent {_model_subject} throughout, full-body visible in each panel."
    )

    if template_set == 2:    # 生活杂志：三格日记卡片
        multi_scene_prompt = (
            (
                f"[Magazine-style 3-panel collage] {desc} showcased across 3 lifestyle scenes with thin white card borders. "
                f"Panel 1: {_ms_scene1} — {_model_subject} {outfit}, relaxed natural pose, {_ms_s1_label}; "
                f"Panel 2: {_ms_scene2} — model {outfit}, candid interaction, {_ms_s2_label}; "
                f"Panel 3: {_ms_scene3} — model {outfit}, full-body visible, {_ms_s3_label}. "
                f"Heading \"{ms_heading}\" at top. Bottom: \"{ms_left}\" left, \"{ms_right}\" right. "
                f"Warm magazine diary aesthetic, natural tones. {_ms_consistency} "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"[Magazine-style 3-panel collage] {desc} shown across 3 scenes: "
                f"Panel 1: {_ms_scene1} ({_ms_s1_label}); "
                f"Panel 2: {_ms_scene2} ({_ms_s2_label}); "
                f"Panel 3: {_ms_scene3} ({_ms_s3_label}). "
                f"Heading \"{ms_heading}\" at top. Warm magazine diary tones. "
                f"CRITICAL: same {desc} in all panels. {TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )
    elif template_set == 3:  # 极简高冷：双屏简洁分割
        multi_scene_prompt = (
            (
                f"[Minimal 2-panel split] Clean bold dividing line at center. "
                f"LEFT: {_ms_scene1}, {_model_subject} {outfit}, clean negative space, {_ms_s1_label}. "
                f"RIGHT: {_ms_scene2}, model {outfit}, airy composition, {_ms_s2_label}. "
                f"Centered heading \"{ms_heading}\". Bottom: \"{ms_left}\" left, \"{ms_right}\" right. "
                f"Luxury minimal aesthetic, high contrast. {_ms_consistency} "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"[Minimal 2-panel split] Clean dividing line. "
                f"LEFT: {_ms_scene1}, {desc} as hero object. RIGHT: {_ms_scene2}, {desc} in use. "
                f"Centered heading \"{ms_heading}\". Bottom: \"{ms_left}\" left, \"{ms_right}\" right. "
                f"CRITICAL: same {desc} both sides. {TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )
    elif template_set == 4:  # 活力爆款：动感对角分割
        multi_scene_prompt = (
            (
                f"[Dynamic diagonal collage] 45-degree bold split. "
                f"Upper-left: {_ms_scene1}, {_model_subject} {outfit}, energetic pose, {_ms_s1_label}. "
                f"Lower-right: {_ms_scene2}, model {outfit}, dynamic movement, {_ms_s2_label}. "
                f"Centered heading \"{ms_heading}\" bold. Bottom: \"{ms_left}\" left, \"{ms_right}\" right. "
                f"High-energy POP composition, saturated vibrant tones. {_ms_consistency} "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"[Dynamic diagonal collage] Bold diagonal split. "
                f"Upper-left: {_ms_scene1}, {desc} vibrant. Lower-right: {_ms_scene2}, {desc} dynamic. "
                f"Heading \"{ms_heading}\" bold. {_ms_s1_label} / {_ms_s2_label}. "
                f"CRITICAL: same {desc}. {TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )
    elif template_set == 5:  # 暗调质感：三屏电影感（用产品真实场景）
        multi_scene_prompt = (
            (
                f"[Cinematic 3-panel collage] Deep dark aesthetic, moody lighting. "
                f"Panel 1: {_ms_scene1}, {_model_subject} {outfit}, dramatic shadows, {_ms_s1_label}; "
                f"Panel 2: {_ms_scene2}, model {outfit}, atmospheric, {_ms_s2_label}; "
                f"Panel 3: {_ms_scene3}, model {outfit}, editorial pose, {_ms_s3_label}. "
                f"Heading \"{ms_heading}\" in gold. Bottom: \"{ms_left}\" left, \"{ms_right}\" right. "
                f"Cinematic dark fashion. {_ms_consistency} "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"[Cinematic 3-panel collage] Dark aesthetic. "
                f"Panel 1: {_ms_scene1} ({_ms_s1_label}). Panel 2: {_ms_scene2} ({_ms_s2_label}). Panel 3: {_ms_scene3} ({_ms_s3_label}). "
                f"Heading \"{ms_heading}\" in gold. CRITICAL: same {desc}. "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )
    elif template_set == 6:  # 非对称布局：左侧大图+右侧小图（2026.04 新增）
        multi_scene_prompt = (
            (
                f"[Asymmetric Product Showcase Layout] Professional collage with hero main image and detail insets. "
                f"Layout: Left 60% — large hero shot of {_ms_scene1} with {_model_subject} {outfit}, {_ms_s1_label}. "
                f"Right 40% — vertical stack of 2-3 detail panels with labels. "
                f"Detail Panel 1: {_ms_scene2}, {_ms_s2_label} — tight crop focusing on key design feature. "
                f"Detail Panel 2: {_ms_scene3}, {_ms_s3_label} — clean composition showing product in use context. "
                f"Thin white divider separating left and right sections. "
                f"Top-left heading \"{ms_heading}\" with subtle shadow. "
                f"Bottom-left: \"{ms_left}\". Bottom-right: \"{ms_right}\". "
                f"Style: photorealistic commercial photography, soft focus backgrounds, clean composition. "
                f"Color: warm inviting tones, natural saturation, no oversaturation. "
                f"{_ms_consistency} {TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"[Asymmetric Product Showcase Layout] Professional collage with hero main image and detail insets. "
                f"Layout: Left 60% — large hero shot of {desc} in {_ms_scene1}, {_ms_s1_label}. "
                f"Right 40% — vertical stack of 2-3 detail panels with labels. "
                f"Detail Panel 1: {_ms_scene2}, {_ms_s2_label} — tight crop focusing on key feature. "
                f"Detail Panel 2: {_ms_scene3}, {_ms_s3_label} — clean composition showing product in use. "
                f"Thin white divider separating left and right sections. "
                f"Top-left heading \"{ms_heading}\" with subtle shadow. "
                f"Bottom-left: \"{ms_left}\". Bottom-right: \"{ms_right}\". "
                f"Style: photorealistic commercial photography, warm natural tones. "
                f"CRITICAL: same {desc} in ALL panels — identical design, color, proportions. "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )
    else:                    # 默认：专业多场景结构（基于用户提供的最佳模板）
        multi_scene_prompt = (
            (
                f"[Commercial Product Showcase Collage] A single {desc} showcased across 3 distinct lifestyle scenes, "
                f"emphasizing versatility. All panels show SAME product worn by consistent relatable {_model_subject}, full-body visible. "
                f"Scene ①: {_ms_scene1} — {_ms_s1_label}, natural light, authentic interaction; "
                f"Scene ②: {_ms_scene2} — {_ms_s2_label}, dynamic natural pose, genuine atmosphere; "
                f"Scene ③: {_ms_scene3} — {_ms_s3_label}, scenic backdrop, full-body shot. "
                f"Layout: 3 equal vertical panels, thin white dividing lines. "
                f"Centered heading \"{ms_heading}\" at top with subtle shadow. "
                f"Bottom-left: \"{ms_left}\". Bottom-right: \"{ms_right}\". "
                f"Style: photorealistic commercial photography, soft focus backgrounds, clean composition. "
                f"Color: warm inviting tones, natural saturation, no oversaturation. "
                f"{_ms_consistency} {TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
            ) if is_apparel else (
                f"[Commercial Product Showcase Collage] A single {desc} featured across 3 distinct usage scenes. "
                f"Scene ①: {_ms_scene1} — {_ms_s1_label}; "
                f"Scene ②: {_ms_scene2} — {_ms_s2_label}; "
                f"Scene ③: {_ms_scene3} — {_ms_s3_label}. "
                f"Layout: 3 equal panels, thin white dividers. "
                f"Centered heading \"{ms_heading}\" at top. Bottom: \"{ms_left}\" left, \"{ms_right}\" right. "
                f"Style: photorealistic commercial photography, warm natural tones. "
                f"CRITICAL: same {desc} in ALL panels — identical design, color, proportions. "
                f"{TEXT_RENDER} {QUALITY}{lock_tail}{ref_tail}"
            )
        )

    # ── 三角度拼图（正面/侧面/背面，360度展示）────────────────────────────────
    # 当仅提供一张正面图时，自动生成三角度拼图以实现360度可见性
    three_angle_view_prompt = (
        (
            f"[Three-Angle Product View - Front/Side/Back Collage] A single image divided into THREE EQUAL-SIZED PANELS showing {_model_subject} wearing {desc} from different angles. "
            f"LEFT PANEL: Front view - model facing forward, full body from head to toe visible, showing front design, neckline, and overall silhouette. "
            f"MIDDLE PANEL: Side view - model standing in profile, full body visible, showing side silhouette, sleeve/sleeveless detail, and fabric drape. "
            f"RIGHT PANEL: Back view - model with back to camera, full body visible, showing back neckline, back design, and complete back silhouette. "
            f"CRITICAL REQUIREMENTS: "
            f"1. All three panels must show the EXACT SAME {desc} - identical design, color, print pattern, proportions. "
            f"2. All panels must be FULL-BODY shots including head, hair, shoulders, torso, legs, feet. NO cropping or body cutoffs. "
            f"3. All three panels must be the SAME SIZE and arranged horizontally with equal width. "
            f"4. Use thin white dividers between panels. "
            f"5. Clean white/light gray studio background, soft even lighting, professional commercial photography. "
            f"6. Sharp focus, natural skin tones, realistic fabric rendering. "
            f"Layout: [FRONT VIEW | SIDE VIEW | BACK VIEW] - three equal horizontal panels. "
            f"{_ms_consistency} {QUALITY}{lock_tail}{ref_tail}{_sp_model_lock}"
        ) if is_apparel else (
            f"[Three-Angle Product View - Front/Side/Back Collage] A single image divided into THREE EQUAL-SIZED PANELS showing {desc} from different angles. "
            f"LEFT PANEL: Front view - showing front design, main features, and front details. "
            f"MIDDLE PANEL: Side view - showing side profile, side details, and dimensional characteristics. "
            f"RIGHT PANEL: Back view - showing back panel, back design, and reverse-side features. "
            f"CRITICAL REQUIREMENTS: "
            f"1. All three panels must show the EXACT SAME product - identical design, color, proportions. "
            f"2. All three panels must be the SAME SIZE and arranged horizontally with equal width. "
            f"3. Use thin white dividers between panels. "
            f"4. Clean white/light gray studio background, professional commercial photography. "
            f"Layout: [FRONT VIEW | SIDE VIEW | BACK VIEW] - three equal horizontal panels. "
            f"{QUALITY}{lock_tail}{ref_tail}"
        )
    )

    prompts = {
        "white_bg": f"{desc}, {white_bg_composition}, product occupies 88% of frame, clean studio lighting with soft shadow. No text.{ref_tail} {QUALITY}",
        "key_features": key_features_prompt,
        "selling_pt": selling_pt_prompt,
        "material": material_prompt,
        "lifestyle": lifestyle_prompt,
        "model": model_prompt,
        "multi_scene": multi_scene_prompt,
        "three_angle_view": three_angle_view_prompt,
    }

    return prompts.get(type_id, f"{desc}. {QUALITY}")


# ── Provider Implementations ────────────────────────────────────────────────

# ── 默认 negative prompt（电商场景强化版）──
DEFAULT_NEGATIVE_PROMPT = (
    # AI 外观专项
    "AI-generated look, artificial, CGI quality, 3D render, digital art, synthetic texture, "
    "plastic skin, mannequin-like, uncanny valley, too perfect, robotic pose, "
    # 过度后处理
    "oversaturated, HDR, heavy vignette, cinematic color grading, heavy post-processing, "
    "dramatic bokeh, excessive lens flare, overprocessed, surreal color, "
    # 基础质量问题
    "low resolution, blurry, deformed, ugly, bad anatomy, extra limbs, "
    "overexposed, underexposed, grainy, noisy, "
    # 电商场景禁止
    "watermark, text, signature, logo, text distortion, bad typography, overlapping text, "
    "cheap look, cartoon"
)


def _to_image_input(path_or_url: str) -> str:
    """将本地路径或 URL 转为 base64 data URI 或原样返回 URL。"""
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url  # URL 或已编码的 data URI 直接透传
    p = Path(path_or_url)
    if not p.exists():
        raise FileNotFoundError(f"参考图文件不存在: {path_or_url}（解析路径: {p.resolve()}）")
    data = base64.b64encode(p.read_bytes()).decode()
    suffix = p.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix, "image/png")
    return f"data:{mime};base64,{data}"


def _to_base64_and_mime(path_or_url: str) -> tuple[str, str]:
    """返回 (base64_data, mime_type)。URL 会先下载；data URI 直接解包。"""
    if path_or_url.startswith("data:"):
        # data:{mime};base64,{data}
        header, b64 = path_or_url.split(",", 1)
        mime = header.split(";")[0].split(":", 1)[1]
        return b64, mime
    if path_or_url.startswith(("http://", "https://")):
        resp = requests.get(path_or_url, timeout=60)
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "image/png").split(";")[0]
        return base64.b64encode(resp.content).decode(), ct
    p = Path(path_or_url)
    if not p.exists():
        raise FileNotFoundError(f"参考图文件不存在: {path_or_url}（解析路径: {p.resolve()}）")
    suffix = p.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix, "image/png")
    return base64.b64encode(p.read_bytes()).decode(), mime


def _to_tongyi_image_entry(path_or_url: str) -> dict:
    """通义 messages content 中的 image 条目：URL/data URI 直传，本地文件转 base64 data URI。"""
    if path_or_url.startswith(("http://", "https://", "data:")):
        return {"image": path_or_url}
    p = Path(path_or_url)
    if not p.exists():
        raise FileNotFoundError(f"参考图文件不存在: {path_or_url}（解析路径: {p.resolve()}）")
    data = base64.b64encode(p.read_bytes()).decode()
    suffix = p.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix, "image/png")
    return {"image": f"data:{mime};base64,{data}"}

def generate_openai(key: str, prompt: str, base_url: str = "", model: str = "",
                    reference_image: str = "", **_kw) -> bytes:
    """OpenAI 图像生成 — 支持 dall-e-3 和 GPT Image (gpt-image-1.5 等)。

    reference_image: 可选，本地文件路径或 URL（多个用逗号分隔）。传入后使用 /v1/images/edits 端点（图生图）。
                    注意：dall-e-3 暂不支持 edits，请使用 gpt-image-1.5 或 gpt-image-1-mini。
    """
    if reference_image:
        # ── Edits 模式（图生图）────────────────────────────────────────────────────
        # 检测是否为 GPT Image 模型（支持 edits）
        is_gpt_image = model and model.startswith("gpt-image")
        if not is_gpt_image and model.startswith("dall-e"):
            # dall-e-3/dall-e-2 不支持 edits，警告并回退到纯文生图
            print(f"    ⚠️  OpenAI {model} 不支持参考图（edits），将忽略参考图使用纯文生图。", file=sys.stderr)
            print(f"    💡 如需图生图，请使用 GPT Image 模型（如 gpt-image-1.5）", file=sys.stderr)
            # 回退到纯文生图模式
            url = (base_url.rstrip("/") + "/v1/images/generations") if base_url else DEFAULT_URLS["openai"]
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "prompt": prompt, "size": "1024x1024", "quality": "hd", "response_format": "b64_json", "n": 1},
                timeout=_kw.get('request_timeout', 180),
            )
            resp.raise_for_status()
            return base64.b64decode(resp.json()["data"][0]["b64_json"])

        # GPT Image edits 模式
        url = (base_url.rstrip("/") + "/v1/images/edits") if base_url else "https://api.openai.com/v1/images/edits"

        # 解析多个参考图（逗号分隔）
        ref_images = [img.strip() for img in reference_image.split(",") if img.strip()]

        # OpenAI edits 要求 multipart/form-data
        # 多个图片用 image[] 数组格式
        files = []
        for i, ref_path in enumerate(ref_images):
            b64_data, mime = _to_base64_and_mime(ref_path)
            # requests 会自动处理相同 key 的多个字段（生成 image[] 格式）
            files.append(("image[]", (f"image{i}.{mime.split('/')[-1]}", base64.b64decode(b64_data), mime)))

        data = {
            "model": model,
            "prompt": prompt,
            "size": "1024x1024",
            "response_format": "b64_json",
            "n": 1,
        }

        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {key}"},
            files=files,
            data=data,
            timeout=_kw.get('request_timeout', 180),
        )
        resp.raise_for_status()
        return base64.b64decode(resp.json()["data"][0]["b64_json"])

    # ── 纯文生图模式────────────────────────────────────────────────────────────────
    url = (base_url.rstrip("/") + "/v1/images/generations") if base_url else DEFAULT_URLS["openai"]
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "prompt": prompt, "size": "1024x1024", "quality": "hd", "response_format": "b64_json", "n": 1},
        timeout=_kw.get('request_timeout', 180),
    )
    resp.raise_for_status()
    return base64.b64decode(resp.json()["data"][0]["b64_json"])


def generate_gemini(key: str, prompt: str, base_url: str = "", model: str = "",
                    reference_image: str = "", **_kw) -> bytes:
    """Gemini 原生图像生成，兼容官方 API 和代理。

    鉴权策略：
      - 官方 API（generativelanguage.googleapis.com）→ x-goog-api-key + ?key= query
      - 代理 API（自定义 base_url）→ Authorization: Bearer（多数代理的标准方式）

    reference_image: 可选，传入后作为 inline_data 参考图（原生格式）或 multipart image[]（OpenAI 格式）。

    2026.04 新增：兼容 OpenAI 格式的代理（检测 /v1/ 路径格式），支持 generations 和 edits 端点。
    """

    # Gemini 默认超时时间较长（edits 端点可能需要更长时间处理）
    gemini_timeout = _kw.get('request_timeout', 600)  # 默认 600 秒（10 分钟）

    # ── 检测是否为 OpenAI 兼容格式的代理 ──
    # 检测条件：base_url 包含 /v1/ 路径格式（如 /v1/images/generations）
    is_openai_format = base_url and "/v1/" in base_url

    if is_openai_format:
        # ── OpenAI 兼容格式 ──

        # 如果有参考图，使用 edits 端点
        if reference_image:
            url = base_url.rstrip("/") if base_url else base_url
            # 替换 generations 为 edits
            if "/images/generations" in url:
                url = url.replace("/images/generations", "/images/edits")
            elif not url.endswith("/images/edits"):
                url = url.rstrip("/") + "/images/edits"

            # 解析多个参考图（逗号分隔）
            ref_images = [img.strip() for img in reference_image.split(",") if img.strip()]

            # multipart/form-data with image[] array
            files = []
            for i, ref_path in enumerate(ref_images):
                b64_data, mime = _to_base64_and_mime(ref_path)
                files.append(("image[]", (f"image{i}.{mime.split('/')[-1]}", base64.b64decode(b64_data), mime)))

            data = {
                "model": model or "nano-banana",  # 通用代理常用模型
                "prompt": prompt,
                "n": 1,
            }

            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {key}"},
                files=files,
                data=data,
                timeout=gemini_timeout,
            )
            resp.raise_for_status()
            response_data = resp.json()

            # OpenAI 格式的响应：data[0].b64_json 或 data[0].url
            if "data" in response_data and len(response_data["data"]) > 0:
                img_data = response_data["data"][0]
                if "b64_json" in img_data:
                    return base64.b64decode(img_data["b64_json"])
                elif "url" in img_data:
                    img_resp = requests.get(img_data["url"], timeout=60)
                    img_resp.raise_for_status()
                    return img_resp.content

            raise RuntimeError(f"OpenAI 格式 edits 代理响应中未找到图片数据: {response_data}")

        # ── 无参考图：generations 端点 ──
        url = base_url.rstrip("/") if base_url else base_url
        # 确保路径是 /v1/images/generations
        if not url.endswith("/images/generations"):
            url = url.rstrip("/") + "/images/generations"

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

        # OpenAI 格式的请求体
        payload = {
            "model": model or "gemini-3.1-flash-image-preview",
            "prompt": prompt,
            "n": 1,
            "size": "1:1",  # 比率格式
            "quality": "low"
        }

        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=gemini_timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        # OpenAI 格式的响应：data[0].b64_json 或 data[0].url
        if "data" in data and len(data["data"]) > 0:
            img_data = data["data"][0]
            if "b64_json" in img_data:
                return base64.b64decode(img_data["b64_json"])
            elif "url" in img_data:
                img_resp = requests.get(img_data["url"], timeout=60)
                img_resp.raise_for_status()
                return img_resp.content

        raise RuntimeError(f"OpenAI 格式代理响应中未找到图片数据: {data}")

    # ── Gemini 原生格式 ──
    is_official = not base_url
    if base_url:
        url = base_url
    elif model and model != DEFAULT_MODELS["gemini"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    else:
        url = DEFAULT_URLS["gemini"]

    if is_official:
        req_url = f"{url}?key={key}" if "?" not in url else url
        headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    else:
        req_url = url
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    parts = []
    if reference_image:
        # 支持多张参考图（逗号分隔）
        ref_images = [img.strip() for img in reference_image.split(",") if img.strip()]
        for ref_img in ref_images:
            b64_data, mime = _to_base64_and_mime(ref_img)
            parts.append({"inline_data": {"mime_type": mime, "data": b64_data}})
        if len(ref_images) > 1:
            print(f"    📎 已传递 {len(ref_images)} 张参考图", flush=True)
    parts.append({"text": prompt})

    resp = requests.post(
        req_url,
        headers=headers,
        json={
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": "1:1",
                    "imageSize": "2K",
                },
            },
        },
        timeout=gemini_timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    for part in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise RuntimeError("Gemini 响应中未找到图片数据")


def generate_stability(key: str, prompt: str, base_url: str = "", model: str = "",
                       reference_image: str = "", **_kw) -> bytes:
    url = base_url or DEFAULT_URLS["stability"]
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        files={"none": ""},
        data={"prompt": prompt, "output_format": "jpeg", "aspect_ratio": "1:1"},
        timeout=_kw.get('request_timeout', 180),
    )
    resp.raise_for_status()
    return base64.b64decode(resp.json()["image"])


def _is_wan_model(model: str) -> bool:
    """判断是否为万象系列模型（wan2.x），使用异步接口。"""
    return model.startswith("wan")


def _tongyi_poll_task(key: str, task_id: str, max_wait: int = 300) -> str:
    """轮询通义异步任务，返回结果图片 URL。"""
    import time
    poll_url = "https://dashscope.aliyuncs.com/api/v1/tasks/" + task_id
    headers = {"Authorization": f"Bearer {key}"}
    elapsed = 0
    interval = 3
    while elapsed < max_wait:
        resp = requests.get(poll_url, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        status = result.get("output", {}).get("task_status", "")
        if status == "SUCCEEDED":
            # 万象模型返回两种格式：choices 或 results
            choices = result["output"].get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", [])
                if content:
                    return content[0].get("image", "")
            results = result["output"].get("results", [])
            if results:
                return results[0].get("url") or results[0].get("b64_image", "")
            raise RuntimeError(f"通义任务成功但无结果: {result}")
        if status in ("FAILED", "UNKNOWN"):
            raise RuntimeError(f"通义任务失败: {result}")
        time.sleep(interval)
        elapsed += interval
        interval = min(interval + 2, 10)
    raise TimeoutError(f"通义异步任务超时 ({max_wait}s): task_id={task_id}")


def generate_tongyi(key: str, prompt: str, base_url: str = "", model: str = "",
                    reference_image: str = "", negative_prompt: str = "",
                    request_timeout: int = 180, poll_max_wait: int = 600, **_kw) -> bytes:
    """通义图像生成 — 自动选择同步/异步接口。

    - wan2.7-image-pro 等万象模型：异步接口 (image-generation/generation)
    - qwen-image-2.0-pro 等千问模型：同步接口 (multimodal-generation/generation)

    两者均支持 reference_image（messages 中加入 image 条目）和 negative_prompt。
    """
    is_wan = _is_wan_model(model)

    # ── URL 选择 ──
    if base_url:
        url = base_url
    elif is_wan:
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
    else:
        url = DEFAULT_URLS["tongyi"]

    # ── 构建 messages content ──
    content = []
    if reference_image:
        # 支持多张参考图（逗号分隔）
        ref_images = [img.strip() for img in reference_image.split(",") if img.strip()]
        for ref_img in ref_images:
            content.append(_to_tongyi_image_entry(ref_img))
        if len(ref_images) > 1:
            print(f"    📎 已传递 {len(ref_images)} 张参考图", flush=True)
    content.append({"text": prompt})

    # ── 请求头 ──
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if is_wan:
        headers["X-DashScope-Async"] = "enable"

    # ── parameters ──
    params = {
        "size": "2048*2048" if is_wan else "1024*1024",
        "n": 1,
        "watermark": False,
    }
    if not is_wan:
        params["prompt_extend"] = False
    neg = negative_prompt or DEFAULT_NEGATIVE_PROMPT
    if neg:
        params["negative_prompt"] = neg[:500]  # 上限 500 字符

    body = {
        "model": model,
        "input": {
            "messages": [{"role": "user", "content": content}]
        },
        "parameters": params,
    }

    resp = requests.post(url, headers=headers, json=body, timeout=request_timeout)
    resp.raise_for_status()
    data = resp.json()

    if is_wan:
        # 异步模式：获取 task_id 后轮询
        task_id = data.get("output", {}).get("task_id", "")
        if not task_id:
            raise RuntimeError(f"通义万象未返回 task_id: {data}")
        print(f"    📡 万象异步任务 task_id={task_id}，轮询中...", flush=True)
        img_url = _tongyi_poll_task(key, task_id, max_wait=poll_max_wait)
        if img_url.startswith("data:") or len(img_url) > 500:
            # base64 返回
            return base64.b64decode(img_url.split(",", 1)[-1] if "," in img_url else img_url)
        return requests.get(img_url, timeout=request_timeout).content
    else:
        # 同步接口直接返回图片 URL
        img_url = data["output"]["choices"][0]["message"]["content"][0]["image"]
        return requests.get(img_url, timeout=request_timeout).content


_DOUBAO_ANTI_AI = (
    "authentic real-world photography, natural skin imperfections, genuine fabric texture, "
    "no synthetic look, no CGI quality, no heavy post-processing, no artificial colors, "
    "no mannequin appearance, candid natural lighting"
)


def generate_doubao(key: str, prompt: str, base_url: str = "", model: str = "",
                    reference_image: str = "", negative_prompt: str = "", **_kw) -> bytes:
    """豆包 Seedream（火山方舟）— 使用 ARK_API_KEY 鉴权。

    reference_image: 可选，本地文件路径或 URL。传入后作为参考图（图生图模式）。
    negative_prompt: Seedream API 不支持独立的 negative_prompt 字段，
                     此参数会被转化为正向"avoid..."描述追加到 prompt 末尾。
    """
    url = base_url or DEFAULT_URLS["doubao"]
    # Seedream 不支持 negative_prompt 字段；将反向意图转为正向约束追加
    effective_prompt = prompt.rstrip(". ") + ". " + _DOUBAO_ANTI_AI
    body = {
        "model": model,
        "prompt": effective_prompt,
        "size": "2048x2048",
        "response_format": "url",
        "watermark": False,
        "n": 1,
    }
    if reference_image:
        # 支持多张参考图（逗号分隔）
        ref_images = [img.strip() for img in reference_image.split(",") if img.strip()]
        body["image"] = [_to_image_input(ref) for ref in ref_images]
        if len(ref_images) > 1:
            print(f"    📎 已传递 {len(ref_images)} 张参考图", flush=True)
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=body,
        timeout=_kw.get('request_timeout', 180),
    )
    resp.raise_for_status()
    img_url = resp.json()["data"][0]["url"]
    return requests.get(img_url, timeout=_kw.get('request_timeout', 180)).content


GENERATORS = {
    "openai":    generate_openai,
    "gemini":    generate_gemini,
    "stability": generate_stability,
    "tongyi":    generate_tongyi,
    "doubao":    generate_doubao,
}

ENV_KEYS = {
    "openai":    "OPENAI_API_KEY",
    "gemini":    "GEMINI_API_KEY",
    "stability": "STABILITY_API_KEY",
    "tongyi":    "DASHSCOPE_API_KEY",
    "doubao":    "ARK_API_KEY",
}

ENV_URLS = {
    "openai":    "OPENAI_BASE_URL",
    "gemini":    "GEMINI_BASE_URL",
    "stability": "STABILITY_BASE_URL",
    "tongyi":    "DASHSCOPE_BASE_URL",
    "doubao":    "ARK_BASE_URL",
}

ENV_MODELS = {
    "openai":    "OPENAI_MODEL",
    "gemini":    "GEMINI_MODEL",
    "stability": "STABILITY_MODEL",
    "tongyi":    "DASHSCOPE_MODEL",
    "doubao":    "ARK_IMAGE_MODEL",
}

DEFAULT_MODELS = {
    "openai":    "dall-e-3",
    "gemini":    "gemini-3.1-flash-image-preview",
    "stability": "core",
    "tongyi":    "wan2.7-image-pro",
    "doubao":    "doubao-seedream-4-5-251128",
}


def resolve_model(provider: str, cli_model: str = "") -> str:
    """CLI --model > 环境变量 > 默认值"""
    return cli_model or os.environ.get(ENV_MODELS[provider], "") or DEFAULT_MODELS[provider]


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="电商套图图像生成脚本")
    parser.add_argument("--product",    required=True, help="商品 JSON 字符串")
    parser.add_argument("--provider",   required=True, choices=list(GENERATORS.keys()))
    parser.add_argument("--api-key",    default="", help="API Key（也可通过环境变量传入）")
    parser.add_argument("--base-url",   default="", help="自定义 Base URL（也可通过环境变量传入）")
    parser.add_argument("--model",      default="", help="模型名称（也可通过环境变量传入，否则用默认值）")
    parser.add_argument("--types",      default="white_bg,key_features,selling_pt,material,lifestyle,model,multi_scene",
                        help="逗号分隔的套图类型")
    parser.add_argument("--model-style", default="standard", choices=["standard", "bodycon"],
                        help="模特展示风格：standard（标准商拍）/ bodycon（贴身合体，适用于紧身衣物）")
    parser.add_argument("--model-image", default="", help="模特参考图路径或 URL（仅 model/lifestyle 类型使用，需供应商支持图生图）")
    parser.add_argument("--product-image", default="", help="商品参考图路径或 URL（单张，向后兼容；多张请用 --product-images）")
    parser.add_argument("--product-images", default="",
                        help="逗号分隔的商品参考图列表（按顺序：正面图,背面图,...）；正面图用于大多数图类型，背面图用于材质图")
    parser.add_argument("--template-set", type=int, default=1, choices=[1, 2, 3, 4, 5],
                        help="全局视觉风格模板：1=默认商拍 2=生活杂志 3=极简高冷 4=活力爆款 5=暗调质感")
    parser.add_argument("--per-type-templates", default="",
                        help="按图类型单独指定模板，格式：key_features:2,material:3（覆盖 --template-set）")
    parser.add_argument("--key-features-style", default="",
                        choices=["magnifier", "icon_list", "annotation", "split"],
                        help="核心卖点图独立样式（优先级高于 template_set）：magnifier=放大镜气泡 icon_list=信息图标列表 annotation=标注线指示 split=分割板块")
    parser.add_argument("--negative-prompt", default="", help="反向提示词，描述不希望在画面中出现的内容（上限500字符）")
    parser.add_argument("--lang", default="zh", choices=["zh", "en"],
                        help="图片内嵌文案语言：zh（中文，默认）/ en（英文，国际平台）")
    parser.add_argument("--output-dir", default="./output/",
                        help="输出目录，默认 ./output/")
    parser.add_argument("--request-timeout", type=int, default=180,
                        help="HTTP 请求超时时间（秒），默认 180s（Gemini 默认 600s）")
    parser.add_argument("--poll-max-wait", type=int, default=600,
                        help="通义万象异步任务最大轮询等待时间（秒），默认 600s")
    args = parser.parse_args()

    # Resolve API key
    api_key = args.api_key or os.environ.get(ENV_KEYS[args.provider], "")
    if not api_key:
        print(f"❌ 未找到 {args.provider} 的 API Key。请通过 --api-key 参数或环境变量 {ENV_KEYS[args.provider]} 传入。", file=sys.stderr)
        sys.exit(1)

    # Resolve base URL
    base_url = args.base_url or os.environ.get(ENV_URLS[args.provider], "")

    # Resolve model
    model = resolve_model(args.provider, args.model)
    print(f"📦 供应商: {args.provider}  模型: {model}")

    product = json.loads(args.product)

    # ── 字段规范化：兼容 analyze.py 旧版输出 ─────────────────────────────────
    # ① usage_scenes（旧版字段名）→ target_scenes
    if "usage_scenes" in product and "target_scenes" not in product:
        product["target_scenes"] = product["usage_scenes"]
    # ② product_style 降级：从 product_subtype / product_category 填充
    if not product.get("product_style"):
        product["product_style"] = (
            product.get("product_subtype") or product.get("product_category") or ""
        )

    # 兼容新旧两种 JSON 格式
    # 旧格式：product_description_for_prompt（直接描述字符串）
    # 新格式：product_name + visual_features（结构化字段）
    desc = product.get("product_description_for_prompt", "")
    if not desc:
        product_name = product.get("product_name", "product")
        vf = product.get("visual_features", {})
        if isinstance(vf, dict):
            # 新格式：从结构化字段拼接描述
            parts = [product_name]
            for key in ("main_color", "pattern", "neckline", "silhouette", "hemline", "fabric_texture"):
                val = vf.get(key)
                if val:
                    parts.append(val)
            desc = " ".join(parts)
        elif isinstance(vf, list):
            # 旧格式 visual_features 为数组
            desc = f"{product_name} {' '.join(vf[:4])}".strip()
        else:
            desc = product_name

    selling_points = product.get("selling_points", [])
    garment_position = product.get("garment_position", "non-apparel")
    # 目标场景和风格：从商品分析 JSON 中提取，用于场景展示图/多场景拼图动态生成
    target_scenes = product.get("target_scenes", [])
    product_style = product.get("product_style", "")
    # 新增字段（analyze.py ① 版本引入）
    print_design_lock = product.get("print_design_lock", "")
    target_audience = product.get("target_audience", "")
    target_scene_envs = product.get("target_scene_envs", [])
    product_type = product.get("product_type", "")
    types = [t.strip() for t in args.types.split(",")]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = GENERATORS[args.provider]
    results = {}

    # 解析 per-type 模板覆盖（格式：key_features:2,material:3）
    per_type_tpl: dict[str, int] = {}
    if args.per_type_templates:
        for pair in args.per_type_templates.split(","):
            pair = pair.strip()
            if ":" in pair:
                k, v = pair.split(":", 1)
                try:
                    per_type_tpl[k.strip()] = int(v.strip())
                except ValueError:
                    pass

    # 构建商品图列表（--product-images 优先，--product-image 作为兼容）
    if args.product_images:
        product_images = [p.strip() for p in args.product_images.split(",") if p.strip()]
    elif args.product_image:
        product_images = [args.product_image.strip()]
    else:
        product_images = []

    # 当只提供一张图片时，自动添加三角度拼图类型以实现360度展示
    if len(product_images) == 1 and "three_angle_view" not in types:
        print(f"📸 检测到仅提供一张商品图，将自动生成三角度拼图（正面/侧面/背面）以实现360度展示", flush=True)
        # 在 multi_scene 之前插入 three_angle_view
        try:
            idx = types.index("multi_scene")
            types.insert(idx, "three_angle_view")
        except ValueError:
            types.append("three_angle_view")

    input_image_type = product.get("input_image_type", "flat_lay")

    # 跟踪本次运行中已生成的模特图，用于后续 lifestyle/multi_scene 自动锁定模特
    _generated_model_img: str = ""

    for type_id in types:
        print(f"⏳ 生成 [{type_id}]...", flush=True)
        prompt = ""  # 在 try 外初始化，保证 except 里能引用
        try:
            # 根据图类型选择对应的商品参考图（正面/背面）
            slot = TYPE_IMAGE_SLOT.get(type_id, 0)
            product_ref = (
                product_images[slot] if slot < len(product_images)
                else (product_images[0] if product_images else "")
            )
            has_product_ref = bool(product_ref)

            # 模特/场景类：模特图锁定优先级
            #   1. --model-image 显式传入（最高优先级）
            #   2. 本次运行中刚生成的模特展示图（同一批次）
            #   3. output 目录已有的模特展示图（上次生成的，用于单独重新生成时）
            #   4. 商品参考图（兜底，无模特锁定）
            #
            # 重要：当有模特参考图时，同时传递商品参考图，确保AI知道要穿什么服装
            if type_id in ("model", "lifestyle", "multi_scene"):
                if args.model_image:
                    ref_img = args.model_image
                    has_model_ref = True
                    # 同时传递商品参考图（用逗号分隔，让AI同时参考模特和商品）
                    if product_ref:
                        ref_img = f"{args.model_image},{product_ref}"
                        print(f"    📎 双参考图: 模特图 + 商品图", flush=True)
                elif type_id != "model" and _generated_model_img:
                    ref_img = _generated_model_img
                    has_model_ref = True
                    # 同时传递商品参考图
                    if product_ref:
                        ref_img = f"{_generated_model_img},{product_ref}"
                        print(f"    🔒 双参考图: 本次模特图 + 商品图", flush=True)
                    else:
                        print(f"    🔒 锁定本次生成的模特图: {_generated_model_img}", flush=True)
                elif type_id != "model" and (output_dir / "模特展示图.jpg").exists():
                    ref_img = str((output_dir / "模特展示图.jpg").resolve())
                    has_model_ref = True
                    # 同时传递商品参考图
                    if product_ref:
                        ref_img = f"{ref_img},{product_ref}"
                        print(f"    🔒 双参考图: 已有模特图 + 商品图", flush=True)
                    else:
                        print(f"    🔒 自动使用已有模特图: {ref_img}", flush=True)
                else:
                    ref_img = product_ref
                    has_model_ref = False
            else:
                ref_img = product_ref
                has_model_ref = False

            tpl = per_type_tpl.get(type_id, args.template_set)
            # 获取 model_ethnicity（从 product 中，默认为 asian）
            model_ethnicity = product.get("model_ethnicity", "asian")
            prompt = build_prompt(type_id, desc, selling_points,
                                  model_style=args.model_style,
                                  has_model_ref=has_model_ref,
                                  lang=args.lang,
                                  garment_position=garment_position,
                                  print_design_lock=print_design_lock,
                                  has_product_ref=has_product_ref,
                                  input_image_type=input_image_type,
                                  template_set=tpl,
                                  key_features_style=args.key_features_style,
                                  per_type_templates=per_type_tpl,
                                  target_scenes=target_scenes,
                                  product_style=product_style,
                                  target_audience=target_audience,
                                  target_scene_envs=target_scene_envs,
                                  product_type=product_type,
                                  model_ethnicity=model_ethnicity)

            # 调试输出：验证参考图传递和 prompt 约束
            if ref_img:
                print(f"    📎 参考图: {ref_img} (has_product_ref={has_product_ref})", flush=True)
                if has_product_ref and "PRODUCT_REF_LOCK" in prompt:
                    print(f"    🔒 商品外观约束已启用", flush=True)
                # 临时调试：显示 prompt 前几个字符（验证约束存在）
                if "--debug" in sys.argv:  # 临时调试模式
                    preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
                    print(f"    📝 Prompt 预览: {preview}", flush=True)

            img_bytes = generator(api_key, prompt, base_url, model,
                                  reference_image=ref_img,
                                  negative_prompt=args.negative_prompt,
                                  request_timeout=args.request_timeout,
                                  poll_max_wait=args.poll_max_wait)
            zh_name = TYPE_NAMES_ZH.get(type_id, type_id)
            out_path = output_dir / f"{zh_name}.jpg"
            out_path.write_bytes(img_bytes)
            abs_path = str(out_path.resolve())
            results[type_id] = {"status": "ok", "path": abs_path, "name": zh_name}
            print(f"  ✅ 已保存到 {abs_path}")
            # 记录已生成的模特图，供后续 lifestyle/multi_scene 自动锁定
            if type_id == "model":
                _generated_model_img = abs_path
        except Exception as e:
            log_path = _write_error_log(output_dir, args.provider, type_id, prompt, e)
            results[type_id] = {"status": "error", "error": str(e), "log": str(log_path.resolve())}
            print(f"  ❌ 失败: {e}", file=sys.stderr)
            print(f"  📝 完整错误日志: {log_path}", file=sys.stderr)

    # Output summary JSON for downstream scripts
    summary_path = output_dir / "generate_result.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📋 生成结果摘要已保存到 {summary_path.resolve()}")

    ok = [k for k, v in results.items() if v["status"] == "ok"]
    fail = [k for k, v in results.items() if v["status"] == "error"]
    print(f"✅ 成功 {len(ok)} 张，❌ 失败 {len(fail)} 张")


if __name__ == "__main__":
    main()
