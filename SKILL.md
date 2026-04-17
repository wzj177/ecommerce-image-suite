---
name: ecommerce-image-suite
description: >
  电商套图生成助手。用户明确提出需要生成电商套图、商品主图、卖点图、场景图、模特图等图片内容时触发。
  支持国内平台（淘宝、京东、拼多多、抖音）与国际跨境平台（Amazon、独立站）的尺寸规范。
  触发示例：「帮我生成这件T恤的电商套图」「做一套淘宝主图」「生成亚马逊listing图片」。
  不应在用户仅上传图片但未明确提出图片生成需求时触发。
metadata: {"openclaw":{"emoji":"🛍️","requires":{"env":["DASHSCOPE_API_KEY"]},"primaryEnv":"DASHSCOPE_API_KEY","optionalEnv":["OPENAI_API_KEY","OPENAI_BASE_URL","OPENAI_MODEL","GEMINI_API_KEY","GEMINI_BASE_URL","GEMINI_MODEL","STABILITY_API_KEY","STABILITY_BASE_URL","STABILITY_MODEL","DASHSCOPE_BASE_URL","DASHSCOPE_MODEL","ARK_API_KEY","ARK_BASE_URL","ARK_IMAGE_MODEL","ARK_VIDEO_MODEL"]}}
---

# 电商套图生成助手

## 概览

本 Skill 实现从「商品原始图片 + 卖点信息」到「完整电商套图」的一键生成流程：

```
① 上传商品图片（必须）+ 输入卖点信息（可选）
        ↓
② AI 视觉分析：提取商品主体，智能生成卖点文案（可编辑）
        ↓
③ 选择平台规范 + 套图类型（7种标准图）
        ↓
④ AI 生成每张图的详细 Prompt（可编辑）
        ↓
⑤ 调用图像生成 API，输出完整套图（文案由生图模型直接渲染）
        ↓
⑥ 平台文案（可选）→ ⑦ 详情页 HTML（可选）
        ↓
⑧ 产品展示视频生成（可选，基于套图，需用户确认）
```

---

## ⛔ 前置检查：API Key 验证（必须最先执行）

**在执行任何其他操作之前**，Agent 必须先完成以下验证。若验证失败，**立即停止，不得调用任何工具或执行任何后续步骤**。

### 验证步骤

运行供应商检测脚本：

```bash
python3 scripts/check_providers.py
```

解析输出中的 `configured` 数组：

- **如果 `configured` 为空数组 `[]`**：
  > ❌ **配置缺失，任务终止。**
  >
  > 向用户输出以下消息，然后**立即停止，不再调用任何工具**：
  >
  > ---
  > **未检测到任何图像生成 API Key，无法继续操作。**
  >
  > 请至少配置以下供应商之一（国内用户推荐前两个）：
  >
  > | 供应商 | 环境变量 | 说明 |
  > |--------|---------|------|
  > | 阿里云通义 | `DASHSCOPE_API_KEY` | 国内直连，推荐 |
  > | 字节跳动豆包 | `ARK_API_KEY` | 国内直连 |
  > | OpenAI | `OPENAI_API_KEY` | 需代理 |
  > | Google Gemini | `GEMINI_API_KEY` | 需代理 |
  > | Stability AI | `STABILITY_API_KEY` | 需代理 |
  >
  > 配置方法：
  > ```bash
  > export DASHSCOPE_API_KEY="sk-..."   # 推荐，国内直连
  > # 或
  > export ARK_API_KEY="..."
  > ```
  > 加入 `~/.zshrc` 后执行 `source ~/.zshrc` 使其永久生效，然后重新启动对话。
  > ---
  >
  > **⚠️ Agent 规则：输出上述消息后，立即终止本次任务。不得继续分析图片、生成 Prompt 或调用任何其他工具。**

- **如果 `configured` 非空**：记录可用供应商列表，继续执行第一步。

### check_providers.py 脚本报错处理

若脚本本身执行失败（非零退出码或输出异常），**将完整错误信息输出到对话**，格式如下，然后停止：

> ❌ **供应商检测脚本执行失败，任务终止。**
>
> 错误详情：
> ```
> [此处粘贴脚本的完整 stdout + stderr 输出]
> ```
> 请检查 Python 环境（需 Python 3.8+）及脚本路径是否正确。

---

## 触发入口：判断是否已上传图片

> ⚠️ **Agent 必须在第一步开始前执行此判断，决定对话起点。**

### 情况 A：用户触发时【未上传图片】

用户说了类似「帮我做电商套图」「我要给某商家出套图」但**没有附带任何图片**时，Agent **禁止直接进入第一步**，必须先走以下引导流程：

**1. 发送欢迎 + 图片输入引导（一条消息完成）：**

> 好的，我来帮您生成完整的电商套图！
>
> 在上传图片前，先了解一下最佳输入方案，**图片质量直接决定生成效果**：
>
> ---
>
> **请选择您的图片输入方式：**
>
> | 编号 | 方式 | 效果 | 适用情况 |
> |------|------|------|---------|
> | **① 正面 + 背面（平铺）** | ⭐⭐⭐⭐⭐ 最佳 | AI 全面理解正背面结构，材质图自动用背面细节 | 服装/鞋类**强烈推荐** |
> | **② 单张正面（平铺）** | ⭐⭐⭐⭐ 优秀 | 标准正面展示，效果稳定 | 仅有一张时首选 |
> | **③ 正面 + 背面（挂拍）** | ⭐⭐⭐⭐ 优秀 | 悬挂构图，适合有衣架的商家 | 有挂拍图时推荐 |
> | **④ 单张挂拍** | ⭐⭐⭐ 良好 | 悬挂构图，效果较平铺略差 | 仅有挂拍图时 |
> | **⑤ 模特实拍** | ⭐⭐⭐ 良好 | AI 提取商品特征，去除模特 | 有模特图时可用 |
>
> 💡 **小贴士**：多张图必须是**同一商品**，不同颜色/款式请分批处理；平铺图请确保平整无褶皱。
>
> 请选择编号（或直接上传图片，我会自动识别类型），然后上传图片即可开始。

**2. 等待用户回复：**

- 用户选择编号后，记录 `input_image_type`（见映射表），再提示上传对应数量的图片
- 用户直接上传图片（未选编号），自动检测 `input_image_type`，进入情况 B

**编号 → `input_image_type` 映射：**

| 编号 | `input_image_type` |
|------|-------------------|
| ① | `flat_lay_front_back` |
| ② | `flat_lay` |
| ③ | `hanging_front_back` |
| ④ | `hanging` |
| ⑤ | `model` |

---

### 情况 B：用户触发时【已上传图片】

用户在同一条消息中**附带了图片**时，Agent **直接进入第一步**，无需重复引导。
自动检测 `input_image_type`（见第二步 Step A），跳过欢迎引导。

