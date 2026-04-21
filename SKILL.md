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
> 📋 **CLI 环境（如 Claude Code）**：无法直接拖拽上传图片，请提供以下任一方式：
> - 本地文件路径（如 `/Users/me/photos/product.jpg`）
> - 远程图片 URL（如 `https://example.com/product.jpg`）
> - Base64 字符串（`data:image/jpeg;base64,/9j/4AAQ...`）
> - Base64 文件路径（文件内容为 base64 编码的图片数据）
>
> 请选择编号（或直接上传图片 / 提供路径或 URL，我会自动识别类型），然后提供图片即可开始。

**2. 等待用户回复：**

- 用户选择编号后，记录 `input_image_type`（见映射表），再提示提供对应数量的图片（图形界面：上传图片；CLI：提供本地路径 / URL / base64）
- 用户直接上传图片或提供路径/URL/base64（未选编号），自动检测 `input_image_type`，进入情况 B

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

### ⚠️ 确定输出目录（output_dir）

> ⚠️ **Agent 必须先检查已有目录，按最大编号 +1 递增，禁止直接使用 001！**

**每个商品任务使用独立子目录**，避免多批次生成图与 `generate_result.json` 互相覆盖。

**自动递增规则**：
1. 检查 `./output/` 下已有三位数编号子目录（`001/`、`002/`、`003/`、`004/`……）
2. 取最大编号 +1 作为本次目录（如已有 `004/` 则本次使用 `005/`）
3. 若 `./output/` 不存在或为空，则从 `001` 开始

**Agent 操作流程**：

1. **先检查已有目录**（必须执行）：

```bash
# Bash 方式
if [ -d "./output" ]; then
  n=$(ls -d ./output/[0-9][0-9][0-9] 2>/dev/null | sort | tail -1 | grep -oE '[0-9]+$')
  next=$(printf "%03d" $((${n:-0} + 1)))
  echo "检测到已有目录，将使用: ${next}"
else
  next=001
  echo "output 目录为空，将从 001 开始"
fi
```

2. **创建输出目录**：

