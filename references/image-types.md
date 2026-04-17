# 电商套图：7种图片类型规格与 Prompt 模板

每种图类型均包含：视觉规格、文案规范、Prompt 模板（可编辑）。
**核心原则**：严格保持商品一致性，不得改动商品结构、颜色、比例及细节。

---

# 平台字体系统总览

| 平台 | 美学定位 | 字体风格 | 主色调 | 排版特征 |
|------|---------|---------|--------|---------|
| 淘宝/天猫 | 内容杂志风 | 衬线优雅体 | #2D2D2D 深灰 + #C8A86C 金沙 | 大字间距、精致装饰线 |
| 京东 | 技术规格美学 | 无衬线 + 等宽数据 | #1A1A1A 深黑 + #E4393C 京东红 | 数据化、胶囊标签 |
| 拼多多 | POP艺术冲击 | 超粗体 + 手写 | #E02E24 拼多多红 + #FFD700 金黄 | 高饱和、粗边框、大字号 |
| 抖音 | Neo-Brutalist拼贴 | 粗体 + 等宽故障 | #FE2C55 抖音红 + #25F4EE 抖音青 | 斜向、重叠、高对比 |
| Amazon | 高端目录风格 | 优雅衬线 | #2C2C2C 深灰 + #8B7355 大地棕 | 大量留白、目录式 |
| Shopify | DTC品牌美学 | 多样化（按tone） | 可配置品牌色 | 极简、现代、电影感 |

---

## 图1：白底主图（White Background Hero）

### 视觉规格
- **背景**：纯白（RGB 255,255,255），绝对纯净
- **商品占比**：90% 画面，居中
- **拍摄角度**：正面或轻微 45° 角
- **灯光**：干净工作室灯光，仅在商品下方有极轻微自然阴影
- **禁止**：任何环境、道具、装饰、文字水印

### 文案
- 无文字

### Prompt 模板（所有平台通用）
```
[PRODUCT_DESCRIPTION], displayed centered on pure white background (RGB 255,255,255),
product occupies 90% of frame, front view or slight 45-degree angle,
clean studio lighting with very subtle natural shadow underneath,
no props, no decorations, no text, photorealistic, high detail, commercial product photography, 8K quality.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color, do not modify any design detail.
```

### 替换变量
- `[PRODUCT_DESCRIPTION]`：如 "white loose-fit round-neck short-sleeve T-shirt with cute cartoon dog and 'CUTE' print"

---

## 图2：核心卖点图（Key Features / Icons）

### 视觉规格
- **背景**：浅色干净背景（米白/浅灰）
- **左侧**：商品完整正面外观，清晰展示（占画面 45-50%）
- **右侧**：3个现代极简线框图标，纵向排列
- **图标风格**：细线条 outline 风格，简洁现代

### 文案（英文版）
```
右上角：WHY CHOOSE US（主标题）
图标1副标题：Combed Cotton
图标2副标题：Loose & Breathable
图标3副标题：Cute Design
```

### 文案（中文版）
```
右上角：为什么选择我们
图标1副标题：精梳棉面料
图标2副标题：宽松透气
图标3副标题：萌趣设计
```

---

### 淘宝/天猫 Prompt（内容杂志风）