---

## 第一步：收集输入信息

### 必须项
- **商品图片**：用户上传的原始商品图，**支持 1-3 张同一商品的不同角度/拍摄方式**
  - 平铺图（flat lay）、挂拍图（hanging）、模特实拍图（model）均可
  - 多图时，Agent 综合所有图片分析，提取更完整的商品信息
  - 多图仅用于分析参考，生成套图时以 `--product` JSON 驱动，不直接传入多图

### 可选项（若用户未提供，AI 将自动从图片中分析生成）
| 字段 | 说明 |
|------|------|
| 商品名称 | 如"黑色碎花交叉细吊带荷叶边下摆连衣裙" |
| 核心卖点 | 材质、版型、设计特点等 3-5 条 |
| 适用人群 | 如"追求甜美法式风格的年轻女性" |
| 期望场景 | 如"海边度假、浪漫约会、周末聚会" |
| 规格参数 | 材质、颜色、版型、领型、袖长等 |

---

## 第二步：AI 分析与卖点生成

> **🤖 商品识别三级优先策略（Agent 必须按顺序判断，不得跳级）：**
>
> | 优先级 | 条件 | 执行方式 |
> |--------|------|----------|
> | **① 最高** | Agent 自身具备视觉理解能力（如 Claude Vision、GPT-4o 等多模态模型） | **直接使用 Agent 内置能力**分析图片，输出卖点 JSON。**禁止调用任何外部脚本。** |
> | **② 次之** | Agent 不具备原生视觉能力，但**拥有图像识别相关工具**（如 `analyze_image`、`img_recognize`、`vision_tool` 等） | **调用 Agent 内置工具**分析图片，输出卖点 JSON。 |
> | **③ 兜底** | Agent 既无原生视觉能力、也无视觉工具 | **调用 `scripts/analyze.py` 脚本**（见下方说明）。**禁止让用户手动描述商品，禁止凭空生成商品描述。** |
>
> ⚠️ **严禁行为**：在未尝试上述三级方案的情况下，直接询问用户「请描述一下您的商品」。

### ⚠️ 图片预处理（最先执行，所有步骤的前提）

> 用户上传的图片保存在 session 临时目录，脚本运行时可能因路径失效或权限问题无法访问。**必须在调用任何脚本前将图片复制到 `{output_dir}/` 下。**

```bash
# 将所有用户上传的商品图片复制到工作区（路径以实际上传路径为准）
cp "/absolute/path/to/用户上传图1.jpg" "{output_dir}/front.jpg"
cp "/absolute/path/to/用户上传图2.jpg" "{output_dir}/back.jpg"   # 若有背面图
```

复制完成后，后续所有脚本一律使用 `{output_dir}/front.jpg`、`{output_dir}/back.jpg` 等**工作区绝对路径**，不得直接使用用户上传的原始路径。

**Agent 操作规则：**
1. 用 Bash `cp` 命令将每张上传图复制到 `{output_dir}/`
2. 若 `output_dir` 尚未创建，先 `mkdir -p {output_dir}`
3. 复制成功后记录工作区路径，后续 `--product-images`、`--model-image`、`analyze.py` 参数全部使用工作区路径

---

### 视觉分析步骤

**Step A：判断 `input_image_type`（必须，影响生图构图）**

| 用户提供的图片 | `input_image_type` | 说明 |
|--------------|-------------------|------|
| 1 张平铺图（正面） | `flat_lay` | 默认，标准正面平铺 |
| 2 张平铺图（正面 + 背面） | `flat_lay_front_back` | 最佳组合；背面图自动用于材质图 |
| 1 张挂拍图 | `hanging` | 构图自动改为挂拍悬挂风格 |
| 2 张挂拍图（正面 + 背面） | `hanging_front_back` | 背面挂拍用于材质图 |
| 1 张模特实拍 | `model` | AI 提取商品特征，构图提示去除模特 |

**Step B：确定参考图列表（决定 `--product-images` 参数）**

> 使用图片预处理步骤中复制到 `{output_dir}/` 的绝对路径，不得使用用户上传的原始路径。

- 1 张图 → `--product-images {output_dir}/front.jpg`
- 正反 2 张 → `--product-images {output_dir}/front.jpg,{output_dir}/back.jpg`（顺序必须：正面在前）
- 3 张 → `--product-images {output_dir}/front.jpg,{output_dir}/back.jpg,{output_dir}/detail.jpg`

**生图脚本自动按图类型选图**：

| 套图类型 | 使用哪张图 |
|---------|-----------|
| 白底主图、核心卖点图、卖点图、场景图、模特图、多场景图 | 第 1 张（正面） |
| 材质图 | 第 2 张（背面/细节）；无则用第 1 张 |

**Step C：分析商品信息**

1. 识别商品类型、颜色、款式、设计元素，多图时综合所有图片信息
2. 提取精确视觉特征：主色、辅助色、印花图案、领型、廓形、下摆、面料质感、季节属性
3. 基于视觉特征推断材质、功能卖点，生成每个卖点的视觉关键词（用于放大镜气泡）
4. 生成结构化卖点 JSON（格式见下），供第四步生成 generate.py 参数使用

### 卖点 JSON 结构（丰富版）

```json
{
  "product_name": "黑色碎花交叉细吊带荷叶边下摆连衣裙",
  "product_category": "连衣裙",
  "product_subtype": "吊带裙",
  "product_type": "服装",

  "visual_features": {
    "main_color": "黑色",
    "secondary_colors": ["淡粉色樱花", "白色"],
    "pattern": "碎花印花",
    "neckline": "V领交叉细吊带",
    "silhouette": "鱼尾A字",
    "hemline": "荷叶边双层",
    "length": "短裙/中裙",
    "fabric_texture": "轻盈飘逸",
    "season": "春夏"
  },

  "selling_points": [
    {
      "type": "design",
      "title": "个性交叉领口",
      "description": "V领结合多重细绑带设计，凸显优雅锁骨曲线",
      "visual_keywords": ["交叉绑带", "V领", "锁骨", "层次感"],
      "icon": "design",
      "en": "Cross-strap V-neckline",
      "zh": "个性交叉领口"
    },
    {
      "type": "pattern",
      "title": "唯美碎花印花",
      "description": "黑色底面点缀淡雅樱花图案，营造复古浪漫氛围",
      "visual_keywords": ["碎花", "樱花", "复古", "浪漫"],
      "icon": "design",
      "en": "Floral Print",
      "zh": "唯美碎花印花"
    },
    {
      "type": "silhouette",
      "title": "灵动鱼尾设计",
      "description": "下摆采用层次感荷叶边，行走间灵动飘逸",
      "visual_keywords": ["鱼尾", "荷叶边", "飘逸", "层次"],
      "icon": "fit",
      "en": "Ruffle Hemline",
      "zh": "灵动鱼尾设计"
    }
  ],

  "target_audience": "追求个性时尚、喜爱甜美法式风格的年轻女性",
  "usage_scenes": ["海边度假", "浪漫约会", "周末聚会", "盛夏日常"],

  "input_image_type": "flat_lay",
  "number_of_input_images": 1,

  "color": "黑色",
  "material": "轻薄印花面料"
}
```