```bash
output_dir="$(pwd)/output/${next}"
mkdir -p "${output_dir}"
echo "本次套图将保存到: ${output_dir}"

3. **告知用户**：

> 检测到已有商品任务（最高编号：004），本次将使用 **output/005/**。
> 直接继续，或输入自定义目录名（如 `黑色连衣裙`）。

**同一任务使用多个模型时**：在任务子目录下再创建模型名子目录（如 `output/001/nano-banana/`、`output/001/gpt-image-1.5/`）。

**多模型子目录**（同一任务对比不同模型效果）：

```bash
# 首个模型
output_dir="$(pwd)/output/001/nano-banana"
mkdir -p "${output_dir}"
# 后续模型
output_dir_2="$(pwd)/output/001/gpt-image-1.5"
mkdir -p "${output_dir_2}"
```

**非 Bash 客户端**：用文件系统工具列出 `./output/` 子目录，找最大数字编号 +1；若无法判断则默认 `./output/001/`。

用户也可**自定义目录名**（如按商品命名）。

记录 `output_dir` 后，后续所有步骤统一使用此路径。

> ⚠️ **常见错误**：直接使用 `output/001/` 会覆盖之前的任务！必须先检查最大编号。

---

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
2. `output_dir` 已在上一步创建，无需重复 `mkdir`
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
      "visual_keywords": ["cross-strap neckline", "V-neck detail", "collarbone"],
      "icon": "design",
      "en": "Cross-strap V-neckline",
      "zh": "个性交叉领口"
    },
    {
      "type": "pattern",
      "title": "唯美碎花印花",
      "description": "黑色底面点缀淡雅樱花图案，营造复古浪漫氛围",
      "visual_keywords": ["floral print pattern", "cherry blossom motif"],
      "icon": "design",
      "en": "Floral Print",
      "zh": "唯美碎花印花"
    },
    {
      "type": "silhouette",
      "title": "灵动鱼尾设计",
      "description": "下摆采用层次感荷叶边，行走间灵动飘逸",
      "visual_keywords": ["ruffle hemline layers", "flowy silhouette"],
      "icon": "fit",
      "en": "Ruffle Hemline",
      "zh": "灵动鱼尾设计"
    }
  ],

  "target_audience": "追求个性时尚、喜爱甜美法式风格的年轻女性",
  "target_scenes": ["海边度假", "浪漫约会", "周末聚会", "盛夏日常"],
  "target_scene_envs": [
    "tropical beach with golden sand and turquoise ocean, bright midday sunlight",
    "romantic outdoor restaurant terrace at dusk, warm candlelight, string lights",
    "stylish rooftop party, urban skyline backdrop, golden hour glow",
    "sunny park path, lush green trees, soft natural bokeh"
  ],
  "product_style": "甜美法式浪漫",

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

**用户确认后继续**；若用户说"不对"或表示不准确：

> ⚠️ **Agent 必须执行以下操作之一**：
> - **方式A（推荐）**：直接调用项目中内置的专业分析脚本 `analyze.py` 重新分析
> - **方式B**：询问用户"是否使用项目中更专业的视觉分析脚本重新分析？"

**调用 analyze.py 的命令**：

```bash
# 自动选择已配置的视觉供应商（Qwen → 豆包 → OpenAI）
python3 scripts/analyze.py ./product.jpg --output ./output/product.json
```

使用 analyze.py 输出的结果继续后续流程。

> ⚠️ **错误处理**：
> - 若脚本返回 `exit code 2`，表示未配置任何视觉识别 API Key → Agent 必须告知用户配置环境变量（DASHSCOPE_API_KEY / ARK_API_KEY / OPENAI_API_KEY）
> - 若脚本返回 `exit code 1`，表示 API 调用失败或 JSON 解析失败 → Agent 必须将完整错误信息输出给用户
> - 若脚本无输出但成功执行（exit code 0），检查是否使用了 `--output` 参数导致结果写入文件而非 stdout

---

### analyze.py 脚本详细用法

**完整用法示例**：

```bash
# 自动选择已配置的视觉供应商（Qwen → 豆包 → OpenAI）
python3 scripts/analyze.py ./product.jpg

# 指定供应商
python3 scripts/analyze.py ./product.jpg --provider tongyi

