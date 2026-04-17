# 电商文案 & 详情页 Prompt 模板

## 通用说明

Agent 直接按以下模板生成平台文案和详情页 HTML，无需调用外部脚本。
将 `{product_json}` 替换为第二步生成的商品卖点 JSON，`{images_list}` 替换为已生成的套图列表。

---

## 一、平台文案 Prompt

### 系统 Prompt（所有平台通用）

```
你是一位专业电商文案策划师和转化率专家，精通各大平台规则。
严格按照指定平台要求输出文案，直接给出最终内容，不要任何说明、markdown或代码块。
```

---

### 淘宝/天猫 文案 Prompt

```
平台：淘宝/天猫
商品信息：{product_json}

请生成以下内容，严格按区块标注输出：

【标题】
- 主标题（≤30字，含核心关键词，格式：品牌/品类词+核心卖点+属性词）
- 副标题（≤25字，补充卖点或活动信息）

【核心卖点】
5条 bullet，每条格式：「关键词｜说明文字」，≤20字/条
侧重：情感价值 > 功能参数，强调"感受"而非"规格"

【详细描述】（400-550字）
结构：痛点共鸣 → 三大亮点 → 场景代入 → 促单背书

【搜索关键词】
20个，逗号分隔，含长尾词，覆盖：品类词+属性词+场景词+人群词

【类目属性标签】
10个，用于店铺标签和类目筛选
```

---

### 京东 文案 Prompt

```
平台：京东
商品信息：{product_json}

请生成以下内容，严格按区块标注输出：

【商品标题】
≤60字，格式：品牌+商品名+核心参数/材质+适用场景
突出品质背书，避免促销词，多用参数描述

【商品卖点（5条）】
每条 ≤15字，格式：「参数/材质名称：具体说明」
侧重：材质参数 > 情感表达，数据化、可验证

【商品描述】（400-600字，结构：定位 → 参数详解 → 工艺说明 → 售后背书）

【搜索关键词】
15个，偏向参数词和品类精准词，逗号分隔

【京东类目标签】
8个
```

---

### 拼多多 文案 Prompt

```
平台：拼多多
商品信息：{product_json}

请生成以下内容，严格按区块标注输出：

【商品标题】
≤30字，格式：核心品类词+最强卖点+价格锚点词（"超值""划算"等）
直白，不堆砌，第一眼看清是什么

【核心卖点（3条）】
极简风格，每条 ≤10字，直击利益点
如：「厂价直发，省中间商差价」「买2件减10元」

【商品描述】（150-200字）

【搜索关键词】
10个，精准品类词为主，逗号分隔
```

---

### 抖音电商 文案 Prompt

```
平台：抖音电商（抖店）
商品信息：{product_json}

请生成以下内容，严格按区块标注输出：

【视频标题/封面文案】
≤20字，口语化，情绪触发，适合短视频封面展示
格式参考：「这件T恤穿上真的瘦10斤！」「女朋友看到直接下单」

【商品标题（店铺展示用）】
≤20字，品类词+场景词+吸引点

【直播话术脚本】（3段，每段≤80字）

【商品描述（详情页）】
200-300字，口语化，场景代入感强，多用"你""我"第一人称

【话题标签】
8个，格式：#标签名，覆盖：品类标签+场景标签+人群标签+热门话题
```

---

### Amazon 文案 Prompt

```
Platform: Amazon
Market: {market}（US / UK / DE / JP / etc.）
Product Info: {product_json}

Generate the following, labeled by section:

[TITLE]
≤200 characters. Format: Brand + Main Keyword + Key Feature + Variant Info
Follow Amazon title policy: no promotional phrases ("best", "sale"), no all-caps
Capitalize first letter of each major word

[BULLET POINTS] (5 bullets)
Each bullet ≤255 characters. Start with a capitalized feature keyword followed by em dash.
Format: "FEATURE KEYWORD — Benefit-focused explanation with specific details"
Order: Most important benefit first. Cover: material, fit/size, function, care, compatibility/occasion

[PRODUCT DESCRIPTION]
150-300 words. Plain text, no HTML.
Structure: Hook sentence → 3 key benefits expanded → Use cases → Call to action
Use natural language optimized for A9 search algorithm.

[BACKEND SEARCH TERMS]
Total ≤250 bytes. Space-separated, no commas, no repetition of title words.
Include: synonyms, alternate spellings, related terms, Spanish terms (for US market)

[TAGS / BROWSE NODE KEYWORDS]
10 terms for Amazon browse node classification
```

