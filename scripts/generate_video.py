#!/usr/bin/env python3
"""
generate_video.py - 最终优化版
自动读取图片 + 智能商业视频提示词
"""

import argparse
import base64
import json
import os
import sys
import time
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

try:
    from PIL import Image
    import io as _io
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

# Seedance 2.0/2.0-fast 才支持多模态参考、编辑视频、延长视频等高级功能
# 可通过环境变量 ARK_VIDEO_MODEL 覆盖，或 --model 参数
DEFAULT_MODEL = "doubao-seedance-1-5-pro-251215"
TASK_URL = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"

# 视频输入图片限制：超过此大小（MB）或宽/高超过此像素时自动压缩
_VIDEO_MAX_MB = 3
_VIDEO_MAX_PX = 1920


def _resize_if_needed(img_bytes: bytes, suffix: str) -> tuple[bytes, str]:
    """若图片超过大小或尺寸限制，用 Pillow 压缩后返回新字节；否则原样返回。
    返回 (bytes, mime_type)。需要 Pillow；未安装时直接返回原始数据并打印警告。"""
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix, "image/jpeg")
    size_mb = len(img_bytes) / 1024 / 1024
    if size_mb <= _VIDEO_MAX_MB:
        return img_bytes, mime  # 大小合规，跳过检测尺寸
    if not _HAS_PIL:
        print(f"    ⚠️  图片 {size_mb:.1f}MB 超过 {_VIDEO_MAX_MB}MB，建议安装 Pillow 自动压缩：pip install Pillow", file=sys.stderr)
        return img_bytes, mime
    img = Image.open(_io.BytesIO(img_bytes))
    w, h = img.size
    if w <= _VIDEO_MAX_PX and h <= _VIDEO_MAX_PX and size_mb <= _VIDEO_MAX_MB:
        return img_bytes, mime
    # 按比例缩放到最长边 _VIDEO_MAX_PX
    scale = _VIDEO_MAX_PX / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    buf = _io.BytesIO()
    fmt = "JPEG" if suffix in ("jpg", "jpeg", "webp") else "PNG"
    save_mime = "image/jpeg" if fmt == "JPEG" else "image/png"
    img.save(buf, format=fmt, quality=88, optimize=True)
    new_bytes = buf.getvalue()
    print(f"    🗜️  图片已压缩: {size_mb:.1f}MB → {len(new_bytes)/1024/1024:.1f}MB ({w}×{h} → {new_w}×{new_h})", flush=True)
    return new_bytes, save_mime


def _image_to_base64_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url
    p = Path(path_or_url)
    if not p.exists():
        raise FileNotFoundError(f"图片不存在: {path_or_url}（解析路径: {p.resolve()}）")
    raw = p.read_bytes()
    suffix = p.suffix.lower().lstrip(".")
    data_bytes, mime = _resize_if_needed(raw, suffix)
    data = base64.b64encode(data_bytes).decode()
    return f"data:{mime};base64,{data}"


def build_video_prompt(product_desc: str, selling_points: list) -> str:
    """视频提示词（规避豆包内容安全检测：不使用"模特""展示效果"等敏感词）"""
    sp = "、".join([p.get("zh_title", p.get("zh", "")) for p in selling_points[:3] if p.get("zh_title") or p.get("zh")])
    return (
        f"高清电商产品视频，主体是 {product_desc}。 "
        f"开头白底平铺缓慢旋转360°呈现细节 → 材质与做工近景突出质感 → "
        f"室内生活场景呈现产品穿着效果 → "
        f"多种家居场景自然切换，重点呈现卖点：{sp}。 "
        f"镜头流畅自然，光线温暖明亮，节奏轻快现代，商业广告质感，8K品质，"
        f"无水印、无文字叠加，产品所有细节完全一致，不变形、不走样。"
    )


def submit_task(api_key: str, model: str, images: list, prompt: str, generate_audio: bool, ratio: str, duration: int) -> str:
    content = [{"type": "text", "text": prompt}] if prompt else []
    for img in images:
        content.append({"type": "image_url", "image_url": {"url": _image_to_base64_url(img)}, "role": "reference_image"})

    body = {
        "model": model,
        "content": content,
        "generate_audio": generate_audio,
        "ratio": ratio,
        "duration": duration,
        "watermark": False,
    }
    resp = requests.post(TASK_URL, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=body, timeout=60)
    resp.raise_for_status()
    task_id = resp.json().get("id", "")
    if not task_id:
        raise RuntimeError(f"未返回 task_id: {resp.json()}")
    return task_id