# 保存到文件供后续步骤使用
python3 scripts/analyze.py ./product.jpg --output ./output/product.json
```

**analyze.py 供应商优先级**（视觉识别，与图像生成供应商独立）：

> ⚠️ **Agent 调试检查清单**（当 analyze.py "没有分析出来"时）：
> 1. **检查环境变量**：运行 `echo $DASHSCOPE_API_KEY` 或 `python3 scripts/check_providers.py` 确认是否配置
> 2. **检查图片路径**：确认传入的图片路径存在且可读（`ls -la ./product.jpg`）
> 3. **检查脚本输出**：分析失败时脚本会将错误输出到 stderr，Agent 必须捕获并显示给用户
> 4. **尝试手动调用**：让用户手动运行 `python3 scripts/analyze.py ./product.jpg` 查看详细错误

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

### 自动补充类型：三角度拼图（正面/侧面/背面）

**触发条件**：当仅提供一张商品图时（`len(product_images) == 1`），脚本**自动生成** `three_angle_view` 类型图片，实现360度展示。

| 图片类型 | 核心目标 | 推荐位置 |
|---|---------|---------|
| **三角度拼图** | 同比例展示正面/侧面/背面三个角度，实现完整360度可见性 | 补充图 |

**设计说明**：
- 采用三栏等宽拼图布局，左中右分别展示：正面、侧面、背面
- 服装类：使用模特展示（正面/侧面/背面，同一模特）
- 非服装类：使用商品平铺或挂拍展示
- 统一背景色（白色/浅灰），保持专业商拍风格

**Agent 操作**：
- 无需手动添加 `three_angle_view` 到 `--types`
- 脚本检测到仅一张图时自动插入到 `multi_scene` 之前
- 若用户已提供多角度图片，则不自动生成此类型

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
| `selling_points` | 第二步 JSON | 确保每项含 `zh`/`en` 字段，新格式额外含 `title`/`description`/`visual_keywords`（英文关键词） |
| `garment_position` | Agent 判断 | 服装上衣 → `top`；下装 → `bottom`；连体/全身 → `full-body`；非服装 → `non-apparel` |
| `product_name` | 第二步 JSON | 完整商品名 |
| `visual_features` | 第二步 JSON | 结构化视觉特征对象 |
| `target_scenes` | 第二步 JSON | 中文目标使用场景列表，如 `["海边度假", "约会晚宴"]` |
| `target_scene_envs` | **Agent 智能生成（优先）** | 与 `target_scenes` 一一对应的英文场景环境描述。**Agent 根据商品信息分析后生成**，包含具体的视觉元素（光线、环境、氛围）。示例：`"tropical beach, golden sand, turquoise ocean, bright midday sunlight, coastal vibe"`。<br><br>⚠️ **禁止依赖硬编码映射**：generate.py 虽有 `_scene_to_env()` 兜底函数（中文场景名→英文环境），但 Agent **必须优先生成 `target_scene_envs`**。兜底函数仅作为最后手段，且效果远不如 Agent 智能生成。 |
| `product_style` | 第二步 JSON / Agent 补充 | 商品风格标签，如 `"法式浪漫"` / `"运动休闲"`，用于 lifestyle 图标题 |
| `target_audience` | 第二步 JSON | 目标用户描述，用于推断模特性别/年龄 |
| `print_design_lock` | 第二步 JSON | 精确锁定商品设计细节的英文约束短语，防止生成时设计被修改 |

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
      "visual_keywords": ["cross-strap neckline", "V-neck detail"],
      "zh": "个性交叉领口", "en": "Cross-strap V-neckline",
      "zh_desc": "V领交叉绑带，凸显锁骨曲线", "en_desc": "Delicate cross straps frame the neckline elegantly"
    },
    {
      "type": "pattern", "title": "唯美碎花印花",
      "description": "黑色底面点缀淡雅樱花图案，营造复古浪漫氛围",
      "visual_keywords": ["floral print pattern", "cherry blossom motif"],
      "zh": "唯美碎花印花", "en": "Floral Print",
      "zh_desc": "黑底樱花印花，浪漫复古韵味", "en_desc": "Romantic floral print adds vintage charm"
    },
    {
      "type": "silhouette", "title": "灵动鱼尾设计",
      "description": "下摆采用层次感荷叶边，行走间灵动飘逸",
      "visual_keywords": ["ruffle hemline layers", "flowy silhouette"],
      "zh": "灵动鱼尾设计", "en": "Ruffle Hemline",
      "zh_desc": "荷叶边层次下摆，行走飘逸灵动", "en_desc": "Layered ruffle hem flows beautifully with movement"
    }
  ],
  "target_audience": "追求甜美法式风格的18-30岁年轻女性",
  "target_scenes": ["海边度假", "浪漫约会", "周末聚会"],
  "target_scene_envs": [
    "tropical beach, golden sand and turquoise ocean, bright midday sunlight, coastal vibe",
    "romantic outdoor restaurant terrace at dusk, warm candlelight, string lights bokeh",
    "chic rooftop social gathering, urban skyline backdrop, golden hour glow"
  ],
  "product_style": "甜美法式浪漫",
  "print_design_lock": "black spaghetti dress with delicate cherry blossom floral print, cross-strap V-neckline, ruffle hemline — exact same print pattern, color and proportions must not change",
  "input_image_type": "flat_lay"
}
```

### 核心卖点图（key_features）展示样式选择

> ⚠️ **Agent 必须根据商品卖点特征智能分析并推荐，不得使用简单规则匹配。**

**Agent 智能分析流程**：

1. **读取商品卖点**：分析 `selling_points` 数组，判断卖点类型
   - 材质细节类（莫代尔面料、真丝、蕾丝）→ 需要局部特写 → 推荐 **① 放大镜气泡**
   - 功能特点类（防晒、速干、防水、保温）→ 需要图标化说明 → 推荐 **② 信息图标列表**
   - 设计亮点类（交叉细吊带、荷叶边下摆、法式浪漫）→ 需要标注指向 → 推荐 **③ 标注线指示**
   - 高端定位类（奢侈品质感、极简设计）→ 需要分割排版 → 推荐 **④ 分割板块**