---

### 独立站 / Shopify 文案 Prompt

```
Platform: Shopify / Independent Website
Language: {language}（EN / ZH / etc.）
Brand Tone: {brand_tone}（minimalist / playful / luxury / streetwear）
Product Info: {product_json}

Generate the following, labeled by section:

[SEO TITLE TAG]
≤60 characters. Format: Primary Keyword | Brand Name
Include target keyword naturally, no keyword stuffing

[META DESCRIPTION]
≤160 characters. Compelling, includes CTA ("Shop now", "Free shipping").
Contains primary keyword once naturally.

[PRODUCT PAGE H1]
≤70 characters. Brand voice, not just keyword. Memorable.

[PRODUCT DESCRIPTION - SHORT]
50-80 words. Used above the fold. Hook + top 2 benefits + CTA.
Scannable, emotional, brand voice consistent.

[PRODUCT DESCRIPTION - LONG]
200-350 words. Full storytelling version.
Structure: Story/problem → Product solution → Key features (3) → Social proof hint → Sizing/fit guide → CTA

[FEATURE BULLETS]
5 items, each 10-15 words. Benefit-first format.

[FAQ SECTION]
3 Q&A pairs covering: sizing, material/care, shipping
```

---

## 二、详情页 HTML Prompt

### 系统 Prompt（所有平台通用）

```
你是一位专业的电商前端开发工程师和视觉设计师，擅长创建具有独特美学和高度转化率的商品详情页。

请生成完整可用的 HTML 文件，包含内联 CSS，无需外部依赖。
直接输出 HTML 代码，不要任何 markdown 包裹或说明文字。
所有文案内容必须符合指定平台规范。

【文件路径说明】
- HTML 文件生成在：output/pages/{平台名}_detail.html
- 图片文件位于：output/ 目录（相对于 HTML 的上一级目录）
- 图片使用相对路径：../图片文件名.jpg

【图片文件映射】
- 白底主图.jpg → ../白底主图.jpg
- 核心卖点图.jpg → ../核心卖点图.jpg
- 卖点图.jpg → ../卖点图.jpg
- 材质图.jpg → ../材质图.jpg
- 场景展示图.jpg → ../场景展示图.jpg
- 模特展示图.jpg → ../模特展示图.jpg
- 多场景拼图.jpg → ../多场景拼图.jpg

【设计要求】
- 使用指定的 Web Fonts（通过 Google Fonts 或 CDN 引入）
- 实现独特的设计语言，避免通用模板感
- 加入 CSS 动画和微交互效果
- 图片使用相对路径（../图片名.jpg），价格用 [PRICE] 占位符
- 确保响应式设计，移动端优先
```

---

### 淘宝/天猫 详情页 HTML Prompt（内容杂志风）