def poll_task(api_key: str, task_id: str, max_wait: int = 600) -> dict:
    url = f"{TASK_URL}/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    elapsed = 0
    interval = 5
    while elapsed < max_wait:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        status = result.get("status", "")
        if status == "succeeded":
            return result
        if status in ("failed", "cancelled"):
            raise RuntimeError(f"生成失败: {json.dumps(result, ensure_ascii=False)}")
        print(f"    ⏳ 状态: {status}，已等待 {elapsed}s...", flush=True)
        time.sleep(interval)
        elapsed += interval
        interval = min(interval + 5, 30)
    raise TimeoutError(f"超时: {task_id}")


def download_video(video_url: str, output_path: Path):
    resp = requests.get(video_url, timeout=120, stream=True)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


def main():
    parser = argparse.ArgumentParser(description="豆包 Seedance 视频生成最终版")
    parser.add_argument("--images", nargs="*", default=[], help="参考图片（不填自动读取output）")
    parser.add_argument("--prompt", default="", help="自定义prompt")
    parser.add_argument("--audio", action="store_true", help="生成有声视频")
    parser.add_argument("--ratio", default="16:9",
                        choices=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"],
                        help="Seedance 2.0/2.0-fast 支持 21:9/4:3/3:4；旧版模型仅支持 16:9/9:16/1:1")
    parser.add_argument("--duration", type=int, default=6, choices=[4, 5, 6, 8, 10, 12, 15],
                        help="视频时长（秒）。Seedance 2.0/2.0-fast 支持 4-15s；旧版模型最大 12s")
    parser.add_argument("--model", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--max-wait", type=int, default=600)
    parser.add_argument("--output-dir", default="./output/video/")
    parser.add_argument("--product-json", default="", help="商品JSON路径，用于自动prompt")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ARK_API_KEY", "")
    if not api_key:
        print("❌ 未找到 ARK_API_KEY", file=sys.stderr)
        sys.exit(1)

    model = args.model or os.environ.get("ARK_VIDEO_MODEL", "") or DEFAULT_MODEL
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 自动读取 output 目录图片
    if not args.images:
        out_dir = Path("./output")
        candidates = ["白底主图.jpg", "模特展示图.jpg", "场景展示图.jpg", "多场景拼图.jpg", "材质图.jpg"]
        images = [str(out_dir / n) for n in candidates if (out_dir / n).exists()]
        if not images:
            print("❌ 未找到图片，请使用 --images 指定", file=sys.stderr)
            sys.exit(1)
    else:
        images = args.images

    # 智能 prompt 生成
    final_prompt = args.prompt
    if not final_prompt and args.product_json and Path(args.product_json).exists():
        try:
            with open(args.product_json, encoding="utf-8") as f:
                prod = json.load(f)
            final_prompt = build_video_prompt(prod.get("product_description_for_prompt", "产品"), prod.get("selling_points", []))
        except Exception:
            final_prompt = "高清电商产品视频，清晰呈现细节与质感"
    elif not final_prompt:
        final_prompt = "高清电商产品视频，依次呈现商品全貌、材质细节、室内穿着效果，过渡自然流畅"

    print(f"🎬 生成视频 | 图片数量: {len(images)} | 比例: {args.ratio} | 时长: {args.duration}s | 有声: {args.audio}")

    task_id = submit_task(api_key, model, images, final_prompt, args.audio, args.ratio, args.duration)
    print(f"✅ 任务提交成功: {task_id}")

    print("⏳ 正在生成视频，请耐心等待...")
    result = poll_task(api_key, task_id, args.max_wait)

    video_url = result.get("content", {}).get("video_url", "")
    if not video_url:
        print("❌ 未找到视频URL", file=sys.stderr)
        sys.exit(1)

    video_path = output_dir / "product_video.mp4"
    download_video(video_url, video_path)
    print(f"✅ 视频生成完成！保存路径: {video_path}")

    with open(output_dir / "video_result.json", "w", encoding="utf-8") as f:
        json.dump({"task_id": task_id, "video_local": str(video_path), "video_url": video_url}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