2. **给出有理有据的推荐**：

> 根据分析您的商品卖点「莫代尔柔软材质、交叉细吊带设计、荷叶边下摆」，我推荐：
>
> **① 放大镜气泡** — 原因：您的卖点集中在材质细节（莫代尔）和设计细节（吊带、荷叶边），放大镜气泡可以清晰展示这些局部特写，让用户直观感受材质质感和设计亮点。

> 请选择编号（或直接回车使用推荐），也可以选择其他样式：

向用户展示所有选项：

> **① 放大镜气泡** — 居中主图 + 3个圆形放大镜气泡，连细线到商品局部
> **② 信息图标列表** — 左侧商品图 + 右侧 3 条图标+文字卖点列表
> **③ 标注线指示** — 商品居中 + 手写风格标注线指向各部位（生活杂志风）
> **④ 分割板块** — 上下/左右分割，每块一个卖点 + 对应商品局部特写（极简洁风）

**用户确认后**：Agent 通过 `--per-type-templates key_features:N` 参数传递选择（①→默认，②→默认非服装，③→2，④→3）

---

> 💡 **重要**：Agent 推荐必须基于卖点分析，而非简单规则匹配。例如：
> - 错误：`if 服装 then 推荐①`
> - 正确：`if 卖点包含材质细节 or 设计亮点 then 推荐①，理由是...`

放大镜气泡内容自动取自 `selling_points[0..2].visual_keywords`（首两个关键词，**必须为英文**，直接嵌入英文 Prompt）。

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

> ⚠️ **Agent 必须主动向用户确认模特来源，不得跳过或自行决定。**

若需要模特，向用户提问（**仅询问模特来源**）：

> 模特展示图的**模特来源**请选择：
>
> 1. **使用内置模特库** — 从预置的 AI 模特中选择，Agent 展示图片后确认（推荐，形象稳定一致）
> 2. **AI 自动生成** — 由 AI 生成随机模特，生成后展示给您确认，确认后锁定用于场景图和多场景图

**② 模特种族偏好（根据目标市场询问）**

Agent 根据目标销售平台/地区询问用户模特种族偏好：

> 请问您希望使用什么种族的模特？（根据目标市场选择）
>
> 1. **亚洲模特** — 适合国内市场（淘宝、京东、拼多多）或东亚市场
> 2. **欧美模特** — 适合跨境平台（Amazon、独立站）或欧美市场
> 3. **混合种族** — 多元化展示，适合国际化定位

Agent 将用户选择传递给 generate.py：在商品 JSON 中添加 `"model_ethnicity": "asian/western/mixed"` 字段。

**③ 展示风格（Agent 根据商品分析 JSON 自动判断，无需询问用户）**

Agent 获取商品 JSON 后，按以下规则自动选择 `--model-style`：

| 判断条件（任一字段含以下关键词即触发） | 自动选择 | 参数 |
|---|---|---|
| `product_type` 含：内衣 / 睡衣 / 泳装 / 比基尼 / 塑形衣 / 紧身裤 / 瑜伽裤 / 健身衣 | 贴身合体 | `--model-style bodycon` |
| `style` 含：修身 / 紧身 / 贴身 / slim / bodycon | 贴身合体 | `--model-style bodycon` |
| `material` 含：莫代尔 / 弹力 / 氨纶 / spandex / lycra | 贴身合体 | `--model-style bodycon` |
| 其他所有商品 | 标准商拍 | 默认，无需传参 |

> 若关键词无法确定，默认「标准商拍」。自动选择后可在回复中顺带说明（如：「已根据商品类型自动选择贴身合体展示风格」），用户如不满意可随时告知调整。

### 4.3 内置模特选择（用户选择方案 1）