```
平台：淘宝/天猫（手机端详情页）
美学定位：内容杂志风 - 参考 Kinfolk 杂志排版 + 天猫旗舰店品质感

商品信息：{product_json}
文案内容：{copy_json}
套图路径：{images_json}

生成手机端详情页 HTML，要求：

【技术规范】
- viewport: width=device-width, initial-scale=1.0
- 最大宽度 750px，居中显示
- 图片宽度 100%
- 纯内联 <style>，通过 @import 引入 Google Fonts

【字体系统】
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500&family=Oswald:wght@500;600&display=swap');

--font-heading: "Noto Serif SC", serif;           /* 衬线标题，杂志感 */
--font-body: "Noto Sans SC", sans-serif;          /* 现代正文 */
--font-accent: "Oswald", sans-serif;               /* 价格数字，几何感 */

【色彩系统】
:root {
  --color-bg: #FAF8F5;           /* 温暖米白，纸张质感 */
  --color-bg-alt: #F5F2ED;       /* 深米色区块 */
  --color-text: #2D2D2D;         /* 柔和深灰 */
  --color-text-light: #6B6B6B;   /* 次级文字 */
  --color-accent: #C8A86C;       /* 金沙色，品质感 */
  --color-price: #D94545;        /* 温暖价格红 */
  --color-tag-bg: #F0ECE6;       /* 标签背景 */
  --color-border: #E8E4DD;       /* 精致分隔线 */
}

【页面结构】（杂志式布局）

1. 品牌开场区
   - 全宽主图：../白底主图.jpg
   - 渐入动画（fadeUp 0.8s）
   - 图片下方 8px 细线 + 居中小装饰元素

2. 标题故事区
   - 大标题（32px, 衬线体, letter-spacing: 1px）
   - 副标题（14px, 浅色，行间距 1.8）
   - 价格区块（48px, Oswald字体，米色背景块，使用 [PRICE] 占位符）

3. 核心卖点 Banner
   - 3个图标，不对称布局（左侧 2 + 右侧 1）
   - 图标 + 标题 + 2行说明
   - 悬停微动效（translateY -2px）

4. 版型展示区（杂志排版）
   - 左侧：../卖点图.jpg（占 60%）
   - 右侧 40% 文案区（竖向居中）
   - 对角线装饰分隔

5. 材质工艺区
   - 上方：../材质图.jpg（全宽）
   - 下方参数表格（极简风格，竖线分隔）

6. 场景故事区（大图叙事）
   - ../场景展示图.jpg（全宽，无文字叠加）
   - 下方引用式文案（衬线斜体，大字号）

7. 模特展示区（画册风格）
   - ../模特展示图.jpg（全宽）
   - 下方小标签（"MODEL HEIGHT 165cm / WEARING SIZE M"）

8. 多场景拼贴区
   - ../多场景拼图.jpg
   - 网格标签标注场景

9. 规格参数表格
   - 精致表格，横线分隔
   - 参数名称（浅色）| 数值（深色加粗）

10. 品牌故事区
    - 大量留白，居中排版
    - 品牌标语（衬线体，24px）
    - 简短故事（150字，行间距 1.8）

【CSS 动效】
- 入场动画：fadeUp（渐显 + 上浮），交错延迟 0.1s 递增
- 图片悬停：scale(1.02) + box-shadow，0.3s ease
- 标签悬停：背景色加深，translateY(-2px)

【空间语法】
- 区块间距：48px（营造呼吸感）
- 标题上留白：64px（杂志式分隔）
- 内容两侧边距：20px（移动端）

【视觉细节】
- 装饰性分隔线（1px 实线 + 中心小圆点）
- 标签设计（8px 圆角，精致边框）
- 背景纹理（可选：细微噪点 overlay）
```

---

### 京东 详情页 HTML Prompt（技术规格美学）

