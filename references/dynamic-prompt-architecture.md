# 动态Prompt生成架构设计

## 现有问题

**固定模板架构的缺陷**：
```
固定模板 → 填充占位符 → 生成图片
```

- ❌ 所有商品用同一套Prompt
- ❌ 文案内容固定（如"宽松版型设计"），不适合连衣裙、鞋子等其他品类
- ❌ 无法根据商品特点（颜色、材质、款式）动态调整
- ❌ 无法利用分析出的卖点

---

## 新架构设计

```
商品分析 → 动态Prompt生成 → 生图
```

### 核心原则

1. **基于商品真实特征生成**：不是套模板，而是理解商品后创作
2. **卖点驱动**：每张图的Prompt都要体现核心卖点
3. **平台适配**：根据平台规范调整尺寸、风格、文字要求
4. **保持一致性**：所有图片中的商品必须保持一致

---

## 第一步：商品深度分析

### 分析维度

```json
{
  // 基础信息
  "product_name": "黑色碎花交叉细吊带荷叶边下摆连衣裙",
  "product_category": "连衣裙",
  "product_subtype": "吊带裙",

  // 视觉特征（从图片中提取）
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

  // 核心卖点（用户确认或AI分析）
  "selling_points": [
    {
      "type": "design",
      "title": "个性交叉领口",
      "description": "V领结合多重细绑带设计，凸显优雅锁骨曲线",
      "visual_keywords": ["交叉绑带", "V领", "锁骨", "层次感"]
    },
    {
      "type": "pattern",
      "title": "唯美碎花印花",
      "description": "黑色底面点缀淡雅樱花图案，营造复古浪漫氛围",
      "visual_keywords": ["碎花", "樱花", "复古", "浪漫"]
    },
    {
      "type": "silhouette",
      "title": "灵动鱼尾设计",
      "description": "下摆采用层次感荷叶边，行走间灵动飘逸",
      "visual_keywords": ["鱼尾", "荷叶边", "飘逸", "层次"]
    }
  ],

  // 目标用户与场景
  "target_audience": "追求个性时尚、喜爱甜美法式风格的年轻女性",
  "target_scenes": ["海边度假", "浪漫约会", "周末聚会", "盛夏日常"],

  // 商品图类型检测
  "input_image_type": "flat_lay", // flat_lay(平铺) / hanging(挂拍) / model(模特)
  "number_of_input_images": 1-3 // 支持1-3张
}
```

---

## 第二步：动态Prompt生成策略

### Prompt生成逻辑

对每种图片类型，根据商品特征动态生成Prompt：

#### 1. 白底主图
```python
def generate_white_bg_prompt(product_analysis):
    """生成白底主图Prompt"""

    # 提取关键视觉特征
    main_features = extract_main_features(product_analysis)

    # 构建描述
    description = f"""
    {product_analysis['product_name']},

    视觉特征：
    - 主色：{product_analysis['visual_features']['main_color']}
    - 设计：{', '.join(product_analysis['visual_features']['pattern'])}
    - 版型：{product_analysis['visual_features']['silhouette']}
    - 细节：{product_analysis['visual_features']['neckline']}领，
      {product_analysis['visual_features']['hemline']}

    Displayed on pure white background (RGB 255,255,255),
    product occupies 90% of frame,
    {get_angle_prompt(product_analysis['input_image_type'])},
    clean studio lighting.

    CRITICAL: Keep the product EXACTLY the same —
    same {main_features['color']}, same {main_features['pattern']},
    same {main_features['neckline']}, same {main_features['hemline']},
    do not modify any design detail.
    """

    return description
```