> 📄 详细分析 Prompt 见 `references/analysis-prompts.md`

### 分析结果确认

分析完成后，Agent 向用户展示识别出的卖点，让用户确认或补充：

> 我分析出这是一件 **[商品名]**，主要特点是：
>
> • [卖点1 title]：[description]
> • [卖点2 title]：[description]
> • [卖点3 title]：[description]
>
> 请确认这些卖点是否准确，或补充其他卖点（直接告知即可，我会更新后继续）。

用户确认后继续；若用户有修改，更新 `selling_points` 后继续。

### 兜底方案：调用 analyze.py 脚本

当进入**第③级**时，执行以下脚本，自动按 **Qwen VL → 豆包视觉 → GPT-4o** 顺序降级：

```bash
# 自动选择已配置的视觉供应商（Qwen → 豆包 → OpenAI）
python3 scripts/analyze.py ./product.jpg

# 指定供应商
python3 scripts/analyze.py ./product.jpg --provider tongyi

# 保存到文件供后续步骤使用
python3 scripts/analyze.py ./product.jpg --output ./output/product.json
```

**analyze.py 供应商优先级**（视觉识别，与图像生成供应商独立）：

| 优先级 | 供应商 | 环境变量 | 视觉模型 |
|--------|--------|---------|----------|
| 1 | 阿里云通义 VL | `DASHSCOPE_API_KEY` / `ALIYUN_API_KEY` | `qwen-vl-max` |
| 2 | 字节豆包视觉 | `ARK_API_KEY` | `doubao-vision-pro-32k` |
| 3 | OpenAI | `OPENAI_API_KEY` | `gpt-4o` |

若三者均未配置，脚本退出码 2，并输出配置指引。**此时 Agent 必须将完整错误输出到对话并停止。不得继续。**

---

## 第三步：选择平台与套图配置

> ⚠️ **Agent 必须在此步骤主动询问用户目标平台，不得跳过。** 若用户在第一步已明确说明平台（如"做一套淘宝主图"），可直接采用；否则必须先询问再继续。未确认平台前，**禁止进入第四步及后续任何生图操作**。

向用户提问：

> 请选择目标电商平台（决定图片尺寸和文案语言）：
>
> **国内平台**：淘宝/天猫 · 京东 · 拼多多 · 抖音/小红书
> **国际平台**：Amazon · 独立站/Shopify
>
> 可多选（如同时投放多个平台），我会按各平台规范分别生成。

> 📄 各平台规范详见 `references/platforms.md`

### 平台选择
| 平台类型 | 平台 | 推荐尺寸 | 语言 |
|---------|------|---------|------|
| 国内 | 淘宝/天猫 | 800×800 (1:1) | 中文 |
| 国内 | 京东 | 800×800 (1:1) | 中文 |
| 国内 | 拼多多 | 750×750 (1:1) | 中文 |
| 国内 | 抖音/小红书 | 1080×1350 (4:5) 或 1:1 | 中文 |
| 国际 | Amazon | 2000×2000 (1:1) | 英文 |
| 国际 | 独立站/Shopify | 2000×2000 (1:1) 或 16:9 | 英文 |

### 标准套图（7种）
每种图的详细规格见 `references/image-types.md`

| # | 图片类型 | 核心目标 | 推荐位置 |
|---|---------|---------|---------|
| 1 | **白底主图** | 商品全貌展示，符合平台收录规则 | 第1张主图 |
| 2 | **核心卖点图** | 3大卖点图标化呈现 | 第2张 |
| 3 | **卖点图** | 单一核心卖点深度展示 | 第3张 |
| 4 | **材质图** | 面料/工艺特写，建立品质信任 | 第4张 |
| 5 | **场景展示图** | 生活方式场景，激发代入感 | 第5张 |
| 6 | **模特展示图** | 真人/AI模特穿搭，直观展示效果 | 第6张 | ⚠️ 仅服装/鞋类 |
| 7 | **多场景拼图** | 多场景适用性对比，提升决策 | 第7张 |

---

## 第四步：准备生图参数（动态填充商品信息）

> 📄 各图类型的视觉规格参考见 `references/image-types.md`
>
> ⚠️ **架构说明**：图片 Prompt 由 `scripts/generate.py` 内置引擎自动生成，Agent 的任务是**准备好正确的商品 JSON 参数**传给脚本，而非手写 Prompt 文本。图片名称和类型均由脚本固定输出（中文文件名），Agent **禁止**自行调用图像 API 或另存文件。

### Agent 必须完成的工作

**将第二步的卖点 JSON 补充为完整的 generate.py 输入 JSON**，关键字段：

| 字段 | 来源 | 说明 |
|------|------|------|
| `product_description_for_prompt` | **Agent 必须生成** | 精炼的英文/中文商品描述，供 generate.py 拼接所有 Prompt 使用（见格式要求） |
| `selling_points` | 第二步 JSON | 确保每项含 `zh`/`en` 字段，新格式额外含 `title`/`description`/`visual_keywords` |
| `garment_position` | Agent 判断 | 服装上衣 → `top`；下装 → `bottom`；连体/全身 → `full-body`；非服装 → `non-apparel` |
| `product_name` | 第二步 JSON | 完整商品名 |
| `visual_features` | 第二步 JSON | 结构化视觉特征对象 |

### `product_description_for_prompt` 格式要求

**必须**包含商品名 + 核心视觉特征（颜色、印花、款式细节），供 generate.py 在所有 Prompt 中引用。

```
格式：[product_name], [main_color] [pattern] [neckline] [silhouette] [hemline]

示例：
黑色碎花交叉细吊带荷叶边下摆连衣裙, black floral print V-neck cross-strap spaghetti dress with ruffle hemline
白色卡通小狗印花宽松精梳棉短袖T恤, white loose combed cotton short-sleeve T-shirt with cute dog print
```

### 完整 generate.py 输入 JSON 示例