```
平台：京东（手机端详情页）
美学定位：技术规格美学 - 参考 Apple 技术规格页 + 京东 PLUS 卡片

商品信息：{product_json}
文案内容：{copy_json}
套图路径：{images_json}

生成手机端详情页 HTML，要求：

【技术规范】
- viewport: width=device-width, initial-scale=1.0
- 最大宽度 750px，居中显示
- 纯内联 <style>，引入 Web Fonts

【字体系统】
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Source+Han+Serif+SC:wght@400;700&family=Roboto+Mono:wght@400;500&display=swap');

--font-ui: "Noto Sans SC", sans-serif;           /* UI 字体 */
--font-serif: "Source Han Serif SC", serif;      /* 参数区衬线 */
--font-mono: "Roboto Mono", monospace;           /* 数据展示 */

【色彩系统】
:root {
  --color-bg: #FFFFFF;              /* 纯白背景 */
  --color-bg-alt: #F7F8FA;          /* 浅灰区块 */
  --color-text: #1A1A1A;            /* 深黑文字 */
  --color-text-secondary: #5E5E5E;  /* 次级文字 */
  --color-primary: #E4393C;         /* 京东红 */
  --color-blue: #2E68E9;            /* 信任蓝 */
  --color-gold: #C8A86C;            /* PLUS 金 */
  --color-border: #E6E6E6;          /* 精确边框 */
  --color-mono-bg: #F2F3F5;         /* 代码背景 */
}

【页面结构】（工程美学布局）

1. 产品规格卡片区
   - ../白底主图.jpg（全宽）
   - 下方产品名称（17px, 字重 700）
   - 参数标签（"精梳棉 · 宽松版型 · 短袖"）

2. 核心参数网格
   - 3列等宽网格
   - 参数名（12px, 浅色，mono字体）
   - 参数值（20px, 加粗）
   - 数据可视化风格

3. 材质详解区（技术图表）
   - 左侧：../材质图.jpg（占 50%）
   - 右侧参数对比表
   - 表格样式：竖线分隔，斑马纹行

4. 版型工程图区
   - ../卖点图.jpg
   - 技术标注线（CSS 绘制）
   - 尺寸标注（mono字体）

5. 工艺说明区
   - 标题（"工艺说明" + 英文 "CRAFTSMANSHIP"）
   - 图标 + 说明列表
   - 等宽字体技术参数

6. 场景应用区
   - ../场景展示图.jpg
   - 适用场景标签（胶囊样式）

7. 模特数据展示区
   - ../模特展示图.jpg
   - 模特数据卡（身高 / 体重 / 试穿尺码）

8. 多场景对比区
   - ../多场景拼图.jpg
   - 场景编号标签（01, 02, 03）

9. 完整规格表（工程制表）
   - 双列表格：参数名 | 参数值
   - 参数名（右对齐，浅色）
   - 参数值（左对齐，加粗）

10. 品质保障区（PLUS 风格）
    - 4列图标网格
    - 标题 + 英文 subtitle
    - 金色强调元素

【视觉细节】
- 精确 1px 边框（#E6E6E6）
- 数据展示用等宽字体
- 参数标签用胶囊样式（浅灰背景，圆角 4px）
- 技术标注线（细线 + 小圆点）
- 英文 subtitle（8px, 全大写, letter-spacing: 2px）

【CSS 动效】
- 数据卡入场：scaleIn（从中心展开）
- 表格行悬停：背景色变化
- 参数标签悬停：边框色变京东红
```

---

### 拼多多 详情页 HTML Prompt（POP 艺术冲击）

```
平台：拼多多（手机端详情页）
美学定位：POP 艺术冲击 - 参考 好市多广告 + 抖音电商卡片

商品信息：{product_json}
文案内容：{copy_json}
套图路径：{images_json}

生成手机端详情页 HTML，要求：

【技术规范】
- viewport: width=device-width, initial-scale=1.0
- 最大宽度 750px，居中显示
- 纯内联 <style>，引入 Web Fonts

【字体系统】
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&family=ZCOOL+KuaiLe&display=swap');

--font-bold: "Noto Sans SC", sans-serif;       /* 粗体强调 */
--font-fun: "ZCOOL KuaiLe", cursive;           /* 手写趣味 */

【色彩系统】
:root {
  --color-bg: #FFF9F0;           /* 暖白背景 */
  --color-bg-red: #FFE5E5;       /* 红色区块 */
  --color-text: #1A1A1A;         /* 深黑 */
  --color-red: #E02E24;          /* 拼多多红 */
  --color-red-dark: #C41E15;     /* 深红 */
  --color-yellow: #FFD700;       /* 价格黄 */
  --color-tag-red: #FFF0F0;      /* 标签红底 */
}

【页面结构】（高冲击力布局）

1. 爆款开场区
   - ../白底主图.jpg（全宽）
   - 右上角"爆款"标签（红色旋转标签）
   - 闪烁边框动画

2. 价格爆破区
   - 超大价格（72px, 粗体, 红色，使用 [PRICE] 占位符）
   - "限时特惠"标签（黄色背景，抖动动画）
   - 原价删除线（24px）

3. 三大卖点（大字号冲击）
   - 3条卖点，每条 28px
   - 红色圆点序号
   - 简短有力（"厂价直发！" "买2减10！" "7天无理由！"）

4. 商品展示区（双图并排）
   - 左侧：../卖点图.jpg
   - 右侧：../材质图.jpg
   - 图片边框 3px 红色实线

5. 场景展示区
   - ../场景展示图.jpg（全宽）
   - 下方"适用场景"大标题

6. 规格参数（极简表格）
   - 4行参数（颜色 | 尺码 | 材质 | 洗涤）
   - 红色竖线分隔

7. 保障区（简洁有力）
   - 3列图标：正品认证 | 7天退换 | 包邮
   - 红色 ✓ 勾标

【视觉细节】
- 高饱和度颜色
- 粗边框（3px 红色实线）
- 旋转标签（"爆款""限时""特惠"）
- 价格爆破效果（黄色星burst背景）
- 抖动动画（价格标签）

【CSS 动效】
- 旋转标签：rotate 360°（2s 无限循环）
- 抖动：shake 0.5s（价格标签）
- 脉冲：pulse 1.5s（"立即抢购"按钮）
- 闪烁：blink 1s（"限时"标签）
```