```
Clean product feature infographic with warm beige background (#FAF8F5).
Left side shows complete front view of [PRODUCT_DESCRIPTION] (45% of frame).
Right side layout: heading text "[为什么选择我们 / WHY CHOOSE US]" at top-right,
rendered in elegant serif font (Noto Serif SC / Playfair Display style),
42px size, letter-spacing 3px, deep charcoal color (#2D2D2D),
with delicate gold underline accent (#C8A86C, 2px thickness).
Below heading: 3 minimalist outline icons vertically arranged, each with a label:
"[FEATURE1]", "[FEATURE2]", "[FEATURE3]" in modern sans-serif font (Noto Sans SC),
18px size, soft gray text (#6B6B6B), 20px line spacing.
Warm, magazine-style typography with generous whitespace.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### 京东 Prompt（技术规格美学）

```
Technical product feature infographic with clean white background (#FFFFFF).
Left side shows complete front view of [PRODUCT_DESCRIPTION] (45% of frame).
Right side layout: heading text "[为什么选择我们 / WHY CHOOSE US]" at top-right,
rendered in bold UI font (Noto Sans SC), 36px size, pure black (#1A1A1A),
with technical subtitle in smaller 12px monospace font (Roboto Mono style),
letter-spacing 2px, uppercase, JD red accent (#E4393C).
Below heading: 3 minimalist outline icons vertically arranged, each with:
- Feature label in monospace font, 16px, dark gray (#5E5E5E)
- Data badge (pill shape, light gray background #F2F3F5, 4px radius)
- Technical precision, aligned grid layout.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### 拼多多 Prompt（POP艺术冲击）

```
Bold product feature infographic with warm off-white background (#FFF9F0).
Left side shows complete front view of [PRODUCT_DESCRIPTION] (45% of frame).
Right side layout: heading text "[为什么选择我们 / WHY CHOOSE US]" at top-right,
rendered in extra-bold font (Noto Sans SC, weight 900), 48px size,
vibrant Pinduoduo red (#E02E24), with 3px thick black outline.
Heading tilted -2 degrees for dynamic energy.
Below heading: 3 bold outline icons vertically arranged, each with:
- Feature label in extra-bold font, 24px, pure black (#1A1A1A)
- Yellow star burst accent (#FFD700) behind each icon
- High contrast, max impact, sale poster style.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### 抖音 Prompt（Neo-Brutalist拼贴）

```
Edgy product feature infographic with dark background (#161823).
Left side shows complete front view of [PRODUCT_DESCRIPTION] (45% of frame).
Right side layout: heading text "[为什么选择我们 / WHY CHOOSE US]" at top-right,
rendered in heavy bold font (Noto Sans SC, weight 900), 40px size,
pure white (#FFFFFF), with glitch effect:
- Cyan color split shadow (#25F4EE, offset 3px left)
- Red color split shadow (#FE2C55, offset 3px right)
Heading tilted -5 degrees.
Below heading: 3 brutalist icons vertically arranged, each with:
- Feature label in monospace font (JetBrains Mono style), 20px, white
- Hard shadow (4px, no blur, #FE2C55)
- High contrast, Gen Z aesthetic, raw energy.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### Amazon Prompt（高端目录风格）

```
Elegant product feature infographic with pure white background (#FFFFFF).
Left side shows complete front view of [PRODUCT_DESCRIPTION] (45% of frame).
Right side layout: heading text "[WHY CHOOSE US]" at top-right,
rendered in refined serif font (Playfair Display style),
38px size, letter-spacing 2px, deep charcoal (#2C2C2C),
with understated earth-tone underline (#8B7355, 1px thickness).
Below heading: 3 minimalist outline icons vertically arranged, each with:
- Feature label in clean sans-serif font (Source Sans Pro style), 16px
- Muted gray text (#6B6B6B), generous 24px line spacing
- Catalog-style elegance, minimal sophistication.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### Shopify Prompt（DTC品牌美学）

```
Modern product feature infographic with minimal off-white background (#F8F8F8).
Left side shows complete front view of [PRODUCT_DESCRIPTION] (45% of frame).
Right side layout: heading text "[WHY CHOOSE US]" at top-right,
rendered in modern geometric font (Inter / Space Grotesk style),
36px size, brand primary color ([BRAND_COLOR], default #1A1A1A),
letter-spacing 1px, subtle opacity 0.9.
Below heading: 3 refined outline icons vertically arranged, each with:
- Feature label in body font (Inter style), 16px, soft gray (#6B6B6B)
- Clean spacing (20px), rounded corners (8px) on icon containers
- DTC minimalism, contemporary, Instagram-worthy.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

## 图3：卖点图（Single Feature Highlight）

### 视觉规格
- **背景**：温馨舒适室内卧室，适度虚化（景深处理）
- **商品呈现**：平铺于柔软床铺 OR 隐藏面部模特穿着展示
- **重点**：宽大衣摆、落肩袖型，凸显宽松版型与休闲质感
- **光线**：柔和明亮，温馨感

### 文案（英文版）
```
左上方：LOOSE FIT DESIGN（主标题）
左下方1：Unrestricted Movement
左下方2：Comfortable and Flattering
```

### 文案（中文版）
```
左上方：宽松版型设计
左下方1：活动自如无束缚
左下方2：显瘦舒适两不误
```

---

### 淘宝/天猫 Prompt（内容杂志风）

```
Cozy bedroom interior, soft bokeh background, warm ambient lighting.
[PRODUCT_DESCRIPTION] laid flat on soft bed OR worn by faceless model showing oversized silhouette.
Focus on loose fit, dropped shoulders, relaxed drape.
Text layout:
- Main heading "[宽松版型设计 / LOOSE FIT DESIGN]" at upper-left,
  rendered in elegant serif font (Noto Serif SC / Playfair Display),
  52px size, letter-spacing 2px, deep charcoal (#2D2D2D),
  with gold accent underline (#C8A86C, 3px thickness, extends 60% of text width).
- Two captions below at lower-left: "[副标题1]" and "[副标题2]",
  rendered in modern sans-serif (Noto Sans SC), 18px size,
  soft gray (#6B6B6B), 24px line spacing, magazine-style typography.
Warm, lifestyle mood, refined elegance.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### 京东 Prompt（技术规格美学）

```
Cozy bedroom interior, soft bokeh background, warm ambient lighting.
[PRODUCT_DESCRIPTION] laid flat on soft bed OR worn by faceless model showing oversized silhouette.
Focus on loose fit, dropped shoulders, relaxed drape.
Text layout:
- Main heading "[宽松版型设计 / LOOSE FIT DESIGN]" at upper-left,
  rendered in bold UI font (Noto Sans SC, weight 700),
  44px size, pure black (#1A1A1A),
  with technical subtitle in 12px monospace (Roboto Mono style),
  uppercase, letter-spacing 3px, JD red (#E4393C).
- Two captions below at lower-left: "[副标题1]" and "[副标题2]",
  rendered in monospace font, 16px size,
  dark gray (#5E5E5E), with data badges (light gray background #F2F3F5).
Technical precision, data-driven presentation.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### 拼多多 Prompt（POP艺术冲击）

```
Cozy bedroom interior, soft bokeh background, warm ambient lighting.
[PRODUCT_DESCRIPTION] laid flat on soft bed OR worn by faceless model showing oversized silhouette.
Focus on loose fit, dropped shoulders, relaxed drape.
Text layout:
- Main heading "[宽松版型设计 / LOOSE FIT DESIGN]" at upper-left,
  rendered in extra-bold font (Noto Sans SC, weight 900),
  56px size, vibrant Pinduoduo red (#E02E24),
  with 4px thick black outline, tilted -3 degrees.
- Two captions below at lower-left: "[副标题1]" and "[副标题2]",
  rendered in extra-bold font, 24px size,
  pure black (#1A1A1A), with yellow highlight bursts (#FFD700).
High impact, bold, sale poster energy.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### 抖音 Prompt（Neo-Brutalist拼贴）

```
Cozy bedroom interior, soft bokeh background, warm ambient lighting.
[PRODUCT_DESCRIPTION] laid flat on soft bed OR worn by faceless model showing oversized silhouette.
Focus on loose fit, dropped shoulders, relaxed drape.
Text layout:
- Main heading "[宽松版型设计 / LOOSE FIT DESIGN]" at upper-left,
  rendered in heavy bold font (Noto Sans SC, weight 900),
  48px size, pure white (#FFFFFF),
  with glitch effect (cyan #25F4EE and red #FE2C55 color splits, 4px offset),
  tilted -8 degrees.
- Two captions below at lower-left: "[副标题1]" and "[副标题2]",
  rendered in monospace font (JetBrains Mono style), 20px size,
  white with hard shadows (6px, no blur, #FE2C55).
Raw, Gen Z energy, brutalist aesthetic.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### Amazon Prompt（高端目录风格）

```
Cozy bedroom interior, soft bokeh background, warm ambient lighting.
[PRODUCT_DESCRIPTION] laid flat on soft bed OR worn by faceless model showing oversized silhouette.
Focus on loose fit, dropped shoulders, relaxed drape.
Text layout:
- Main heading "[LOOSE FIT DESIGN]" at upper-left,
  rendered in refined serif font (Playfair Display style),
  46px size, letter-spacing 1px, deep charcoal (#2C2C2C),
  with subtle earth-tone accent (#8B7355, 2px underline).
- Two captions below at lower-left: "[副标题1]" and "[副标题2]",
  rendered in clean sans-serif (Source Sans Pro), 16px size,
  muted gray (#6B6B6B), 22px line spacing, catalog elegance.
Sophisticated, Williams-Sonoma catalog style.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### Shopify Prompt（DTC品牌美学）

```
Cozy bedroom interior, soft bokeh background, warm ambient lighting.
[PRODUCT_DESCRIPTION] laid flat on soft bed OR worn by faceless model showing oversized silhouette.
Focus on loose fit, dropped shoulders, relaxed drape.
Text layout:
- Main heading "[LOOSE FIT DESIGN]" at upper-left,
  rendered in modern font (Inter / Poppins style),
  42px size, brand primary color ([BRAND_COLOR]),
  letter-spacing 0.5px, subtle 0.9 opacity.
- Two captions below at lower-left: "[副标题1]" and "[副标题2]",
  rendered in body font (Inter style), 16px size,
  soft gray (#6B6B6B), 20px line spacing.
Minimal, contemporary, Allbirds/Glossier aesthetic.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

## 图4：材质图（Material / Texture Close-up）

### 视觉规格
- **风格**：微距特写摄影
- **构图**：商品部分折叠放置画面中央
- **灯光**：侧光打入，展现面料针织纹理与手感
- **道具**：可点缀纯净棉花植物，强化材质属性
- **焦点**：柔软织物表面的纹理细节

### 文案（英文版）
```
右上方：PREMIUM COMBED COTTON（主标题）
右中：Soft and Skin-friendly
右下：Keep Dry and Breathable
```

### 文案（中文版）
```
右上方：优质精梳棉
右中：亲肤柔软不刺激
右下：干爽透气，全天舒适
```

---

### 淘宝/天猫 Prompt（内容杂志风）

```
Macro photography style, [PRODUCT_DESCRIPTION] partially folded at center.
Directional side lighting highlighting knit fabric texture and softness.
Cotton plant props in background to emphasize natural material.
Text layout:
- Bold heading "[优质精梳棉 / PREMIUM COMBED COTTON]" at upper-right,
  rendered in elegant serif font (Noto Serif SC / Playfair Display),
  46px size, letter-spacing 2px, deep charcoal (#2D2D2D),
  with decorative gold vertical bar accent (|, #C8A86C, 4px width).
- Caption "[副标题1]" at mid-right: 18px, sans-serif, soft gray (#6B6B6B)
- Caption "[副标题2]" at lower-right: 18px, sans-serif, soft gray (#6B6B6B)
Captions with 20px line spacing, magazine-style refinement.
High clarity, sharp fabric texture, soft bokeh background.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
Commercial product photography, ultra-detailed, 8K.
```

---

### 京东 Prompt（技术规格美学）

```
Macro photography style, [PRODUCT_DESCRIPTION] partially folded at center.
Directional side lighting highlighting knit fabric texture and softness.
Cotton plant props in background to emphasize natural material.
Text layout:
- Bold heading "[优质精梳棉 / PREMIUM COMBED COTTON]" at upper-right,
  rendered in bold UI font (Noto Sans SC, weight 700),
  38px size, pure black (#1A1A1A),
  with technical data badge (pill shape, #F2F3F5 background, 4px radius, 12px monospace).
- Caption "[副标题1]" at mid-right: 16px, monospace, dark gray (#5E5E5E)
- Caption "[副标题2]" at lower-right: 16px, monospace, dark gray (#5E5E5E)
Technical precision, data visualization style.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
Commercial product photography, ultra-detailed, 8K.
```

---

### 拼多多 Prompt（POP艺术冲击）

```
Macro photography style, [PRODUCT_DESCRIPTION] partially folded at center.
Directional side lighting highlighting knit fabric texture and softness.
Cotton plant props in background to emphasize natural material.
Text layout:
- Bold heading "[优质精梳棉 / PREMIUM COMBED COTTON]" at upper-right,
  rendered in extra-bold font (Noto Sans SC, weight 900),
  50px size, vibrant Pinduoduo red (#E02E24),
  with 4px thick yellow outline (#FFD700).
- Caption "[副标题1]" at mid-right: 22px, extra-bold, pure black (#1A1A1A)
- Caption "[副标题2]" at lower-right: 22px, extra-bold, pure black
High contrast, bold, eye-catching.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
Commercial product photography, ultra-detailed, 8K.
```

---

### 抖音 Prompt（Neo-Brutalist拼贴）

```
Macro photography style, [PRODUCT_DESCRIPTION] partially folded at center.
Directional side lighting highlighting knit fabric texture and softness.
Cotton plant props in background to emphasize natural material.
Text layout:
- Bold heading "[优质精梳棉 / PREMIUM COMBED COTTON]" at upper-right,
  rendered in heavy bold font (Noto Sans SC, weight 900),
  42px size, pure white (#FFFFFF),
  with glitch effect (cyan #25F4EE and red #FE2C55 splits, 3px offset),
  tilted 5 degrees.
- Caption "[副标题1]" at mid-right: 18px, monospace, white, hard shadow (4px, #FE2C55)
- Caption "[副标题2]" at lower-right: 18px, monospace, white, hard shadow
Raw, edgy, Gen Z aesthetic.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
Commercial product photography, ultra-detailed, 8K.
```

---

### Amazon Prompt（高端目录风格）

```
Macro photography style, [PRODUCT_DESCRIPTION] partially folded at center.
Directional side lighting highlighting knit fabric texture and softness.
Cotton plant props in background to emphasize natural material.
Text layout:
- Bold heading "[PREMIUM COMBED COTTON]" at upper-right,
  rendered in refined serif font (Playfair Display style),
  40px size, letter-spacing 1px, deep charcoal (#2C2C2C),
  with elegant earth-tone period accent (. in #8B7355, 12px).
- Caption "[副标题1]" at mid-right: 16px, sans-serif (Source Sans Pro), muted gray (#6B6B6B)
- Caption "[副标题2]" at lower-right: 16px, sans-serif, muted gray
Catalog sophistication, generous spacing (24px).
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
Commercial product photography, ultra-detailed, 8K.
```

---

### Shopify Prompt（DTC品牌美学）

```
Macro photography style, [PRODUCT_DESCRIPTION] partially folded at center.
Directional side lighting highlighting knit fabric texture and softness.
Cotton plant props in background to emphasize natural material.
Text layout:
- Bold heading "[PREMIUM COMBED COTTON]" at upper-right,
  rendered in modern font (Inter / Poppins style),
  38px size, brand primary color ([BRAND_COLOR]),
  letter-spacing 0.5px, subtle 0.9 opacity.
- Caption "[副标题1]" at mid-right: 16px, body font (Inter), soft gray (#6B6B6B)
- Caption "[副标题2]" at lower-right: 16px, body font, soft gray
Clean, minimal, 20px line spacing.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
Commercial product photography, ultra-detailed, 8K.
```

---

## 图5：场景展示图（Lifestyle Scene）

### 视觉规格
- **场景**：⚠️ **必须来自商品分析的 `target_scenes`**，绝不写死固定场景
  - 示例：内衣/睡衣 → 卧室、梳妆台；运动服 → 健身房、跑道；礼服 → 宴会厅、浪漫餐厅
- **氛围**：与商品定位和目标场景匹配
- **搭配道具**：根据场景和卖点选择，不固定
- **商品呈现**：与道具自然搭配摆放或模特穿着
- **色调**：与场景氛围匹配

### 文案（动态生成，禁止写死）
```
左上方：[来自 product_style 或第3个卖点标题]
左下方1：[来自 target_scenes[0]]
左下方2：[来自 target_scenes[1] 或第2个卖点标题]
```

### ❌ 禁止使用的硬编码文案（仅适用于T恤，不适用其他品类）
```
❌ 日常减龄穿搭 / CASUAL EVERYDAY STYLE
❌ 校园首选 / Perfect for School
❌ 百搭轻松 / Easy to Match
❌ 阳光明媚的校园绿地
❌ 帆布包、笔记本电脑、复古耳机
```

---

### 淘宝/天猫 Prompt（内容杂志风）

```
Sunny campus green lawn or café wooden table surface, shallow depth of field lifestyle scene.
[PRODUCT_DESCRIPTION] paired with canvas bag, laptop or vintage headphones.
Young, casual, carefree atmosphere, bright natural lighting.
Text layout:
- Bold heading "[日常减龄穿搭 / CASUAL EVERYDAY STYLE]" at upper-left,
  rendered in elegant serif font (Noto Serif SC / Playfair Display),
  48px size, letter-spacing 2px,
  gradient fill from deep charcoal (#2D2D2D) to warm gray (#4A4A4A),
  with gold shadow effect (#C8A86C, 4px blur, offset 2px).
- Two smaller captions at lower-left: "[副标题1]" and "[副标题2]",
  rendered in modern sans-serif (Noto Sans SC), 18px size,
  white with subtle shadow (2px blur, 0.8 opacity), 20px line spacing.
Scene conveys youthful everyday styling, magazine-quality.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### 京东 Prompt（技术规格美学）

```
Sunny campus green lawn or café wooden table surface, shallow depth of field lifestyle scene.
[PRODUCT_DESCRIPTION] paired with canvas bag, laptop or vintage headphones.
Young, casual, carefree atmosphere, bright natural lighting.
Text layout:
- Bold heading "[日常减龄穿搭 / CASUAL EVERYDAY STYLE]" at upper-left,
  rendered in bold UI font (Noto Sans SC, weight 700),
  40px size, pure black (#1A1A1A),
  with technical tag (12px monospace, uppercase, JD red #E4393C, pill shape).
- Two smaller captions at lower-left: "[副标题1]" and "[副标题2]",
  rendered in monospace font, 16px size,
  white with sharp shadow (3px, no blur), 18px line spacing.
Clean, technical, data-driven lifestyle.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### 拼多多 Prompt（POP艺术冲击）

```
Sunny campus green lawn or café wooden table surface, shallow depth of field lifestyle scene.
[PRODUCT_DESCRIPTION] paired with canvas bag, laptop or vintage headphones.
Young, casual, carefree atmosphere, bright natural lighting.
Text layout:
- Bold heading "[日常减龄穿搭 / CASUAL EVERYDAY STYLE]" at upper-left,
  rendered in extra-bold font (Noto Sans SC, weight 900),
  52px size, vibrant Pinduoduo red (#E02E24),
  with 4px yellow outline (#FFD700) and black stroke (2px),
  tilted -4 degrees.
- Two smaller captions at lower-left: "[副标题1]" and "[副标题2]",
  rendered in extra-bold font, 22px size,
  white with red shadow (6px, #E02E24), high contrast.
Bold, energetic, sale poster style.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### 抖音 Prompt（Neo-Brutalist拼贴）

```
Sunny campus green lawn or café wooden table surface, shallow depth of field lifestyle scene.
[PRODUCT_DESCRIPTION] paired with canvas bag, laptop or vintage headphones.
Young, casual, carefree atmosphere, bright natural lighting.
Text layout:
- Bold heading "[日常减龄穿搭 / CASUAL EVERYDAY STYLE]" at upper-left,
  rendered in heavy bold font (Noto Sans SC, weight 900),
  44px size, pure white (#FFFFFF),
  with glitch effect (cyan #25F4EE and red #FE2C55 splits, 5px offset),
  tilted -10 degrees, multiple hard shadows (3px, white, cyan, red).
- Two smaller captions at lower-left: "[副标题1]" and "[副标题2]",
  rendered in monospace font (JetBrains Mono style), 20px size,
  white with hard shadow (5px, #FE2C55), raw energy.
Gen Z aesthetic, brutalist lifestyle.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### Amazon Prompt（高端目录风格）

```
Sunny campus green lawn or café wooden table surface, shallow depth of field lifestyle scene.
[PRODUCT_DESCRIPTION] paired with canvas bag, laptop or vintage headphones.
Young, casual, carefree atmosphere, bright natural lighting.
Text layout:
- Bold heading "[CASUAL EVERYDAY STYLE]" at upper-left,
  rendered in refined serif font (Playfair Display style),
  42px size, letter-spacing 1px, deep charcoal (#2C2C2C),
  with subtle shadow (3px blur, 0.3 opacity, #8B7355 tint).
- Two smaller captions at lower-left: "[副标题1]" and "[副标题2]",
  rendered in clean sans-serif (Source Sans Pro), 16px size,
  white with refined shadow (2px blur, 0.5 opacity), 22px line spacing.
Catalog elegance, Williams-Sonoma lifestyle style.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

### Shopify Prompt（DTC品牌美学）

```
Sunny campus green lawn or café wooden table surface, shallow depth of field lifestyle scene.
[PRODUCT_DESCRIPTION] paired with canvas bag, laptop or vintage headphones.
Young, casual, carefree atmosphere, bright natural lighting.
Text layout:
- Bold heading "[CASUAL EVERYDAY STYLE]" at upper-left,
  rendered in modern font (Inter / Poppins style),
  38px size, brand primary color ([BRAND_COLOR]),
  letter-spacing 0.5px, subtle 0.85 opacity.
- Two smaller captions at lower-left: "[副标题1]" and "[副标题2]",
  rendered in body font (Inter style), 16px size,
  white with soft shadow (2px blur, 0.6 opacity), 18px line spacing.
Minimal, Instagram-worthy, contemporary.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color.
```

---

## 图6：模特展示图（Model Showcase）

### 视觉规格
- **场景**：阳光充沛的户外公园
- **模特**：典型年轻中国面孔女性，面带灿烂微笑
- **穿搭**：商品（白色T恤）+ 浅蓝色牛仔短裤
- **姿态**：自信漫步，洋溢青春活力
- **焦点**：衣服是绝对视觉中心

### 文案
- 无文字

### Prompt 模板（所有平台通用）
```
Outdoor park with abundant sunlight.
Young Chinese female model with bright smile, confidently walking.
Wearing [PRODUCT_DESCRIPTION] with light blue denim shorts.
Product is absolute visual focus, youthful and energetic mood.
CRITICAL: keep the product EXACTLY the same — same print, same proportions, same color, do not modify any design detail.
Natural lighting, commercial fashion photography style.
```

---

## 图7：多场景拼图（Multi-Scene Split）

### 视觉规格
- **构图**：3格等比例拼图（推荐）或 左右2格分镜
- **场景**：⚠️ **必须来自商品分析的 `target_scenes`**，绝不写死"居家+户外"
  - 示例：睡衣 → 卧室/梳妆/浴后；运动服 → 健身/户外/瑜伽；礼服 → 约会/派对/婚礼
- **商品**：所有格中保持完全一致性（同一件商品）
- **模特**：同一人物始终出现，全身可见

### 专业拼图 Prompt 结构
```
[Commercial Product Showcase Collage] A single [产品描述] showcased across 3 distinct lifestyle scenes.
All panels: SAME product, SAME model (consistent East Asian female), full-body visible.
Scene ①: [target_scenes[0] 对应环境] — [标签], natural light, authentic interaction;
Scene ②: [target_scenes[1] 对应环境] — [标签], dynamic pose, genuine atmosphere;
Scene ③: [target_scenes[2] 对应环境] — [标签], scenic backdrop, full-body shot.
Layout: 3 equal vertical panels, thin white dividers.
Heading "[ms_heading]" at top. Bottom-left: "[ms_left]". Bottom-right: "[ms_right]".
```

### 文案（动态生成，禁止写死）
```
上方居中：[来自第3个卖点标题 或 通用多场景标题]
左下方：[来自 target_scenes[0]]
右下方：[来自 target_scenes[1]]
```

### ❌ 禁止使用的硬编码场景（仅适用于T恤/休闲服，不通用）
```
❌ 居家慵懒风 / Home Lounging
❌ 出游活力风 / Outdoor Outings
❌ 左侧：居家休闲（对睡衣是对的，但对礼服是错的）
❌ 右侧：户外出游（对运动服是对的，但对睡衣是错的）
```

---

### 淘宝/天猫 Prompt（内容杂志风）

```
Split-screen image divided by an elegant gold vertical line at center (2px, #C8A86C).
LEFT HALF: cozy warm home interior, soft diffused lighting, [PRODUCT_DESCRIPTION] in relaxed lounging setting.
RIGHT HALF: bright outdoor park, abundant natural sunlight, [PRODUCT_DESCRIPTION] in vibrant outdoor setting.
Text layout:
- Bold heading "[一件多穿，随心切换 / VERSATILE FOR ANY OCCASION]" centered at top,
  rendered in elegant serif font (Noto Serif SC / Playfair Display),
  44px size, letter-spacing 3px, deep charcoal (#2D2D2D),
  with gold shadow effect (#C8A86C, 3px blur, offset 2px).
- Bottom-left label "[居家慵懒风 / Home Lounging]" and bottom-right label "[出游活力风 / Outdoor Outings]",
  rendered in modern sans-serif (Noto Sans SC), 16px size,
  soft gray (#6B6B6B) with subtle shadow, 18px line spacing.
Magazine-style sophistication, warm elegance.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same in both halves — same print, same proportions, same color.
Photorealistic, commercial product photography, 8K quality.
```

---

### 京东 Prompt（技术规格美学）

```
Split-screen image divided by a sharp technical vertical line at center (2px, #E6E6E6).
LEFT HALF: cozy warm home interior, soft diffused lighting, [PRODUCT_DESCRIPTION] in relaxed lounging setting.
RIGHT HALF: bright outdoor park, abundant natural sunlight, [PRODUCT_DESCRIPTION] in vibrant outdoor setting.
Text layout:
- Bold heading "[一件多穿，随心切换 / VERSATILE FOR ANY OCCASION]" centered at top,
  rendered in bold UI font (Noto Sans SC, weight 700),
  38px size, pure black (#1A1A1A),
  with technical data badges (12px monospace, uppercase, JD red #E4393C, pill shape).
- Bottom-left label "[居家慵懒风 / Home Lounging]" and bottom-right label "[出游活力风 / Outdoor Outings]",
  rendered in monospace font, 14px size,
  dark gray (#5E5E5E) with light gray background (#F2F3F5), sharp edges.
Technical precision, clean grid layout.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same in both halves — same print, same proportions, same color.
Photorealistic, commercial product photography, 8K quality.
```

---

### 拼多多 Prompt（POP艺术冲击）

```
Split-screen image divided by a bold red vertical line at center (4px, #E02E24).
LEFT HALF: cozy warm home interior, soft diffused lighting, [PRODUCT_DESCRIPTION] in relaxed lounging setting.
RIGHT HALF: bright outdoor park, abundant natural sunlight, [PRODUCT_DESCRIPTION] in vibrant outdoor setting.
Text layout:
- Bold heading "[一件多穿，随心切换 / VERSATILE FOR ANY OCCASION]" centered at top,
  rendered in extra-bold font (Noto Sans SC, weight 900),
  48px size, vibrant Pinduoduo red (#E02E24),
  with 4px yellow outline (#FFD700), tilted -3 degrees.
- Bottom-left label "[居家慵懒风 / Home Lounging]" and bottom-right label "[出游活力风 / Outdoor Outings]",
  rendered in extra-bold font, 20px size,
  pure black (#1A1A1A) with yellow burst backgrounds (#FFD700).
High impact, bold, sale poster energy.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same in both halves — same print, same proportions, same color.
Photorealistic, commercial product photography, 8K quality.
```

---

### 抖音 Prompt（Neo-Brutalist拼贴）

```
Split-screen image divided by a glitchy cyan vertical line at center (3px, #25F4EE with red offset).
LEFT HALF: cozy warm home interior, soft diffused lighting, [PRODUCT_DESCRIPTION] in relaxed lounging setting.
RIGHT HALF: bright outdoor park, abundant natural sunlight, [PRODUCT_DESCRIPTION] in vibrant outdoor setting.
Text layout:
- Bold heading "[一件多穿，随心切换 / VERSATILE FOR ANY OCCASION]" centered at top,
  rendered in heavy bold font (Noto Sans SC, weight 900),
  40px size, pure white (#FFFFFF),
  with glitch effect (cyan #25F4EE and red #FE2C55 splits, 4px offset),
  tilted -6 degrees.
- Bottom-left label "[居家慵懒风 / Home Lounging]" and bottom-right label "[出游活力风 / Outdoor Outings]",
  rendered in monospace font (JetBrains Mono style), 18px size,
  white with hard shadows (4px, #FE2C55), raw energy.
Gen Z aesthetic, brutalist split.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same in both halves — same print, same proportions, same color.
Photorealistic, commercial product photography, 8K quality.
```

---

### Amazon Prompt（高端目录风格）

```
Split-screen image divided by a refined vertical line at center (1px, #E0E0E0).
LEFT HALF: cozy warm home interior, soft diffused lighting, [PRODUCT_DESCRIPTION] in relaxed lounging setting.
RIGHT HALF: bright outdoor park, abundant natural sunlight, [PRODUCT_DESCRIPTION] in vibrant outdoor setting.
Text layout:
- Bold heading "[VERSATILE FOR ANY OCCASION]" centered at top,
  rendered in refined serif font (Playfair Display style),
  38px size, letter-spacing 2px, deep charcoal (#2C2C2C),
  with subtle shadow (2px blur, 0.4 opacity).
- Bottom-left label "[居家慵懒风 / Home Lounging]" and bottom-right label "[出游活力风 / Outdoor Outings]",
  rendered in clean sans-serif (Source Sans Pro), 14px size,
  muted gray (#6B6B6B), generous spacing (20px).
Catalog elegance, minimal sophistication.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same in both halves — same print, same proportions, same color.
Photorealistic, commercial product photography, 8K quality.
```

---

### Shopify Prompt（DTC品牌美学）

```
Split-screen image divided by a clean vertical line at center (2px, #E8E8E8).
LEFT HALF: cozy warm home interior, soft diffused lighting, [PRODUCT_DESCRIPTION] in relaxed lounging setting.
RIGHT HALF: bright outdoor park, abundant natural sunlight, [PRODUCT_DESCRIPTION] in vibrant outdoor setting.
Text layout:
- Bold heading "[VERSATILE FOR ANY OCCASION]" centered at top,
  rendered in modern font (Inter / Poppins style),
  36px size, brand primary color ([BRAND_COLOR]),
  letter-spacing 1px, subtle 0.9 opacity.
- Bottom-left label "[居家慵懒风 / Home Lounging]" and bottom-right label "[出游活力风 / Outdoor Outings]",
  rendered in body font (Inter style), 14px size,
  soft gray (#6B6B6B), clean spacing (18px).
Minimal, contemporary, DTC aesthetic.
IMPORTANT: Render all specified text labels directly into the image.
CRITICAL: keep the product EXACTLY the same in both halves — same print, same proportions, same color.
Photorealistic, commercial product photography, 8K quality.
```

---

## 通用品质 Prompt 词库

### 画面品质
```
photorealistic, ultra-high definition, 8K resolution, commercial photography quality,
sharp details, professional lighting
```

### 服装类专用
```
fabric texture visible, natural drape, true-to-life colors,
no distortion of garment structure, consistent with original product
```

### 禁用词（避免AI改变商品）
```
CRITICAL: keep the product EXACTLY the same.
Do NOT alter the clothing design, color, print pattern, proportions, or any structural detail.
Same print, same proportions, same color throughout all images.
```

---

## 字体渲染增强词库

### 淘宝/天猫专用（杂志风）
```
elegant serif typography, refined letter-spacing, warm gold accents,
magazine-style layout, generous whitespace, sophisticated hierarchy
```

### 京东专用（技术风）
```
monospace data fonts, technical badges, precise alignment,
pill-shaped tags, grid layout, engineering aesthetic
```

### 拼多多专用（POP冲击）
```
extra-bold display type, high saturation colors, thick outlines,
dynamic angles, burst backgrounds, sale poster energy
```

### 抖音专用（Neo-Brutalist）
```
heavy brutalist typography, glitch effects, color splits,
hard shadows, raw aesthetic, Gen Z energy
```

### Amazon专用（目录风）
```
refined serif headings, clean sans-serif body, earth-tone accents,
catalog elegance, generous spacing, minimal sophistication
```

### Shopify专用（DTC美学）
```
modern geometric fonts, subtle opacity variations, clean minimal layout,
contemporary typography, Instagram-worthy style
```