```json
{
  "product_description_for_prompt": "黑色碎花交叉细吊带荷叶边下摆连衣裙, black floral print V-neck cross-strap dress with ruffle hemline",
  "product_name": "黑色碎花交叉细吊带荷叶边下摆连衣裙",
  "product_category": "连衣裙",
  "product_type": "服装",
  "garment_position": "full-body",
  "visual_features": {
    "main_color": "黑色",
    "secondary_colors": ["淡粉色樱花", "白色"],
    "pattern": "碎花印花",
    "neckline": "V领交叉细吊带",
    "silhouette": "鱼尾A字",
    "hemline": "荷叶边双层",
    "fabric_texture": "轻盈飘逸"
  },
  "selling_points": [
    {
      "type": "design", "title": "个性交叉领口",
      "description": "V领结合多重细绑带设计，凸显优雅锁骨曲线",
      "visual_keywords": ["交叉绑带", "V领", "锁骨", "层次感"],
      "zh": "个性交叉领口", "en": "Cross-strap V-neckline"
    },
    {
      "type": "pattern", "title": "唯美碎花印花",
      "description": "黑色底面点缀淡雅樱花图案，营造复古浪漫氛围",
      "visual_keywords": ["碎花", "樱花", "复古", "浪漫"],
      "zh": "唯美碎花印花", "en": "Floral Print"
    },
    {
      "type": "silhouette", "title": "灵动鱼尾设计",
      "description": "下摆采用层次感荷叶边，行走间灵动飘逸",
      "visual_keywords": ["鱼尾", "荷叶边", "飘逸", "层次"],
      "zh": "灵动鱼尾设计", "en": "Ruffle Hemline"
    }
  ],
  "input_image_type": "flat_lay"
}
```

### 核心卖点图（key_features）自动模板选择

generate.py 根据 `garment_position` 字段**自动选择模板**，无需 Agent 干预：

| 商品类型 | 自动选用模板 | 视觉效果 |
|---------|-------------|---------|
| 服装/鞋类（`garment_position` ≠ `non-apparel`） | **放大镜特写模板** | 居中主图 + 3个圆形放大镜气泡，连细线到商品局部，展示 3 个卖点细节特写 |
| 非服装类（`garment_position = non-apparel`） | **信息图标模板** | 左侧商品图 + 右侧 3 条图标+文字卖点 |

放大镜气泡内容自动取自 `selling_points[0..2].visual_keywords`（首两个关键词）。

---

## 第四步半：模特图判断与模特选择（条件步骤）

> 本步骤仅在套图类型包含 `model` 或 `lifestyle` 时执行。

### 4.1 是否需要模特图？

Agent 根据第二步分析结果中的 `product_type` 判断：

| 品类 | 是否需要模特 |
|------|-------------|
| 服装（T恤、裙子、外套等） | ✅ 需要 |
| 鞋类 | ✅ 需要 |
| 3C 数码、家电、家具、食品等 | ❌ 不需要 → 自动跳过 `model` 类型 |

**若商品不需要模特**，Agent 自动从 `--types` 中移除 `model`，并告知用户：
> 检测到您的商品为 [品类]，不适合模特展示图，已自动跳过该类型。

### 4.2 选择模特来源与展示风格

> ⚠️ **Agent 必须主动向用户提出此问题，不得跳过或自行决定。**

若需要模特，**一次性**向用户提问：

> 模特展示图需要确认以下两个设置：
>
> **① 模特来源**
> 1. **使用内置模特库** — 从预置的 AI 模特中选择，Agent 展示图片后确认（推荐，形象稳定一致）
> 2. **AI 自动生成** — 由 AI 生成随机模特，生成后展示给您确认，确认后锁定用于场景图和多场景图
>
> **② 展示风格**
> 1. **标准商拍** — 户外/棚拍常规展示（默认，适用于大多数服装）
> 2. **贴身合体** — 强调贴合身体效果（适用于紧身衣物、内衣、泳装、健身服等）

**展示风格处理**：用户选择「贴身合体」则调用 generate.py 时加上 `--model-style bodycon`；默认选「标准商拍」无需额外参数。

### 4.3 内置模特选择（用户选择方案 1）

> 🔒 **人物锁定**：选定内置模特后，`--model-image` 参数会作为参考图传入生图脚本。generate.py 会在 Prompt 中嵌入强制指令，要求生图模型严格复刻参考图中的人物外貌，**不得替换为其他人物或外国面孔。**

**Agent 必须展示模特图片，禁止只用文字描述。**

流程：

1. 读取 `assets/models.json` 加载模特列表，按商品风格/性别自动推荐 3 位
2. **逐一展示模特图片**：读取 `assets/models/{id}.png` 并**直接在对话中展示图片**
3. 同时附上文字信息辅助判断：

```
根据您的商品 [商品名]，推荐以下模特，请查看图片后选择：

[展示 assets/models/01.png 图片]
① 柔妍（优雅风·女·165cm）— 适合正装、中淑风

[展示 assets/models/02.png 图片]
② 雅琪（甜妹系·女·167cm）— 适合甜妹、JK、日系

[展示 assets/models/03.png 图片]
③ 宇菲（街头风·女·168cm）— 适合休闲、运动、街拍

请选择编号，或输入偏好（肤色/风格/体型），我为您筛选更多。
```

4. 用户选定后，记录 `model_image_path = assets/models/{id}.png`，进入 4.5

**肤色/风格筛选**：根据用户偏好（如"偏白"、"欧美风"、"男模"）过滤 models.json 的 `style` 字段后**重新展示图片**。

### 4.4 AI 自动生成（用户选择方案 2）

不使用内置模特，由 AI 随机生成。**与方案 1 的关键区别是需要一次额外的确认步骤**（见 4.5）。

**默认模特风格**（Agent 根据商品属性自动选择，并明确告知用户）：

| 商品属性 | 默认 Prompt 模板 | 说明 |
|---------|----------------|---------|
| 女装 / 中性款 | `asian_studio` | 国内亚洲女模，淡妆，棚拍风格 |
| 男装 | `male_studio` | 国内亚洲男模，休闲棚拍风格 |

> Agent 告知示例：「将使用国内女模 AI 随机生成，生成后展示给您确认，确认满意后再用于场景图和多场景图。」

### 4.5 模特图生成与确认（两阶段生成的核心步骤）

> ⚠️ **模特展示图、场景展示图、多场景拼图 必须使用同一个模特参考图。** 这三类图必须在确认模特后分两阶段生成，**不得一次性批量生成全部 7 种图**。

**方案 1（内置模特）：直接进入阶段二**

- `model_image_path` = `assets/models/{id}.png`（用户选定的内置模特路径）
- 已有参考图，无需额外生成，直接跳到「阶段二生成」

**方案 2（AI 自动生成）：先生成→确认→锁定**

**阶段一：单独生成模特展示图**

```bash
python3 scripts/generate.py \
  --product '{...}' \
  --provider [provider] \
  --lang zh \
  --product-images ./front.jpg \
  --types model \
  --template-set [N] \
  --output-dir ./output/
```

生成完成后，**Agent 从 `generate_result.json` 读取模特图的绝对路径**，然后展示图片并提问：