---

### 抖音电商 详情页 HTML Prompt（Neo-Brutalist 拼贴）

```
平台：抖音电商（抖店详情页，竖版）
美学定位：Neo-Brutalist 拼贴 - 参考 TikTok 原生卡片 + Depop 独立站

商品信息：{product_json}
文案内容：{copy_json}
套图路径：{images_json}

生成竖版手机端详情页 HTML，要求：

【技术规范】
- viewport: width=device-width, initial-scale=1.0
- 最大宽度 450px（竖屏优化），居中显示
- 纯内联 <style>，引入 Web Fonts

【字体系统】
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&family=JetBrains+Mono:wght@400;700&display=swap');

--font-main: "Noto Sans SC", sans-serif;       /* 主字体 */
--font-mono: "JetBrains Mono", monospace;      /* 等宽数据 */

【色彩系统】
:root {
  --color-bg: #161823;             /* 抖音深色 */
  --color-bg-alt: #1F222E;         /* 深灰区块 */
  --color-text: #FFFFFF;           /* 白色文字 */
  --color-text-muted: #A0A4B8;     /* 灰色文字 */
  --color-red: #FE2C55;            /* 抖音红 */
  --color-cyan: #25F4EE;           /* 抖音青 */
  --color-yellow: #FFD700;         /* 亮黄强调 */
}

【页面结构】（拼贴层叠布局）

1. 封面冲击区（全屏视觉）
   - ../场景展示图.jpg（全宽）
   - 撞色标题叠加（白色文字 + 黑色描边）
   - 标题字体 42px, 粗体, 斜向 -3deg

2. 种草亮点区（emoji + 口语）
   - 3个卖点，大字号 24px
   - emoji 前缀（🔥 ✨ 💡）
   - 口语化短句（"这件穿出去回头率超高！"）

3. 上身效果区（全宽大图）
   - ../模特展示图.jpg（全宽）
   - 底部渐变遮罩
   - "真实上身效果"标签（青色边框）

4. 细节展示区（拼贴网格）
   - 左上：../材质图.jpg
   - 右下：../卖点图.jpg
   - 错落布局，重叠阴影

5. 多场景区（全宽）
   - ../多场景拼图.jpg
   - 场景标签（"日常 | 约会 | 运动"）

6. 购买引导区（强 CTA）
   - 价格（48px, 黄色，使用 [PRICE] 占位符）
   - "限时特惠"标签（红色闪烁）
   - "立即抢购"按钮（渐变红 → 青，大字号 32px）

【视觉细节】
- 故障风效果（文字错位 + 色彩分离）
- 拼贴阴影（hard shadow, 无模糊）
- 高对比度边框（3px 实线，白色/青色）
- 粗体字重（700-900）
- 斜向元素（文字 -3deg，分隔线斜切）
- 斑马纹背景（深色/深灰交替）

【CSS 动效】
- 故障效果：文字 x/y 偏移 + 色彩分离（0.1s 闪动）
- 按钮渐变：background-position 动画
- 标签闪烁：opacity 0.5-1 循环
- 图片悬停：scale(1.05) + rotate(1deg)

【特殊元素】
- 进度条（库存/销量）
- 倒计时器（等宽字体，跳动效果）
- 音符装饰元素（🎵 悬浮动画）
```

