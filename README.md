# ecommerce-image-suite

面向电商商品图生产场景的图片套图 Skill。仓库提供一套从商品图分析、卖点提炼、Prompt 组织到成图输出的脚本与配置，适合用在淘宝、京东、拼多多、抖音等国内平台，以及独立站、Amazon 等跨境场景。

当前仓库内已经附带多组测试样例，集中放在 example 目录。本文档把这些样例直接加载出来，便于开源展示、效果对比和后续维护。

## 项目定位

这个仓库主要解决三件事：

1. 把商品原图转成结构化商品信息。
2. 按平台和图型要求生成标准化电商套图。
3. 为后续文案、详情页 HTML、视频生成提供统一输入。

标准输出图型覆盖：

| 图型 | 说明 |
| --- | --- |
| 白底主图 | 商品全貌展示，适合作为主图或首图 |
| 核心卖点图 | 用于突出 2 到 4 个核心卖点 |
| 卖点图 | 单一卖点深挖 |
| 材质图 | 放大面料、做工、纹理等细节 |
| 场景展示图 | 放到使用场景中展示代入感 |
| 模特展示图 | 服饰类常用，补足上身或穿搭效果 |
| 多场景拼图 | 同一商品在多个场景中的组合图 |
| 电商详情图 | 长图详情页物料 |
| 三角度拼图 | 正面、侧面、背面等角度整合 |

## 仓库结构

| 路径 | 说明 |
| --- | --- |
| SKILL.md | Skill 定义、对话流程、约束与执行规则 |
| scripts/analyze.py | 商品图视觉分析，输出结构化商品信息 |
| scripts/generate.py | 生成套图主脚本 |
| scripts/check_providers.py | 检测图像供应商配置 |
| scripts/generate_video.py | 基于套图生成视频 |
| references/ | Prompt、平台、模型、供应商等参考文档 |
| example/ | 样例图片与测试数据 |
| assets/ | 模型配置与资源文件 |

## 运行前提

- Python 3.8+
- 已安装 openai、requests 等依赖
- 至少配置一个图像生成供应商的 API Key

仓库内置供应商检测脚本：

```bash
python3 scripts/check_providers.py
```

当前脚本支持的供应商包括：

| 供应商 | 环境变量 | 备注 |
| --- | --- | --- |
| 阿里云通义 | DASHSCOPE_API_KEY | 国内直连 |
| 字节豆包 | ARK_API_KEY | 国内直连 |
| OpenAI | OPENAI_API_KEY | 通常需要代理 |
| Google Gemini | GEMINI_API_KEY | 通常需要代理 |
| Stability AI | STABILITY_API_KEY | 通常需要代理 |

### 环境变量配置

#### macOS / Linux

临时生效可以直接在当前终端执行：

```bash
export DASHSCOPE_API_KEY="你的密钥"
export ARK_API_KEY="你的密钥"
```

如果希望长期生效，可以写入 shell 配置文件后再执行 source：

```bash
echo 'export DASHSCOPE_API_KEY="你的密钥"' >> ~/.zshrc
echo 'export ARK_API_KEY="你的密钥"' >> ~/.zshrc
source ~/.zshrc
```

如果你使用的是 bash，则改写到 ~/.bashrc 或 ~/.bash_profile：

```bash
echo 'export DASHSCOPE_API_KEY="你的密钥"' >> ~/.bashrc
echo 'export ARK_API_KEY="你的密钥"' >> ~/.bashrc
source ~/.bashrc
```

#### Windows

可以在系统界面的环境变量设置中新增对应变量，也可以在命令行里设置。

PowerShell 当前会话生效：

```powershell
$env:DASHSCOPE_API_KEY="你的密钥"
$env:ARK_API_KEY="你的密钥"
```

PowerShell 写入用户级环境变量：

```powershell
[System.Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "你的密钥", "User")
[System.Environment]::SetEnvironmentVariable("ARK_API_KEY", "你的密钥", "User")
```

CMD 用户级环境变量：

```cmd
setx DASHSCOPE_API_KEY "你的密钥"
setx ARK_API_KEY "你的密钥"
```

设置完成后，重新打开终端，再执行下面的检测命令确认是否生效：

```bash
python3 scripts/check_providers.py
```

## 快速使用

先分析商品图：

```bash
python3 scripts/analyze.py ./product.jpg --output ./output/001/product.json
```

再根据分析结果生成套图：

```bash
python3 scripts/generate.py \
	--product "$(cat ./output/001/product.json)" \
	--provider tongyi \
	--lang zh \
	--types white_bg,key_features,selling_pt,material,lifestyle,model,multi_scene \
	--output-dir ./output/001
```

如果只是检查环境是否可用，优先执行：

```bash
python3 scripts/check_providers.py
```

## 样例摘要

仓库当前包含服饰、电器、客户端测试和视频智能文搜等多组样例，完整案例已拆分到独立文档，方便首页保持简洁。

| 类型 | 数量 | 说明 |
| --- | ---: | --- |
| 服饰类商品案例 | 5 组 | 男装、女装、童装、多模型输出对比 |
| 电器类商品案例 | 1 组 | 紫黑款桶式吸尘器 |
| 客户端链路截图 | 18 张 | 从会话引导到结果回传 |
| 视频智能文搜项目截图 | 3 张 | 真实项目界面留档 |

代表性展示：

| 男装 | 女装 | 电器 |
| --- | --- | --- |
| ![男装白底主图](./example/男装/白底主图.jpg) | ![女装005白底主图](./example/女装/005/白底主图.jpg) | ![电器白底主图](./example/电器/白底主图.jpg) |

完整样例、文件清单与全部展示图见 EXAMPLES.md。

## 商业合作

如果你希望基于这套能力做定制化项目，可以通过邮箱联系：wanzij177@163.com。

支持的合作方向包括电商套图生产、商品分析与文案、视频智能文搜、多模态业务后台等。详细商务说明见 BUSINESS.md。

## 当前状态说明

- 女装/003 目前没有 product.json，说明这组样例更偏结果留档，而不是完整流程回放。
- 仓库当前未附带独立的 LICENSE 文件。如果准备对外开源，建议补充许可协议、依赖安装说明和最小可运行示例。

## 延伸文档

1. [样例展示](./EXAMPLES.md)
2. [商务合作](./BUSINESS.md)


## 友情链接

[![LINUXDO](https://img.shields.io/badge/%E7%A4%BE%E5%8C%BA-LINUXDO-0086c9?style=for-the-badge&labelColor=555555)](https://linux.do)