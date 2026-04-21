# 图像生成供应商 API 配置参考

## 支持的供应商（5个）

| 供应商 | 模型 | 定价 | 适合场景 | 参考图支持 | 国内访问 |
|--------|------|------|---------|-----------|---------|
| OpenAI | dall-e-3 / gpt-image-1.5 | $0.04-0.2/张 | 高质量写实/场景图 | gpt-image ✅ | 需代理 |
| Google Gemini | gemini-3.1-flash-image-preview | $0.03/张 | 高质量写实，细节好 | ✅ 原生 | 需代理 |
| Stability AI | stable-image-core | $0.03/张 | 精准控制，白底图好 | ❌ | 需代理 |
| 千问 | wan2.7-image-pro | ¥0.14/张 | 国内电商场景优化 | ✅ | ✅直连 |
| 豆包（即梦） | doubao-seedream-4-5-251128 | ¥0.12/张 | 中文场景，风格多样 | ✅ | ✅直连 |

---

## OpenAI

**默认模型:** `dall-e-3`（环境变量 `OPENAI_MODEL` 可覆盖为 `gpt-image-1.5`）

**API Endpoints:**
- 纯文生图：`/v1/images/generations`
- 图生图（参考图）：`/v1/images/edits`

**Key获取:** https://platform.openai.com/api-keys

**模型选择与参考图支持：**

| 模型 | 参考图 | 说明 | 推荐场景 |
|------|-------|------|---------|
| `gpt-image-1.5` | ✅ 支持 | 最新 GPT Image，支持 edits，高保真参考图 | **电商套图首选** |
| `gpt-image-1` | ✅ 支持 | 上一代 GPT Image | 成本敏感场景 |
| `gpt-image-1-mini` | ✅ 支持 | GPT Image 经济版 | 大批量生成 |
| `dall-e-3` | ❌ 不支持 | DALL·E 3，仅纯文生图 | 纯文字描述场景 |

**环境变量配置：**
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-image-1.5"  # 推荐：覆盖默认 dall-e-3 以启用参考图
# export OPENAI_BASE_URL="https://your-proxy.com/v1"  # 可选代理
```

**纯文生图（无参考图）：**
```javascript
const response = await fetch("https://api.openai.com/v1/images/generations", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${apiKey}`
  },
  body: JSON.stringify({
    model: "dall-e-3",  // 或 gpt-image-1.5
    prompt: prompt,
    size: "1024x1024",
    quality: "hd",       // "standard" | "hd"
    response_format: "b64_json",
    n: 1
  })
});
const data = await response.json();
const base64 = data.data[0].b64_json;
```

**图生图（有参考图，仅 GPT Image）：**
```javascript
const formData = new FormData();
formData.append("model", "gpt-image-1.5");
formData.append("prompt", prompt);
formData.append("size", "1024x1024");
formData.append("response_format", "b64_json");
formData.append("n", "1");
// 参考图（文件）
formData.append("image", new Blob([imageBytes]), "product.jpg");

const response = await fetch("https://api.openai.com/v1/images/edits", {
  method: "POST",
  headers: { "Authorization": `Bearer ${apiKey}` },
  body: formData
});
const data = await response.json();
const base64 = data.data[0].b64_json;
```

**⚠️ 重要：** 使用 `dall-e-3` 时若提供了参考图，脚本会自动降级为纯文生图并输出警告。如需保留商品外观，请设置 `OPENAI_MODEL=gpt-image-1.5` 或在调用时使用 `--model gpt-image-1.5`。

---

## Google Gemini Imagen 3

**API Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict`
**Key获取:** https://aistudio.google.com/app/apikey

```javascript
const response = await fetch(
  `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key=${apiKey}`,
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      instances: [{ prompt: prompt }],
      parameters: {
        sampleCount: 1,
        aspectRatio: "1:1",      // "1:1" | "9:16" | "16:9" | "3:4" | "4:3"
        safetySetting: "block_only_high",
        personGeneration: "allow_adult"
      }
    })
  }
);
const data = await response.json();
const base64 = data.predictions[0].bytesBase64Encoded;
```

---

## Stability AI Stable Image Core

**API Endpoint:** `https://api.stability.ai/v2beta/stable-image/generate/core`
**Key获取:** https://platform.stability.ai/account/keys