---

### Amazon A+ Content HTML Prompt（高端目录风格）

```
Platform: Amazon A+ Content
美学定位：高端目录风格 - 参考 Williams-Sonoma 目录 + Patagonia A+ 内容

Product Info: {product_json}
Copy Content: {copy_json}
Image Paths: {images_json}

Generate Amazon A+ Content HTML following Amazon's module structure:

【Technical Requirements】
- Standard A+ width: 970px max (desktop), must be responsive
- No JavaScript, no external resources, no iframes
- Images: 使用相对路径 ../图片文件名.jpg
- Amazon allows: p, h1-h6, ul, ol, li, table, img, br, strong, em
- No: div positioning, flexbox/grid (use table layout for multi-column)

【Font System】
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+Pro:wght@300;400;600&display=swap');

--font-heading: "Playfair Display", serif;      /* 优雅衬线标题 */
--font-body: "Source Sans Pro", sans-serif;     /* 现代正文 */

【Color System】
:root {
  --color-bg: #FFFFFF;              /* 纯白背景 */
  --color-bg-alt: #FAFAFA;          /* 极浅灰区块 */
  --color-text: #2C2C2C;            /* 深灰（非纯黑） */
  --color-text-light: #6B6B6B;      /* 次级文字 */
  --color-accent: #8B7355;          /* 大地棕 */
  --color-accent-hover: #6B5B45;    /* 深棕 */
  --color-border: #E0E0E0;          /* 精致边框 */
}

【Module Structure】（优雅目录布局）

1. Hero Banner Module
   - Full-width image: ../场景展示图.jpg（使用相对路径）
   - Elegant overlay headline (Playfair Display, 42px)
   - Subtle gradient overlay (bottom to top)
   - Brand tagline in italic

2. Feature Highlight Module (3 columns, table layout)
   - Column 1: ../材质图.jpg + "PREMIUM MATERIAL" + description
   - Column 2: ../卖点图.jpg + "THOUGHTFUL DESIGN" + description
   - Column 3: ../核心卖点图.jpg + "CRAFTSMANSHIP" + description
   - Ample whitespace between columns

3. Product Story Module (2-column table)
   - Left: ../模特展示图.jpg (60% width)
   - Right: H2 headline + 150-word brand story (40% width)
   - Refined typography (line-height 1.8, letter-spacing 0.5px)

4. Comparison/Specification Table
   - Clean table layout, alternating row colors (#FAFAFA)
   - Top header row with accent color background
   - Thin borders (1px, #E0E0E0)
   - Right-aligned numbers

5. Multi-Scene Module
   - ../多场景拼图.jpg（full width，使用相对路径）
   - Elegant caption below (italic, Playfair Display)
   - "VERSATILE FOR ANY OCCASION"

【Visual Details】
- Generous whitespace (60px+ section padding)
- Elegant borders (1px, subtle colors)
- Refined typography (hierarchy via size/weight)
- Subtle background textures (optional: fine noise overlay)
- Center alignment for headings

【Schema.org Product JSON-LD】
Include in <script type="application/ld+json">:
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "[product name]",
  "description": "[meta description]",
  "brand": {"@type": "Brand", "name": "[brand]"},
  "material": "[material]"
}
```

---

### 独立站 / Shopify 详情页 HTML Prompt（DTC 品牌美学）

