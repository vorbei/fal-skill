# 可用的fal.ai模型

## 图像编辑 (Fibo Edit - Bria)

### 正确的endpoint: `bria/fibo-edit/*`

**5个核心操作**:
1. `bria/fibo-edit/colorize` - 为黑白图像添加颜色
2. `bria/fibo-edit/relight` - 改变光照条件
3. `bria/fibo-edit/reseason` - 改变季节
4. `bria/fibo-edit/restore` - 修复旧/损坏照片
5. `bria/fibo-edit/restyle` - 应用艺术风格

**对象编辑**:
6. `bria/fibo-edit/add_object_by_text` - 通过文本添加对象
7. `bria/fibo-edit/erase_by_text` - 通过文本擦除对象
8. `bria/fibo-edit/replace_object_by_text` - 通过文本替换对象

**其他**:
9. `bria/fibo-edit/edit` - 通用编辑
10. `bria/fibo-edit/edit/structured_instruction` - 结构化指令编辑
11. `bria/fibo-edit/blend` - 混合
12. `bria/fibo-edit/rewrite_text` - 重写文本
13. `bria/fibo-edit/sketch_to_colored_image` - 草图上色

## 其他编辑模型

### 重新打光
- `fal-ai/lightx/relight` - LightX重新打光
- `fal-ai/image-apps-v2/relighting` - 图像应用v2重新打光

### 风格化
- `decart/lucy-restyle` - Lucy风格化

### 背景移除
- `fal-ai/bria/background/remove` - Bria背景移除

### Inpaint（修复）
- `fal-ai/z-image/turbo/inpaint` - Z-Image快速修复
- `fal-ai/image-apps-v2/outpaint` - 图像应用v2外部绘制

### Flux编辑
- `fal-ai/flux-2/edit` - Flux 2编辑
- `fal-ai/flux-2-pro/edit` - Flux 2 Pro编辑
- `fal-ai/flux-2/lora/edit` - Flux 2 LoRA编辑

## 图像放大

1. `fal-ai/clarity-upscaler` - Clarity放大器
2. `clarityai/crystal-upscaler` - Crystal放大器（通用）
3. `clarityai/crystal-video-upscaler` - Crystal视频放大器
4. `fal-ai/flashvsr/upscale/video` - FlashVSR视频放大
5. `fal-ai/flux-vision-upscaler` - Flux Vision放大器

## 视频生成

### Kling Video
- `fal-ai/kling-video/v1/standard/text-to-video` - 标准文本转视频
- `fal-ai/kling-video/v1/pro/text-to-video` - Pro文本转视频
- `fal-ai/kling-video/v1/standard/image-to-video` - 标准图像转视频
- `fal-ai/kling-video/v1/pro/image-to-video` - Pro图像转视频

### 其他视频模型
- `fal-ai/wan-pro/image-to-video` - WAN Pro图像转视频
- `fal-ai/veo2/image-to-video` - Veo2图像转视频
- `fal-ai/wan-effects` - WAN效果

## 修复建议

### models/curated.yaml需要更新:

```yaml
image-editing:
  - endpoint_id: bria/fibo-edit/colorize  # 不是 fal-ai/fibo-edit/colorize
  - endpoint_id: bria/fibo-edit/relight
  - endpoint_id: bria/fibo-edit/reseason
  - endpoint_id: bria/fibo-edit/restore
  - endpoint_id: bria/fibo-edit/restyle
```

### 需要测试的模型:
1. ✅ `bria/fibo-edit/colorize` - 正在测试
2. `bria/fibo-edit/relight`
3. `fal-ai/bria/background/remove` - 替代当前的background removal
4. `clarityai/crystal-upscaler` - 替代或补充当前upscaler