#### 2. 核心卖点图
```python
def generate_key_features_prompt(product_analysis, platform_style):
    """生成核心卖点图Prompt（根据平台风格）"""

    # 获取前3个卖点
    top_features = product_analysis['selling_points'][:3]

    # 根据平台风格生成
    if platform_style == "taobao_magazine":
        # 淘宝杂志风：优雅衬线体
        prompt = f"""
        Clean infographic with warm beige background ({platform_style['bg_color']}).

        Left side (45%): Complete front view of {product_analysis['product_name']},

        Right side layout:
        - Heading "{platform_style['heading']}" at top-right,
          rendered in elegant serif font (Noto Serif SC),
          {platform_style['heading_size']}px, letter-spacing 3px,
          {platform_style['heading_color']}

        - 3 feature icons vertically arranged:
        """

        # 添加每个卖点的具体描述
        for i, feature in enumerate(top_features):
            prompt += f"""
          {i+1}. Icon for "{feature['title']}"
             Label: "{feature['title']}"
             Visual emphasis: {', '.join(feature['visual_keywords'][:2])}
             """

    elif platform_style == "pinduoduo_pop":
        # 拼多多POP风：粗体高饱和
        prompt = f"""
        Bold infographic with vibrant background.

        Extra-bold heading "{platform_style['heading']}",
        tilted -3 degrees, Pinduoduo red (#E02E24).

        3 feature icons with yellow burst backgrounds:
        """

        for i, feature in enumerate(top_features):
            prompt += f"""
          {i+1}. "{feature['title']}" — {feature['description'][:30]}...
             """

    # 添加商品一致性约束
    prompt += f"""

    IMPORTANT: Render all specified text labels directly into the image.

    CRITICAL: Keep {product_analysis['product_name']} EXACTLY the same —
    same {product_analysis['visual_features']['main_color']},
    same {product_analysis['visual_features']['pattern']},
    same {product_analysis['visual_features']['neckline']},
    do not modify any design detail.
    """

    return prompt
```

#### 3. 卖点图（单点深度展示）
```python
def generate_feature_highlight_prompt(product_analysis, feature_index, platform_style):
    """生成单卖点深度展示图"""

    # 选择要展示的卖点
    feature = product_analysis['selling_points'][feature_index]

    # 根据卖点类型选择场景
    scene_type = get_scene_for_feature(feature['type'], product_analysis)

    prompt = f"""
    {scene_type['description']} setting.

    {product_analysis['product_name']} displayed in {scene_type['composition']},

    Focus on {feature['title']}：{feature['description']},

    Text layout:
    - Main heading "{feature['title']}" at upper-left,
      rendered in {platform_style['font']},
      {platform_style['heading_size']}px,
      {platform_style['heading_color']}

    - Supporting captions: {', '.join(feature['visual_keywords'][:3])}

    CRITICAL: Keep the product EXACTLY the same —
    same {product_analysis['visual_features']['main_color']},
    same {product_analysis['visual_features']['pattern']},
    same {feature['visual_keywords'][0] if feature['visual_keywords'] else ''},
    do not modify any design detail.
    """

    return prompt
```

---

## 第三步：场景智能匹配

### 场景选择逻辑

根据卖点类型和商品类别自动匹配场景：

```python
SCENE_MAPPING = {
    # 面料/材质卖点 → 特写场景
    "fabric": {
        "scene": "macro close-up",
        "props": ["cotton plant", "fabric swatch"],
        "lighting": "directional side lighting"
    },

    # 版型/廓形卖点 → 人物/人台场景
    "silhouette": {
        "scene": "bedroom or fitting room",
        "props": ["mirror", "soft bedding"],
        "lighting": "soft ambient lighting"
    },

    # 设计细节卖点 → 生活场景
    "design": {
        "scene": "cafe or garden",
        "props": ["coffee cup", "book", "flowers"],
        "lighting": "natural bright lighting"
    },

    # 季节/氛围卖点 → 季节场景
    "seasonal": {
        "scene": "beach or park",
        "props": season_based_props,
        "lighting": "sunlight"
    }
}

def get_scene_for_feature(feature_type, product_analysis):
    """根据卖点类型获取场景配置"""
    base_scene = SCENE_MAPPING.get(feature_type, SCENE_MAPPING["design"])

    # 根据商品类别调整
    if product_analysis["product_category"] == "连衣裙":
        base_scene["composition"] = "worn by faceless model OR elegantly draped"
    elif product_analysis["product_category"] == "T恤":
        base_scene["composition"] = "flat lay OR on hanger"

    return base_scene
```

---

## 第四步：商品一致性增强

### 强化一致性约束

在所有Prompt中添加更严格的一致性描述：