> 🔒 **人物锁定**：选定内置模特后，`--model-image` 参数会作为参考图传入生图脚本。generate.py 会在 Prompt 中嵌入强制指令，要求生图模型严格复刻参考图中的人物外貌，**不得替换为其他人物或外国面孔。**

> **CLI 环境说明**：若当前运行环境（如 Claude Code CLI 或其他命令行界面）不支持内联展示图片，**禁止说"让我为您展示生成的套图"**，应直接列出图片的绝对路径。此规则适用于本技能所有需要展示图片的场景（模特选择、模特确认、生成结果汇总）。图片路径从 `generate_result.json` 或 `assets/models/{id}.png` 读取。

**Agent 必须展示模特图片（图形界面）或列出图片路径（CLI 环境），禁止只用文字描述。**

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
> [展示 {model_image_path} 图片]（CLI 环境：直接输出路径 `{model_image_path}`）
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

## 第四步半 B：视觉风格模板智能推荐

> ⚠️ **此步骤必须在第五步生图之前完成。** Agent 必须根据商品特征智能推荐模板，不得使用简单规则匹配。

### Agent 智能分析流程

1. **分析商品多维信息**：
   - `product_style`：甜美法式、运动休闲、商务正装、极简主义...
   - `target_audience`：18-30岁年轻女性、商务人士、学生...
   - `selling_points`：材质特点、设计亮点、功能卖点...
   - `visual_features`：主色调、图案风格、廓形特征...

2. **综合判断推荐模板**：

| 商品特征分析 | 推荐模板 | 推荐理由 |
|------------|---------|---------|
| 甜美/法式/浪漫 + 女性目标人群 | ② 生活杂志 | 自然光氛围感符合浪漫风格，适合小红书等种草平台 |
| 运动/街头/活力 + 年轻客群 | ④ 活力爆款 | 高饱和冲击力强，符合抖音/拼多多视觉风格 |
| 商务/高端/极简 + 成熟人群 | ③ 极简高冷 | 留白奢品感传达高端定位，适合独立站/Amazon |
| 数码/运动/夜场 + 男性为主 | ⑤ 暗调质感 | 电影感打光突显质感，符合男性审美 |
| 无明显风格特征或新手 | ① 默认商拍 | 干净通用，各平台均适合 |

3. **给出有理有据的推荐**：

> 根据分析您的商品特征：
> - 风格定位：甜美法式浪漫
> - 目标人群：18-30岁年轻女性
> - 主色调：柔和粉色系
> - 平台定位：淘宝/小红书
>
> 我推荐 **② 生活杂志**：
> **理由**：自然光氛围感与甜美法式风格高度契合，黄金时刻的光效能增强浪漫氛围，非常适合小红书等种草平台的视觉调性。

> 请选择编号（或直接回车使用推荐），也可以选择其他模板：

### 6 套视觉风格模板参考

| 套数 | 名称 | 风格描述 |
|------|------|---------|
| **①** | 默认商拍 | 标准电商商拍，干净明亮，重点突出商品 |
| **②** | 生活杂志 | 自然光，有氛围感和生活质感 |
| **③** | 极简高冷 | 极简留白，高反差，奢侈品质感 |
| **④** | 活力爆款 | 高饱和度，大字冲击，活力感强 |
| **⑤** | 暗调质感 | 深色系，电影质感，戏剧性打光 |
| **⑥** | 非对称布局 | 左侧大图（60%）+ 右侧细节图（40%），突出主次层次 |

**各套模板对不同图类型的效果**（供用户参考）：