```python
# 读取 generate_result.json 获取绝对路径（避免相对路径歧义）
import json
result = json.loads(open("{output_dir}/generate_result.json").read())
model_image_path = result["model"]["path"]  # 已是绝对路径
```

> 这是为您生成的模特展示图：
> [展示 {model_image_path} 图片]
>
> 请问这个模特满意吗？
> 1. **满意** — 保存并用于场景展示图、多场景拼图
> 2. **重新生成** — 再生成一次（最多重试 3 次）
> 3. **换内置模特** — 切换到内置模特库选择

- 用户选 **满意** → `model_image_path` = `generate_result.json` 中的 `model.path`（绝对路径），进入阶段二
- 用户选 **重新生成** → 重新执行阶段一（超过 3 次建议切换内置模特）
- 用户选 **换内置模特** → 回到 4.3 内置模特选择

**阶段二：用确认的模特图生成剩余 6 种图**

```bash
python3 scripts/generate.py \
  --product '{...}' \
  --provider [provider] \
  --lang zh \
  --product-images ./front.jpg,./back.jpg \
  --model-image [model_image_path] \
  --types white_bg,key_features,selling_pt,material,lifestyle,multi_scene \
  --template-set [N] \
  --output-dir ./output/
```

> 💡 `--model-image [model_image_path]` 确保 lifestyle 和 multi_scene 使用同一张已确认的模特图，三图模特形象完全一致。

### 4.6 同批次模特自动锁定机制

> **generate.py 内置行为，Agent 无需额外操作。**

当一次调用中 `--types` 同时包含 `model` 和 `lifestyle`/`multi_scene` 时，脚本自动将本次生成的模特图用于后续类型：

```
model 生成完成 → 自动用作 lifestyle 的 --model-image → 自动用作 multi_scene 的 --model-image
控制台提示：🔒 锁定本次生成的模特图: /absolute/path/模特展示图.jpg
```

### 4.7 重新生成单张图时的模特锁定

当用户对某张图不满意，要求**单独重新生成** `lifestyle` 或 `multi_scene` 时：

- **generate.py 会自动检测** `{output_dir}/模特展示图.jpg` 是否存在
- 若存在，自动作为模特参考图（无需手动传 `--model-image`）
- 控制台提示：`🔒 自动使用已有模特图: /absolute/path/模特展示图.jpg`

**Agent 操作规则**：
1. 单独重新生成时，无论是 `lifestyle` 还是 `multi_scene`，**不得省略 `--output-dir`**（必须与首次生成保持一致，否则找不到已有模特图）
2. 若用户此时也想换模特，才需要显式传 `--model-image [new_model_path]`
3. 若 `FileNotFoundError` 错误信息含"参考图文件不存在"，**从错误中读取解析路径**（括号内绝对路径）告知用户实际查找位置：
   ```
   ❌ 参考图文件不存在: ./product.jpg（解析路径: /Users/.../product.jpg）
   → 告知用户：脚本在 /Users/.../product.jpg 找不到文件，请确认路径是否正确
   ```

---

## 第四步半 B：套图模板选择

> ⚠️ **此步骤必须在第五步生图之前完成。** 用户选择模板后，generate.py 才会用对应风格的 Prompt 模板动态组合商品参数。

### 5 套视觉风格模板

向用户展示以下选项（**默认使用第 1 套**，可全局选或按图类型分别选）：

| 套数 | `--template-set` | 名称 | 风格描述 | 适用场景 |
|------|------|------|---------|---------|
| **①** | `1` | **默认商拍** | 标准电商商拍，干净明亮，重点突出商品 | 通用，各平台均适合 |
| **②** | `2` | **生活杂志** | 自然光，有氛围感和生活质感 | 淘宝/天猫/小红书，女装/家居 |
| **③** | `3` | **极简高冷** | 极简留白，高反差，奢侈品质感 | 独立站/Amazon，高端品牌 |
| **④** | `4` | **活力爆款** | 高饱和度，大字冲击，活力感强 | 拼多多/抖音，年轻客群 |
| **⑤** | `5` | **暗调质感** | 深色系，电影质感，戏剧性打光 | 男装/数码/运动/夜场 |

**各套模板对 6 种图类型的效果说明：**

| 图类型 | ① 默认商拍 | ② 生活杂志 | ③ 极简高冷 | ④ 活力爆款 | ⑤ 暗调质感 |
|--------|-----------|-----------|-----------|-----------|-----------|
| 核心卖点图 | 放大镜气泡/信息图标 | 商品居中+手写标注线 | 黑底白字+单色线框 | 爆炸形背景+粗体红字 | 深灰底+金色描边气泡 |
| 卖点图 | 卧室暖光 | 咖啡馆窗前自然光 | 纯白棚拍极简 | 户外街头高饱和 | 暗调棚拍聚光灯 |
| 材质图 | 极macro面料 | 木纹/大理石桌面铺陈 | 折叠几何极简 | 对折叠叠高饱和 | 暗色背景金边光圈 |
| 场景展示图 | 校园/咖啡厅 | 户外公园黄金时刻 | 白色简洁室内 | 街头活力 | 城市夜景/聚光棚拍 |
| 模特展示图 | 户外阳光走路 | 坐姿休闲咖啡厅 | 白底棚拍全身 | 街拍动态跳跃 | 暗调棚拍聚焦 |
| 多场景拼图 | 左右分屏 | 三格日记卡片 | 上下黑白分割 | 对角爆炸分割 | 暗调三屏电影感 |

**Agent 询问话术：**

> 接下来请选择整体视觉风格模板（影响所有图片的氛围和排版）：
>
> **① 默认商拍** — 标准电商风，干净通用（推荐新手）
> **② 生活杂志** — 自然光氛围感，女装/家居首选
> **③ 极简高冷** — 留白奢品感，高端品牌
> **④ 活力爆款** — 高饱和冲击，拼多多/抖音
> **⑤ 暗调质感** — 电影感打光，男装/数码/运动
>
> 直接输入编号即可。如需对某几种图单独指定不同模板，请告知（如"材质图用③，其余用①"）。

**记录选择，传入参数：**

- 全局统一：`--template-set N`
- 按类型分开：`--per-type-templates key_features:2,material:3,selling_pt:4`（其余用全局）

---

## 第五步：多供应商图像生成

> 📄 各供应商 API 接入详情见 `references/providers.md`
### 5.0 选择图像生成供应商与模型

> ⚠️ **Agent 必须在执行生图前向用户确认供应商，不得自行决定。**

首先展示前置检查中检测到的可用供应商列表，然后向用户提问：