```python
def build_consistency_constraint(product_analysis):
    """构建商品一致性约束描述"""

    visual_features = product_analysis['visual_features']

    constraints = f"""
    === PRODUCT CONSISTENCY CONSTRAINTS ===

    Visual characteristics that MUST be preserved:
    1. Color scheme: {visual_features['main_color']} with {', '.join(visual_features['secondary_colors'])}
    2. Pattern: {visual_features['pattern']} — exact same pattern, scale, and placement
    3. Neckline: {visual_features['neckline']} — same shape and structure
    4. Silhouette: {visual_features['silhouette']} — same proportions and drape
    5. Hemline: {visual_features['hemline']} — same style and layers
    6. Fabric texture: {visual_features['fabric_texture']} — same visual quality

    CRITICAL RULES:
    - DO NOT alter the clothing design, color, or print pattern
    - DO NOT change the proportions or structural details
    - DO NOT add or remove design elements
    - The product must look like the EXACT same item across all images
    - Maintain identical print placement, scale, and orientation

    If generating model images: ensure the garment looks like
    it's the SAME product worn by different models/poses.
    """

    return constraints
```

---

## Agent工作流程

### 完整的生成流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 用户上传1-3张商品图                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Agent分析商品（视觉能力或脚本）                              │
│    - 检测商品图类型（平铺/挂拍/模特）                            │
│    - 提取视觉特征（颜色、图案、版型、细节）                        │
│    - 推断品类和风格                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 展示分析结果，让用户确认/补充卖点                               │
│    "我发现这是一件黑色碎花吊带连衣裙，主要特点是：                   │
│     • 交叉细吊带V领                                            │
│     • 樱花粉花印花                                             │
│     • 荷叶边鱼尾下摆                                           │
│                                                             │
│     请确认这些卖点是否准确，或补充其他卖点..."                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 用户确认卖点（可编辑）                                       │
│    最终形成结构化的卖点JSON                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. 选择平台和图片类型                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Agent动态生成每个Prompt                                     │
│    for each image_type in selected_types:                     │
│      - 根据商品特征 + 卖点 + 平台风格 → 生成定制Prompt            │
│      - 应用一致性约束                                          │
│      - 智能匹配场景                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. 展示生成的Prompt，用户可编辑                                 │
│    "核心卖点图的Prompt：                                       │
│     [展示完整的Prompt内容]                                     │
│                                                             │
│     是否需要调整？"                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. 调用生图API                                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 关键改进点

### 1. 支持1-3张商品图输入

```python
# 接收多张商品图
input_images = [product_image_1, product_image_2, product_image_3]

# 分析每张图的类型
for image in input_images:
    image_type = detect_image_type(image)  # flat_lay / hanging / model

# 综合多张图的信息
consolidated_analysis = merge_analysis_results(analyses)
```

### 2. 检测商品图类型

```python
def detect_image_type(image):
    """检测商品图的展示类型"""
    # 使用视觉模型判断
    if has_human_figure(image):
        return "model"
    elif is_hanging(image):
        return "hanging"
    else:
        return "flat_lay"

# 根据输入类型调整Prompt
if input_type == "flat_lay":
    composition_prompt = "displayed flat on surface"
elif input_type == "hanging":
    composition_prompt = "hanging on hanger, full body visible"
elif input_type == "model":
    composition_prompt = "worn by model, same pose and framing"
```

### 3. 文案内容动态化

**之前（固定）**：
```
主标题：宽松版型设计
副标题：活动自如无束缚
```

**现在（动态）**：
```
主标题：{根据商品特点生成}
  - 连衣裙 → "灵动鱼尾设计" / "优雅法式浪漫"
  - T恤 → "舒适宽松版型" / "个性印花设计"
  - 裙子 → "高腰显瘦剪裁" / "飘逸A字廓形"

副标题：{基于卖点描述生成}
  - 直接从卖点JSON中提取
  - 或根据卖点关键词组合
```

---

## 实施建议

### 立即执行

1. **更新SKILL.md第二步**
   - 增加商品图类型检测
   - 增加多图支持说明
   - 细化卖点分析维度

2. **修改第四步（Prompt生成）**
   - 从"读取模板"改为"动态生成"
   - 添加Prompt生成示例
   - 说明如何结合商品特征

3. **增强一致性约束**
   - 在所有Prompt中加入详细的一致性描述
   - 强调"禁止修改商品设计"

### 后续优化

4. **创建Prompt生成参考**
   - 提供不同品类的Prompt示例
   - 提供不同卖点的场景匹配
   - 建立Prompt最佳实践

5. **优化用户交互**
   - 智能推测卖点（减少用户输入）
   - Prompt预览和编辑功能
   - 一键应用平台风格