```javascript
const formData = new FormData();
formData.append("prompt", prompt);
formData.append("output_format", "jpeg");
formData.append("aspect_ratio", "1:1");   // "1:1" | "16:9" | "9:16" etc
// formData.append("negative_prompt", "blurry, distorted");

const response = await fetch("https://api.stability.ai/v2beta/stable-image/generate/core", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${apiKey}`,
    "Accept": "application/json"
  },
  body: formData
});
const data = await response.json();
const base64 = data.image;
```

---

## 千问（阿里云 DashScope）

**API Endpoint:** `https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis`
**Key获取:** https://dashscope.console.aliyun.com/
**模型:** `qwen-image-2.0-pro`

```javascript
// Step 1: 提交任务
const submitRes = await fetch(
  "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
      "X-DashScope-Async": "enable"
    },
    body: JSON.stringify({
      model: "qwen-image-2.0-pro",
      input: { prompt: prompt },
      parameters: {
        size: "1024*1024",
        n: 1,
        style: "<auto>"  // "<photography>" | "<anime>" | "<auto>"
      }
    })
  }
);
const { output: { task_id } } = await submitRes.json();

// Step 2: 轮询结果（每2秒查一次，最多等60秒）
for (let i = 0; i < 30; i++) {
  await new Promise(r => setTimeout(r, 2000));
  const pollRes = await fetch(
    `https://dashscope.aliyuncs.com/api/v1/tasks/${task_id}`,
    { headers: { "Authorization": `Bearer ${apiKey}` } }
  );
  const pollData = await pollRes.json();
  if (pollData.output?.task_status === "SUCCEEDED") {
    const imageUrl = pollData.output.results[0].url;
    // 转base64
    const imgBlob = await (await fetch(imageUrl)).blob();
    const base64 = await new Promise(r => {
      const fr = new FileReader();
      fr.onloadend = () => r(fr.result.split(",")[1]);
      fr.readAsDataURL(imgBlob);
    });
    return base64;
  }
  if (pollData.output?.task_status === "FAILED") throw new Error("Task failed");
}
```

---

## 豆包（字节跳动 火山引擎）

**API Endpoint:** `https://ark.cn-beijing.volces.com/api/v3/images/generations`
**Key获取:** https://console.volcengine.com/ark → API Key管理

```javascript
const response = await fetch("https://ark.cn-beijing.volces.com/api/v3/images/generations", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${apiKey}`
  },
  body: JSON.stringify({
    model: "doubao-seedream-3-0-t2i-250415",  // 最新模型
    prompt: prompt,
    size: "1024x1024",
    response_format: "b64_json",
    n: 1
  })
});
const data = await response.json();
const base64 = data.data[0].b64_json;
```

---

## Canvas 文案叠加规范

每种图类型对应的文案叠加坐标（以1024×1024为基准，使用比例值）：

| 图类型 | 文字位置 | 颜色风格 |
|--------|---------|---------|
| 白底主图 | 无叠加 | — |
| 核心卖点图 | 右侧（0.52-0.95x） | 深色文字（#222） |
| 卖点图 | 左上+左下 | 深色或白色阴影 |
| 材质图 | 右上+右中+右下 | 深色文字 |
| 场景展示图 | 左上+左下 | 白色+阴影 |
| 模特展示图 | 无叠加 | — |
| 多场景拼图 | 顶部居中+底部两侧 | 白色+阴影 |

### 字体规范
- 主标题：字体大小 = canvas宽度 × 0.03，fontWeight: 700
- 副标题：字体大小 = canvas宽度 × 0.022，fontWeight: 600
- 字体族：`"Helvetica Neue", "PingFang SC", "Microsoft YaHei", Arial, sans-serif`
- 阴影（场景/模特图）：`shadowColor: rgba(0,0,0,0.5), shadowBlur: 8`