> 检测到以下图像生成供应商可用：
>
> | 编号 | 供应商 | 默认模型 | 国内直连 |
> |------|--------|---------|---------|
> | 1 | 阿里云通义 | `wan2.7-image-pro` | ✅ |
> | 2 | 字节跳动豆包 | `doubao-seedream-5-0-260128` | ✅ |
> | 3 | OpenAI | `dall-e-3` | 需代理 |
> | 4 | Google Gemini | `gemini-3.1-flash-image-preview` | 需代理 |
> | 5 | Stability AI | `core` | 需代理 |
>
> _(仅展示已配置 API Key 的供应商)_
>
> 请选择使用哪个供应商？（如需使用非默认模型，也可一并告知）

**若用户未明确指定**，优先推荐国内直连供应商（通义 > 豆包），并告知用户。

### 5.1 生成模式选择

> ⚠️ **Agent 必须在执行生图前选择模式，不得跳过。**

当前共有 **[N] 种套图**，每种类型生成 **1 张**，请选择生成方式：

> 1. **一次性批量生成** — 自动依次生成所有套图（推荐，省时）
> 2. **逐张确认** — 每张图生成后暂停，查看效果后再继续

**一次性模式**：直接调用 generate.py 传入全部 `--types`，生成完后一并展示结果。

**逐张模式**：每次只传入一个 `--types`，生成后向用户展示该图路径，获得确认后再生成下一张。若用户对某张不满意，可修改 Prompt 后重新生成该张。

### 执行生图脚本

```bash
python3 scripts/generate.py \
  --product '{"product_description_for_prompt": "...", "selling_points": [...]}' \
  --provider tongyi \
  --lang zh \
  --product-image ./product.jpg \
  --types white_bg,key_features,selling_pt,material,lifestyle,model,multi_scene \
  --output-dir ./output/
```

### generate.py 完整参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--product` | **必填**，商品 JSON 字符串 | — |
| `--provider` | **必填**，供应商：`openai` / `gemini` / `stability` / `tongyi` / `doubao` | — |
| `--api-key` | API Key，也可通过环境变量传入 | 环境变量 |
| `--base-url` | 自定义代理地址，也可通过 `*_BASE_URL` 环境变量传入 | 官方地址 |
| `--model` | 模型名称，也可通过 `*_MODEL` 环境变量传入 | 见供应商表 |
| `--types` | 逗号分隔的套图类型 | 全部 7 种 |
| `--lang` | 图片内嵌文案语言：`zh`（中文）/ `en`（英文，国际平台） | `zh` |
| `--model-style` | 模特展示风格：`standard`（标准商拍）/ `bodycon`（贴身合体，适用于紧身衣物） | `standard` |
| `--template-set` | 全局视觉风格模板：`1`=默认商拍 `2`=生活杂志 `3`=极简高冷 `4`=活力爆款 `5`=暗调质感 | `1` |
| `--per-type-templates` | 按图类型单独指定模板（覆盖 `--template-set`），格式：`key_features:2,material:3` | 无 |
| `--product-images` | **推荐**，逗号分隔的商品参考图列表（按顺序：正面图,背面图,...）；白底/卖点图用正面，材质图自动用背面 | 无 |
| `--product-image` | 单张商品参考图（向后兼容，等价于 `--product-images` 只传一张） | 无 |
| `--model-image` | 模特参考图路径或 URL（`model`/`lifestyle`/`multi_scene` 类型优先使用，锁定模特外貌） | 无（纯文生图） |
| `--output-dir` | 输出目录 | `./output/` |
| `--request-timeout` | 单次 HTTP 请求超时时间（秒） | `180` |
| `--poll-max-wait` | 通义万象异步任务最大轮询等待（秒） | `600` |

### 代理 API 使用示例

各供应商均支持通过 `--base-url` 或环境变量指定代理地址：

```bash
# Gemini 通过代理（代理使用 Bearer token 鉴权）
GEMINI_API_KEY="sk-proxy-key" \
GEMINI_BASE_URL="https://my-proxy.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent" \
  python3 scripts/generate.py --provider gemini --product '...'

# 通义通过代理
DASHSCOPE_API_KEY="sk-..." \
DASHSCOPE_BASE_URL="https://my-proxy.com/api/v1/services/aigc/multimodal-generation/generation" \
  python3 scripts/generate.py --provider tongyi --product '...'

# 切换模型版本（使用千问同步接口代替万象异步）
DASHSCOPE_MODEL="qwen-image-2.0-pro" \
  python3 scripts/generate.py --provider tongyi --product '...'
```

## CLI 执行流程（Agent 调用）

Agent 或 CLI 环境下的完整流程：

```bash
# Step 0: 【必须】前置 API Key 检测（见"前置检查"章节）
python3 scripts/check_providers.py
# → configured 为空则立即停止，不执行后续任何步骤

# Step 1: 商品图片分析（三级优先，见"第二步"）
#   ① Agent 原生视觉能力 → 直接分析，无需脚本（支持 1-3 张图）
#   ② Agent 内置视觉工具 → 调用工具分析
#   ③ 兜底：调用 analyze.py（Qwen → 豆包 → OpenAI 自动降级）
python3 scripts/analyze.py ./product.jpg --output ./output/product.json
# 多图输入：传入多个路径
python3 scripts/analyze.py ./product_1.jpg ./product_2.jpg --output ./output/product.json
# 将输出 JSON 内容作为 --product 参数传入后续脚本

# Step 2: Agent 准备完整商品 JSON（含 product_description_for_prompt），调用生图脚本
# --product-images 按顺序传入：正面图,背面图（有背面图时材质图自动用背面）
# product_description_for_prompt 必须包含：商品名 + 核心视觉特征描述
# input_image_type 决定白底主图的构图风格（flat_lay / flat_lay_front_back / hanging 等）
python3 scripts/generate.py \
  --product '{"product_description_for_prompt":"黑色碎花吊带连衣裙, black floral V-neck dress with ruffle hem","garment_position":"full-body","input_image_type":"flat_lay_front_back","selling_points":[{"zh":"个性交叉领口","en":"Cross-strap neckline","visual_keywords":["交叉绑带","V领"]},{"zh":"唯美碎花印花","en":"Floral Print","visual_keywords":["碎花","樱花"]},{"zh":"灵动鱼尾设计","en":"Ruffle Hemline","visual_keywords":["鱼尾","荷叶边"]}]}' \
  --provider tongyi \
  --lang zh \
  --product-images ./front.jpg,./back.jpg \
  --model-image ./assets/models/02.png \
  --output-dir ./output/

# Step 3: 平台文案生成（可选）— Agent 直接按 references/copy-prompts.md 模板生成
# Step 4: 详情页 HTML 生成（可选）— Agent 直接按 references/copy-prompts.md 模板生成

# Step 5: 产品展示视频生成（可选，需用户确认）
python3 scripts/generate_video.py \
  --images ./output/白底主图.jpg ./output/场景展示图.jpg \
  --prompt "高清电商产品视频，依次呈现商品全貌、材质细节、室内穿着效果，过渡自然流畅" \
  --audio \
  --output-dir ./output/video/
```