```
Platform: Shopify / Independent Website
美学定位：DTC 品牌美学 - 参考 Allbirds / Glossier / Muji

Language: {language}
Brand Tone: {brand_tone}
Product Info: {product_json}
Copy Content: {copy_json}
Image Paths: {images_json}

Generate a complete standalone product page HTML file:

【Technical Requirements】
- Full HTML5 document with <head> including all SEO meta tags
- Responsive: mobile-first, breakpoints at 768px, 1024px, 1440px
- Internal <style> block only, no external CSS frameworks
- Optional: vanilla JavaScript for image gallery and FAQ accordion
- Images: 使用相对路径 ../图片文件名.jpg

【Font System】（基于 brand_tone 匹配）
- minimalist/luxury: "Inter" + "Playfair Display"
- playful: "Poppins" + "Space Grotesk"
- streetwear: "Oswald" + "Roboto Condensed"

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap');

【Color System】（可配置，基于品牌色）
:root {
  --color-bg: #FFFFFF;
  --color-bg-alt: #F8F8F8;
  --color-text: #1A1A1A;
  --color-text-light: #6B6B6B;
  --color-primary: [BRAND_COLOR];    /* 占位符，默认 #1A1A1A */
  --color-accent: [ACCENT_COLOR];    /* 占位符，默认 #6C63FF */
  --color-border: #E8E8E8;
  --spacing-unit: 8px;
}

【SEO Requirements】
- <title>: SEO title from copy_json (≤60 chars)
- <meta name="description">: from copy_json (≤160 chars)
- <meta property="og:title">: Open Graph title
- <meta property="og:description">: description
- <meta property="og:image">: ../白底主图.jpg（相对路径）
- <link rel="canonical">: [CANONICAL_URL] placeholder
- Schema.org Product JSON-LD (full spec)

【Page Layout】（电影感叙事）

1. Header
   - Minimal nav: [BRAND_LOGO] (left) + Cart icon (right)
   - Sticky on scroll (backdrop blur)

2. Product Hero Section (2-column desktop)
   - Left: Image gallery (main image: ../白底主图.jpg + 3 thumbnails)
   - Right: H1 (32-40px) + price (24px, accent color, 使用 [PRICE] 占位符) + short description + size selector + "Add to Cart" button

3. Feature Strips
   - 3-column icon grid: material | fit | design
   - Minimal icon style (outline icons)

4. Product Story Section
   - ../场景展示图.jpg（full width，使用相对路径，parallax effect on desktop）
   - Long-form description (200-350 words, line-height 1.8)

5. Feature Detail Rows (alternating zigzag)
   - Row 1: ../卖点图.jpg left (50%) + text right (50%)
   - Row 2: text left (50%) + ../材质图.jpg right (50%)

6. Model/Lifestyle Gallery
   - ../模特展示图.jpg + ../多场景拼图.jpg（2-column grid，使用相对路径）

7. FAQ Section
   - 3 Q&A pairs (accordion with vanilla JS)
   - Question (bold, cursor pointer) + Answer (hidden by default)

8. Footer
   - Newsletter signup + social links + copyright

【CSS Design System】
- 8px spacing grid
- Max content width: 1200px
- Section padding: 80px (desktop) / 40px (mobile)
- Border radius: 4px (minimal) or 0 (sharp)
- Transition: 0.2s ease (all interactive elements)

【Micro-interactions】
- Button hover: background darken + translateY(-1px)
- Image gallery hover: scale(1.03)
- FAQ accordion: smooth height transition
- Scroll animations: fade-in elements as they enter viewport

【Optional JavaScript】
- Image gallery thumbnail switching
- FAQ accordion toggle
- Smooth scroll for anchor links
```

---

## 三、平台选择影响矩阵

Agent 在生成前应按此矩阵确认平台，不做跨平台兼容：

| 平台 | 文案语言 | 文案风格 | 详情页类型 | 美学定位 | 特殊处理 |
|------|---------|---------|-----------|---------|---------|
| 淘宝/天猫 | 中文 | 情感化 | 手机端HTML | 内容杂志风 | 需促销话术，衬线字体 |
| 京东 | 中文 | 参数化 | 手机端HTML | 技术规格美学 | 需品质背书，等宽字体 |
| 拼多多 | 中文 | 极简价格导向 | 手机端HTML | POP艺术冲击 | 字数最少，高饱和度 |
| 抖音 | 中文 | 口语+直播话术 | 手机端HTML | Neo-Brutalist | 额外生成直播话术，故障风 |
| Amazon | 英文（按市场） | A9关键词优化 | A+ Content HTML | 高端目录风格 | Search Terms字段 |
| 独立站 | 按语言参数 | 品牌叙事 | 完整SEO HTML | DTC品牌美学 | Schema.org + OG |