| 图类型 | ① 默认商拍 | ② 生活杂志 | ③ 极简高冷 | ④ 活力爆款 | ⑤ 暗调质感 | ⑥ 非对称布局 |
|--------|-----------|-----------|-----------|-----------|-----------|-------------|
| 核心卖点图 | 放大镜气泡/信息图标 | 商品居中+手写标注线 | 黑底白字+单色线框 | 爆炸形背景+粗体红字 | 深灰底+金色描边气泡 | 左侧气泡+右侧说明 |
| 卖点图 | 卧室暖光 | 咖啡馆窗前自然光 | 纯白棚拍极简 | 户外街头高饱和 | 暗调棚拍聚光灯 | 左侧大场景+右侧细节 |
| 材质图 | 极macro面料 | 木纹/大理石桌面铺陈 | 折叠几何极简 | 对折叠叠高饱和 | 暗色背景金边光圈 | 左侧面料+右侧纹理 |
| 场景展示图 | 校园/咖啡厅 | 户外公园黄金时刻 | 白色简洁室内 | 街头活力 | 城市夜景/聚光棚拍 | 左侧主景+右侧环境 |
| 模特展示图 | 户外阳光走路 | 坐姿休闲咖啡厅 | 白底棚拍全身 | 街拍动态跳跃 | 暗调棚拍聚焦 | 左侧全身+侧面特写 |
| 多场景拼图 | 左右分屏 | 三格日记卡片 | 上下黑白分割 | 对角爆炸分割 | 暗调三屏电影感 | **左侧大图+右侧小图** |

**用户确认后**：Agent 通过 `--template-set N` 参数传递选择

---

### 非对称布局模板（⑥）专项询问

> ⚠️ **Agent 必须在用户确认全局模板后，主动询问是否使用非对称布局。** 非对称布局（模板⑥）采用"左侧大图（60%）+ 右侧细节图（40%）"的构图，特别适合需要突出主次关系的图类型。

**Agent 操作流程：**

1. **智能推荐适合的图类型**：根据商品特征分析，推荐适合使用非对称布局的图类型

| 图类型 | 非对称布局效果 | 适合商品特征 |
|--------|---------------|-------------|
| 核心卖点图 | 左侧气泡+右侧说明文字 | 卖点较多、需要图文结合的商品 |
| 卖点图 | 左侧大场景+右侧细节特写 | 有明确设计细节、需要突出局部卖点 |
| 材质图 | 左侧面料+右侧纹理特写 | 材质质感重要、需要放大展示的商品 |
| 场景展示图 | 左侧主景+右侧环境氛围 | 场景氛围强、需要环境烘托的商品 |
| 模特展示图 | 左侧全身+侧面特写 | 服装/鞋类、需要多角度展示的商品 |
| 多场景拼图 | 左侧大图+右侧小图对比 | 有多场景对比需求的商品 |

2. **给出个性化推荐**：

> 根据分析您的商品特征，非对称布局（模板⑥）特别适合以下图类型：
>
> • **[推荐图类型1]** — 原因：[具体分析]
> • **[推荐图类型2]** — 原因：[具体分析]
>
> 非对称布局采用"左侧大图+右侧细节"的构图，能更好地突出商品的主次层次。
>
> **请选择您希望使用非对称布局的图类型（可多选）：**
>
> A. 核心卖点图 — 左侧气泡+右侧说明文字
> B. 卖点图 — 左侧大场景+右侧细节特写
> C. 材质图 — 左侧面料+右侧纹理特写
> D. 场景展示图 — 左侧主景+右侧环境氛围
> E. 模特展示图 — 左侧全身+侧面特写
> F. 多场景拼图 — 左侧大图+右侧小图对比
> G. 无需使用非对称布局
>
> **请输入字母（可多选，如 ABDF 或 G）：**

3. **用户选择后**：Agent 使用 `--per-type-templates` 参数传递选择

示例：
- 用户选择 A、D、F → `--per-type-templates key_features:6,lifestyle:6,multi_scene:6`
- 用户选择 G → 不添加额外参数

**高级用法**：用户还可对其他图类型指定不同模板（如"材质图用③，其余用②"），Agent 使用 `--per-type-templates key_features:2,material:3` 参数传递。

---

> 💡 **重要**：Agent 推荐必须基于商品特征的多维分析，而非简单 `if 甜美 then ②`。推荐理由要具体说明分析过程。

---

## 第五步：多供应商图像生成

> 📄 各供应商 API 接入详情见 `references/providers.md`
### 5.0 选择图像生成供应商与模型

> ⚠️ **Agent 必须在执行生图前向用户确认供应商，不得自行决定。**