### 脚本错误处理规则（强制）

每次调用 `generate.py` 后，Agent **必须**检查退出码和输出：

| 情况 | Agent 行为 |
|------|-----------|
| 退出码为 0，无 `ERROR` / `Exception` 关键字 | 继续下一步 |
| 退出码非 0，或输出含 `ERROR` / `Traceback` / `Exception` | **停止后续所有步骤**，将完整错误输出到对话 |

**`FileNotFoundError` 特殊处理**（参考图文件找不到）：

当错误信息含 `参考图文件不存在` 时，Agent **不等待用户**，直接自动修复：

```
错误示例：参考图文件不存在: /tmp/upload/吊带裙.jpg（解析路径: /tmp/upload/吊带裙.jpg）
```

**自动修复步骤**：
1. 检查错误中的解析路径是否真实存在（`ls -la {解析路径}`）
2. 若文件存在但路径问题 → 用绝对路径重新调用脚本
3. 若文件不存在 → **立即将图片从用户上传位置复制到 `{output_dir}/`**：
   ```bash
   cp "{用户上传原始路径}" "{output_dir}/front.jpg"
   ```
4. 用 `{output_dir}/front.jpg`（绝对路径）替换原路径，重新执行失败的脚本
5. **根本预防**：在"图片预处理"步骤中已复制过则此错误不应出现——若出现说明预处理步骤被跳过，重新执行预处理

**错误输出格式**（固定模板，不得省略或摘要）：

> ❌ **脚本执行失败：`[脚本名]`**
>
> 错误详情：
> ```
> [完整的 stdout + stderr，一字不改，原样粘贴]
> ```
>
> 已生成文件：`[已成功生成的文件列表，若有]`
>
> 请根据上述错误排查后重试，或检查 API Key 是否有效、网络是否可达。

> **⚠️ Agent 规则：报错后不得静默重试、不得跳过、不得继续调用任何后续工具。必须等待用户响应。**

---

## 第六步：平台文案生成（可选）

Agent 直接按 `references/copy-prompts.md`（第一部分）中对应平台的 Prompt 模板生成商品文案。

> 📄 Prompt 模板见 `references/copy-prompts.md` → 一、平台文案 Prompt

### 操作方式

1. 根据用户选择的平台（taobao / jd / pdd / douyin / amazon / shopify），找到对应 Prompt 模板
2. 将 `{product_json}` 替换为第二步生成的商品卖点 JSON
3. 国际平台额外替换 `{market}`、`{language}`、`{brand_tone}`
4. Agent 直接生成文案，按区块标注输出
5. 将文案保存为 `./output/copy/{platform}_copy.txt`

> **无需外部脚本或 API Key，Agent 自身即可完成文案生成。**

---

## 第七步：详情页 HTML 生成（可选）

Agent 直接按 `references/copy-prompts.md`（第二部分）中对应平台的 Prompt 模板生成完整商品详情页 HTML。

> 📄 Prompt 模板见 `references/copy-prompts.md` → 二、详情页 HTML Prompt

### 操作方式

1. 根据用户选择的平台，找到对应详情页 HTML Prompt 模板
2. 将 `{product_json}` 替换为商品 JSON，`{copy_json}` 替换为第六步生成的文案，`{images_json}` 替换为套图列表
3. Agent 直接生成完整 HTML（内联 CSS，无外部依赖）
4. **图片使用相对路径**（HTML 保存在 `output/pages/`，图片位于 `output/`，所以路径为 `../图片名.jpg`）：
   - 白底主图 → `../白底主图.jpg`
   - 核心卖点图 → `../核心卖点图.jpg`
   - 卖点图 → `../卖点图.jpg`
   - 材质图 → `../材质图.jpg`
   - 场景展示图 → `../场景展示图.jpg`
   - 模特展示图 → `../模特展示图.jpg`
   - 多场景拼图 → `../多场景拼图.jpg`
5. 价格统一用 `[PRICE]` 占位符
6. 将 HTML 保存为 `./output/pages/{platform}_detail.html`

> **无需外部脚本或 API Key，Agent 自身即可完成 HTML 生成。**

---

## 第八步：产品展示视频生成（可选）

使用豆包 Seedance 模型，基于已生成的套图生成产品展示视频。

> ⚠️ **费用提示**：视频生成使用豆包 Seedance 模型（`doubao-seedance-2-0-260128`），会消耗一定 tokens 费用。Agent 必须在执行前明确告知用户并获得确认。

### 8.1 触发条件

Agent 在完成图片生成后，**主动询问用户**：

> 套图已全部生成完成。是否需要额外生成一段产品展示视频？
>
> - 使用豆包 Seedance 模型生成，需要 `ARK_API_KEY`
> - **会消耗一定 tokens 费用**，请确认是否继续
> - 需要从已生成的图片中选择**至少 2 张**作为参考图（最多 9 张）
> - 支持有声/无声两种模式

**用户确认后**，继续以下步骤。若用户拒绝，跳过本步骤。

### 8.2 用户交互

依次确认以下信息：

1. **选择参考图**：列出已生成的所有图片，让用户选择至少 2 张
2. **有声/无声**：询问用户是否需要生成带声音的视频
3. **视频描述**（可选）：用户可提供期望的视频内容描述，如"呈现产品细节，切换不同室内场景"
4. **视频比例**：默认 `16:9`，也可选 `9:16`（竖屏/短视频）或 `1:1`
5. **视频时长**：`5` 秒或 `10` 秒

### 8.3 视频 Prompt 敏感词规避

> ⚠️ 豆包 Seedance 对人物/服饰相关词汇有内容安全检测，以下词汇**禁止出现在 `--prompt` 中**。Agent 必须在构造 prompt 前完成替换。

| 禁用词 | 替换用词 |
|--------|---------|
| 模特 | 人物 / 穿着效果（仅描述效果时用） |
| 模特上身 | 室内穿着效果 / 穿着呈现 |
| 模特展示 | 穿着效果呈现 |
| 展示效果 | 呈现效果 |
| 展示视频 | 产品视频 |
| 专业展示 | 高清呈现 |
| 优雅法式场景 | 室内场景 / 家居场景 |
| 真人秀 | （直接删除） |

**Agent 从用户描述或商品 JSON 动态生成 `--prompt` 时，必须自动做上表替换。**

### 8.4 执行生成

**Agent 必须使用 `generate_result.json` 中的绝对路径传给 `--images`**，不得手动拼接相对路径：

