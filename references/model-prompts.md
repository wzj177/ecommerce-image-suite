# 模特图生成 Prompt 参考

适用于服装、鞋类商品的 `model` 和 `lifestyle` 图类型。
由 `generate.py` 在检测到品类为服装/鞋类时自动调用。

---

## 模特风格选择逻辑

```python
def auto_select_model_style(product_keywords: str) -> str:
    """根据商品关键词自动选择模特风格模板"""
    kw = product_keywords.lower()
    if any(w in kw for w in ["jk", "制服", "学院", "和风", "lolita", "汉服"]):
        return "asian_studio"
    if any(w in kw for w in ["男", "boy", "male", "先生", "男款"]):
        return "male_studio"
    if any(w in kw for w in ["欧美", "街头", "潮牌", "oversize", "hiphop"]):
        return "western_studio"
    return "neutral_white"  # 默认：最稳定，试穿效果最好
```

---

## 模特 Prompt 模板

```python
MODEL_PROMPTS = {
    # 亚洲模特（日系/学院/休闲风）
    "asian_studio": (
        "Young Asian female, {build} figure, standing upright, "
        "arms slightly away from body, neutral expression, facing camera, "
        "full body head to toe, pure white studio background, "
        "soft even lighting, photorealistic, high resolution, "
        "commercial fashion photography, no clothing"
    ),

    # 欧美模特（街头/潮牌风）
    "western_studio": (
        "Young Caucasian female model, {build} figure, "
        "relaxed natural pose, full body visible, "
        "light gray seamless background, natural soft light, "
        "photorealistic, fashion photography, no clothing"
    ),

    # 男款通用
    "male_studio": (
        "Young {ethnicity} male model, {build} build, standing straight, "
        "arms relaxed at sides, neutral expression, facing camera, "
        "full body head to toe, pure white background, "
        "studio lighting, photorealistic, no clothing"
    ),

    # 中性/通用（稳定性最高，试穿效果最好）
    "neutral_white": (
        "Female model, {build} figure, standing straight, "
        "arms relaxed at sides, pure white background, "
        "even studio lighting, full body, photorealistic, "
        "no clothing, neutral expression, facing forward"
    ),
}

BUILD_MAP = {
    "纤细": "slim",
    "标准": "average",
    "丰满": "plus-size",
}
```

---

## model 图（户外展示）Prompt 模板

用于最终套图中的 `model` 类型，模特已着装，户外场景：

```python
MODEL_SHOWCASE_PROMPTS = {
    # 国内平台（亚洲模特+户外）
    "domestic": (
        "Outdoor park with abundant sunlight. "
        "Young East-Asian female model, bright smile, confidently walking forward. "
        "Wearing {product_description}. "
        "Paired with light blue denim shorts. "
        "Product is absolute visual focus, youthful and energetic mood. "
        "Natural lighting, commercial fashion photography. "
        "Photorealistic, 8K. "
        "CRITICAL: keep the product EXACTLY the same — "
        "same print, same proportions, same color, do not modify any design detail."
    ),

    # 国际平台（多元模特+简洁背景）
    "international": (
        "Clean outdoor setting with natural soft light. "
        "Young female model, diverse appearance, natural smile, relaxed pose. "
        "Wearing {product_description}. "
        "Minimalist background, product-focused composition. "
        "Commercial fashion photography, photorealistic, 8K. "
        "CRITICAL: keep the product EXACTLY the same — "
        "same print, same proportions, same color, do not modify any design detail."
    ),

    # 贴身展示风格（强调服装合体贴合效果，适用于紧身内衣/泳装/健身服等品类）
    "bodycon_studio": (
        "Photorealistic full body front view e-commerce product main image. "
        "Young attractive {ethnicity} female model, {build} figure, "
        "wearing only this single-layer extremely tight form-fitting {product_description}, "
        "smooth elastic fabric seamlessly molding to natural figure, "
        "fabric directly clinging to skin highlighting garment construction and fit details. "
        "Professional studio fashion photography, clean lighting emphasizing clothing texture, "
        "seamless solid background, sharp focus on garment fit, "
        "commercial product shot, photorealistic, 8K. "
        "CRITICAL: keep the product EXACTLY the same — "
        "same print, same proportions, same color, do not modify any design detail."
    ),
}
```

---

## 服装图生成 Prompt（无图时文生图）

当用户没有商品图，只有文字描述时使用：

```python
GARMENT_FLAT_LAY_PROMPTS = {
    # 上衣类（T恤/衬衫/外套/卫衣）
    "top": (
        "{product_description}, "
        "flat lay on pure white background, "
        "studio lighting, top-down angle, "
        "full garment visible, neatly arranged, no wrinkles, "
        "sharp details, commercial e-commerce product photo, "
        "no text, no model, no watermarks, photorealistic, 8K"
    ),

    # 下装类（裤子/裙子）
    "bottom": (
        "{product_description}, "
        "flat lay on pure white background, "
        "neatly arranged, full length visible, "
        "studio lighting, top-down angle, "
        "sharp details, e-commerce product photo, "
        "no model, no text, photorealistic, 8K"
    ),

    # 套装（需分上衣 + 下装分别生成，再分别传给试穿 API）
    "set_top": (
        "{product_description} top piece only, "
        "flat lay on pure white background, "
        "studio lighting, top-down angle, "
        "full garment only, sharp details, no model, photorealistic, 8K"
    ),
    "set_bottom": (
        "{product_description} bottom piece only, "
        "flat lay on pure white background, "
        "studio lighting, full length visible, "
        "sharp details, no model, photorealistic, 8K"
    ),
}
```

---

## 品类 → Prompt 类型自动映射

```python
CATEGORY_TO_GARMENT_TYPE = {
    "t恤": "top", "t-shirt": "top", "衬衫": "top",
    "外套": "top", "卫衣": "top", "夹克": "top",
    "裤子": "bottom", "裙子": "bottom", "shorts": "bottom",
    "套装": "set_top",   # 套装会分两次生成
    "连衣裙": "top",     # 连衣裙视为整体上衣处理
    "鞋": "top",         # 鞋子用通用平铺逻辑
}
```