首先展示前置检查中检测到的可用供应商列表，然后向用户提问：

> 检测到以下图像生成供应商可用：
>
> | 编号 | 供应商 | 默认模型 | 参考图 | 国内直连 |
> |------|--------|---------|-------|---------|
> | 1 | 阿里云通义 | `wan2.7-image-pro` | ✅ | ✅ |
> | 2 | 字节跳动豆包 | `doubao-seedream-4-5-251128` | ✅ | ✅ |
> | 3 | Google Gemini | `gemini-3.1-flash-image-preview` | ✅ | 需代理 |
> | 4 | OpenAI | `dall-e-3` | ⚠️ 仅 GPT Image | 需代理 |
> | 5 | Stability AI | `core` | ❌ | 需代理 |
>
> _(仅展示已配置 API Key 的供应商)_
>
> **参考图说明**：提供商品参考图后，生成的图片会保持商品外观（图案、材质、轮廓）。推荐优先选择标注 ✅ 的供应商。
>
> 请选择使用哪个供应商？（如需使用非默认模型，也可一并告知）

**OpenAI 特殊说明**：默认 `dall-e-3` **不支持参考图**，会根据描述重新生成商品外观。如需保留原图外观，需使用 GPT Image 模型（如 `gpt-image-1.5`），可通过环境变量 `OPENAI_MODEL` 或参数 `--model` 指定。

**若用户未明确指定**，优先推荐国内直连供应商（通义 > 豆包），并告知用户。

### 5.1 语言选择

> ⚠️ **Agent 必须在选择供应商后立即确认目标语言，不得跳过。**

向用户提问：

> 您的目标销售平台是？
>
> **① 国内平台**（淘宝、京东、拼多多、抖音等）→ 使用**中文简体**
> **② 国际平台**（Amazon、独立站、Shopee 等）→ 使用**English**
>
> 选择后将影响所有生成图片的文字内容（卖点标签、场景文字等）。

**记录语言选择**：
- 国内平台 → `lang = "zh"`，传递 `--lang zh`
- 国际平台 → `lang = "en"`，传递 `--lang en`

> ⚠️ **Gemini/OpenAI 特别注意**：选择国内平台时，Agent 必须在调用 generate.py 前确保商品 JSON 中的 `zh_desc`/`en_desc` 和 `visual_keywords` 字段正确填充，并在 prompt 中明确约束"中文简体"。

---

### 5.2 场景智能推荐与确认

> ⚠️ **Agent 必须根据商品具体特征动态生成场景推荐，禁止使用固定模板列表。**

**Agent 智能分析流程**：

1. **深度读取商品信息**：分析以下字段，提取商品特征
   - `product_name`：黑色碎花交叉细吊带荷叶边连衣裙
   - `product_style`：甜美法式浪漫
   - `target_audience`：18-30岁年轻女性
   - `selling_points`：莫代尔柔软材质、交叉细吊带、荷叶边下摆、碎花印花
   - `visual_features.main_color`：黑色/深色系
   - `visual_features.pattern`：碎花印花

2. **基于特征动态生成场景**（而非套用固定列表）：

| 商品特征提取 | 动态生成场景示例 | 推荐理由 |
|------------|----------------|---------|
| **碎花印花** + 甜美风格 | 春日野餐、花园下午茶、公园花海 | 碎花与自然环境相得益彰 |
| **交叉细吊带 + 荷叶边** + 年轻女性 | 音乐节、户外咖啡、校园漫步 | 法式设计适合休闲社交场景 |
| **莫代尔柔软材质** + 浪漫定位 | 蜜月旅行、海滩度假、日落散步 | 柔软材质适合浪漫氛围场景 |
| **黑色/深色系** + 甜美风格 | 夜市约会、酒吧小聚、晚餐约会 | 深色适合晚间社交场景 |

3. **给出个性化推荐**（禁止套用模板）：