```python
# 读取绝对路径（避免工作目录差异导致找不到文件）
import json
result = json.loads(open("{output_dir}/generate_result.json").read())
img_paths = [v["path"] for k, v in result.items() if v["status"] == "ok" and k in ("white_bg","lifestyle","model")]
```

```bash
python3 scripts/generate_video.py \
  --images {img_path_1} {img_path_2} {img_path_3} \
  --prompt "高清电商产品视频，依次呈现商品全貌、材质细节、室内穿着效果，过渡自然流畅" \
  --audio \
  --ratio 16:9 \
  --duration 5 \
  --output-dir {output_dir}/video/
```

> 💡 **图片大小自动处理**：generate_video.py 内置自动压缩，若图片超过 3MB 或分辨率超过 1920px，会在上传前自动压缩（需安装 `pip install Pillow`）。Agent **不需要手动压缩图片**。若未安装 Pillow 而图片过大，脚本会打印警告但仍尝试上传。

### generate_video.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--images` | **必填**，参考图片路径或 URL（至少 2 张，最多 9 张） | — |
| `--prompt` | 视频描述文本 | 空（模型自动理解图片内容） |
| `--audio` | 是否生成有声视频（加此 flag 为有声） | 无声 |
| `--ratio` | 视频比例：`16:9` / `9:16` / `1:1` / `4:3` / `3:4` / `21:9` | `16:9` |
| `--duration` | 视频时长（秒）：`4`/`5`/`6`/`8`/`10`/`12`/`15`（Seedance 2.0 支持 4-15s） | `6` |
| `--model` | 模型名称 | `doubao-seedance-2-0-260128` |
| `--api-key` | ARK API Key（也可通过 `ARK_API_KEY` 环境变量传入） | 环境变量 |
| `--max-wait` | 最大等待时间（秒） | `600` |
| `--output-dir` | 输出目录 | `./output/video/` |

输出：`product_video.mp4` + `video_result.json`（含 task_id、视频 URL、tokens 消耗等信息）。

> **前置条件**：需配置 `ARK_API_KEY` 环境变量。

---

## 执行检查清单

- [ ] **⛔ API Key 检测通过**（`check_providers.py` 输出 `configured` 非空，否则停止）
- [ ] 商品图片已上传（必须）
- [ ] 商品卖点已生成或用户已填写
- [ ] 平台已选择（决定语言和尺寸）
- [ ] 套图类型已选择（至少1种）
- [ ] 所有 Prompt 已审核（可选）
- [ ] 图像生成 API 可用

---

## 参考文件索引

| 文件 | 内容 |
|------|------|
| `references/platforms.md` | 各平台尺寸规范、主图要求、文案风格指南 |
| `references/image-types.md` | 7种套图的详细视觉规格与 Prompt 模板 |
| `references/analysis-prompts.md` | AI商品分析与卖点提取的系统 Prompt |
| `references/providers.md` | 供应商 API 接入详情 |
| `scripts/check_providers.py` | 检测已配置的**图像生成**供应商（读取环境变量） |
| `scripts/analyze.py` | **商品图视觉分析**（Qwen VL → 豆包视觉 → GPT-4o 自动降级，输出卖点 JSON） |
| `scripts/generate.py` | 调用图像生成 API（5个供应商，文案由模型直接渲染，支持 `--lang` / `--model` / `--base-url` / `--api-key`） |
| `references/copy-prompts.md` | 6平台文案 Prompt + 6平台详情页 HTML Prompt（Agent 直接使用，无需脚本） |
| `references/model-prompts.md` | 模特图 Prompt 模板（4种风格 + 品类自动映射） |
| `assets/models.json` | 内置 AI 模特库（45 个模特，含风格/性别/体型信息） |
| `assets/models/*.png` | 内置模特参考图（与 models.json 中 id 对应） |

| `scripts/generate_video.py` | 调用豆包 Seedance 生成产品展示视频（需 `ARK_API_KEY`） |

---

## API Key 配置

本 Skill 使用两类 API：

| 变量 | 用途 | 是否必需 |
|---|---|---|
| `DASHSCOPE_API_KEY` | 千问图像生成 + 千问 VL 商品识别（国内直连） | ✅ 推荐 |
| `ALIYUN_API_KEY` | `DASHSCOPE_API_KEY` 的兼容别名 | 可选 |

| `ARK_API_KEY` | 豆包 Seedream 图像生成 + Seedance 视频生成 + 豆包视觉商品识别（国内直连） | 可选 |
| `OPENAI_API_KEY` | DALL·E 3 图像生成（需代理） | 可选 |
| `GEMINI_API_KEY` | Gemini 原生图像生成（需代理） | 可选 |
| `STABILITY_API_KEY` | Stable Image Core（需代理） | 可选 |
| `*_BASE_URL` | 各供应商自定义代理地址（`OPENAI_BASE_URL` / `GEMINI_BASE_URL` 等） | 可选 |
| `*_MODEL` | 各供应商自定义模型名（`DASHSCOPE_MODEL` / `ARK_MODEL` / `GEMINI_MODEL` 等） | 可选 |

> **安全声明**：API Key 仅存于本地环境变量，直接调用各供应商官方 Endpoint，不经过任何第三方服务器中转。建议使用权限最小化的 Key，并定期轮换。

### 方式一：环境变量

```bash
# 至少配置一个图像供应商
export DASHSCOPE_API_KEY="sk-..."       # 阿里云 DashScope（国内直连，推荐）
export ARK_API_KEY="..."                # 字节跳动火山方舟（国内直连）
export OPENAI_API_KEY="sk-..."         # 需代理
export GEMINI_API_KEY="AIzaSy..."      # 需代理
export STABILITY_API_KEY="sk-..."      # 需代理

# 可选：自定义代理地址
export OPENAI_BASE_URL="https://my-proxy.com/v1"
export GEMINI_BASE_URL="https://my-proxy.com/gemini"
export DASHSCOPE_BASE_URL="https://my-proxy.com/dashscope"

# 可选：自定义模型名（不配置则使用默认值）
export DASHSCOPE_MODEL="qwen-image-2.0-pro"       # 默认 wan2.7-image-pro
export ARK_MODEL="doubao-seedream-5-0-260128" # 默认 doubao-seedream-5-0-260128
export GEMINI_MODEL="gemini-3.1-flash-image-preview"  # 默认同此
```

加入 `~/.zshrc` 或 `~/.bashrc` 后永久生效。

### 方式二：OpenClaw 配置文件

在 `$OPENCLAW_CONFIG_PATH`（默认 `~/.openclaw/openclaw.json`）中配置 `apiKey`，对应 `primaryEnv`（即 `DASHSCOPE_API_KEY`）：

```json5
{
  skills: {
    entries: {
      "ecommerce-image-suite": {
        apiKey: "DASHSCOPE_API_KEY_HERE",
      },
    }
  },
}
```