> 根据分析您的商品「黑色碎花交叉细吊带荷叶边连衣裙」：
> - **印花特征**：碎花图案 → 适合户外自然场景（野餐、花园、公园）
> - **设计特征**：交叉细吊带 + 荷叶边 → 法式浪漫风格 → 适合休闲社交（咖啡、下午茶）
> - **材质特征**：莫代尔柔软 → 适合浪漫氛围（度假、约会）
> - **目标人群**：18-30岁年轻女性 → 适合活力场景（音乐节、校园、夜市）
>
> 我为您生成以下个性化场景推荐：
>
> | 编号 | 场景 | 推荐理由 |
> |------|------|---------|
> | ① | 春日野餐 | 碎花印花与草地环境天然搭配，展现甜美户外氛围 |
> | ② | 花园下午茶 | 法式浪漫风格，碎花与花园场景相得益彰 |
> | ③ | 夜市约会 | 黑色深色系适合晚间场景，吊带设计展现约会魅力 |
> | ④ | 音乐节活力 | 年轻目标人群，法式设计适合户外活力场景 |
>
> 请选择编号（可多选，如 1 2 3 4），或输入自定义场景名称。

4. **用户确认后生成英文环境描述**：

Agent 将用户选择的中文场景转换为详细的英文环境描述：

```json
{
  "target_scenes": ["春日野餐", "花园下午茶", "夜市约会", "音乐节活力"],
  "target_scene_envs": [
    "spring picnic on green grass lawn, wildflowers scattered, dappled sunlight through trees, fresh outdoor atmosphere",
    "garden afternoon tea, blooming flowers, vintage table setting, warm natural light, romantic French style",
    "night market dating, string lights and lanterns, vibrant evening atmosphere, social dining scene",
    "music festival energy, young crowd, outdoor stage, dynamic lighting, lively concert atmosphere"
  ]
}
```

> 💡 **重要**：场景推荐必须基于商品具体特征（印花、设计、材质、颜色）**动态生成**，禁止使用固定模板列表（如"海边度假、浪漫约会、咖啡厅休闲"）。每件商品的特征不同，推荐场景应该不同。

**Agent 场景生成思考过程**（内部思考，不向用户展示）：

```
1. 读取商品信息：product_name=黑色碎花连衣裙, pattern=碎花, style=甜美法式
2. 提取特征关键词：碎花→户外自然；法式→休闲社交；黑色→晚间场景
3. 组合特征生成场景：
   - 碎花 + 户外 → 春日野餐、花园下午茶
   - 法式 + 社交 → 咖啡厅、音乐节
   - 黑色 + 晚间 → 夜市约会、酒吧小聚
4. 筛选最合适的 3-5 个场景，给出推荐理由
```

---

### 5.3 生成模式选择

> ⚠️ **Agent 必须在执行生图前选择模式，不得跳过。**

当前共有 **[N] 种套图**，每种类型生成 **1 张**，请选择生成方式：

> 1. **一次性批量生成** — 自动依次生成所有套图（推荐，省时）
> 2. **逐张确认** — 每张图生成后暂停，查看效果后再继续

**一次性模式**：直接调用 generate.py 传入全部 `--types`，生成完后读取 `generate_result.json`，列出所有图片的绝对路径（CLI 环境）或逐一展示图片（图形界面环境）。

**逐张模式**：每次只传入一个 `--types`，生成后向用户列出该图的绝对路径（CLI 环境）或展示图片（图形界面环境），获得确认后再生成下一张。若用户对某张不满意，可修改 Prompt 后重新生成该张。

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
| `--types` | 逗号分隔的套图类型；当仅提供一张商品图时自动添加 `back_side_view` | 全部 7 种 |
| `--lang` | **重要**：图片内嵌文案语言。国内平台→`zh`（中文简体），国际平台→`en`（English）。Gemini/OpenAI 需根据此值在 prompt 中明确约束语言 | `zh` |
| `--model-style` | 模特展示风格：`standard`（标准商拍）/ `bodycon`（贴身合体，适用于紧身衣物） | `standard` |
| `--template-set` | 全局视觉风格模板：`1`=默认商拍 `2`=生活杂志 `3`=极简高冷 `4`=活力爆款 `5`=暗调质感 `6`=非对称布局 | `1` |
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
