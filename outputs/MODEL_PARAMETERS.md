# Model Parameter Reference
Generated from 13 model schemas
---
## bria/fibo-edit/colorize
**Parameters**: 2 total, 2 required

### Required Parameters
- **`color`** (`string`): Select the color palette or aesthetic for the output image
- **`image_url`** (`string`): The source image.

---

## bria/fibo-edit/relight
**Parameters**: 3 total, 3 required

### Required Parameters
- **`light_type`** (`string`): The quality/style/time of day.
- **`light_direction`** (`string | null`): Where the light comes from.
- **`image_url`** (`string`): The source image.

---

## bria/fibo-edit/reseason
**Parameters**: 2 total, 2 required

### Required Parameters
- **`season`** (`string`): The desired season.
- **`image_url`** (`string`): The source image.

---

## bria/fibo-edit/restore
**Parameters**: 1 total, 1 required

### Required Parameters
- **`image_url`** (`string`): The source image.

---

## bria/fibo-edit/restyle
**Parameters**: 2 total, 2 required

### Required Parameters
- **`style`** (`string`): Select the desired artistic style for the output image.
- **`image_url`** (`string`): The source image.

---

## clarityai/crystal-upscaler
**Parameters**: 3 total, 1 required

### Required Parameters
- **`image_url`** (`string`): URL to the input image

### Optional Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `creativity` | number (0-10) | `0` | Creativity level for upscaling |
| `scale_factor` | number (1-200) | `2` | Scale factor |

---

## fal-ai/birefnet/v2
**Parameters**: 7 total, 1 required

### Required Parameters
- **`image_url`** (`string`): URL of the image to remove background from

### Optional Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `operating_resolution` | string | `1024x1024` | The resolution to operate on. The higher the resolution, the more accurate the output will be for hi... |
| `output_format` | string | `png` | The format of the output image |
| `model` | string | `General Use (Light)` | 
            Model to use for background removal.
            The 'General Use (Light)' model is the... |
| `sync_mode` | boolean | `False` | If `True`, the media will be returned as a data URI and the output data won't be available in the re... |
| `output_mask` | boolean | `False` | Whether to output the mask used to remove the background |
| `refine_foreground` | boolean | `True` | Whether to refine the foreground using the estimated mask |

---

## fal-ai/clarity-upscaler
**Parameters**: 10 total, 1 required

### Required Parameters
- **`image_url`** (`string`): The URL of the image to upscale.

### Optional Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | `masterpiece, best quality, highres` | The prompt to use for generating the image. Be as descriptive as possible for best results. |
| `resemblance` | number (0-1) | `0.6` | 
            The resemblance of the upscaled image to the original image. The higher the resemblance... |
| `creativity` | number (0-1) | `0.35` | 
            The creativity of the model. The higher the creativity, the more the model will deviate... |
| `upscale_factor` | number (1-4) | `2` | The upscale factor |
| `guidance_scale` | number (0-20) | `4` | 
            The CFG (Classifier Free Guidance) scale is a measure of how close you want
           ... |
| `num_inference_steps` | integer (4-50) | `18` | The number of inference steps to perform. |
| `seed` | integer | null | - | 
            The same seed and the same prompt given to the same version of Stable Diffusion
       ... |
| `negative_prompt` | string | `(worst quality, low quality, normal quality:2)` | The negative prompt to use. Use it to address details that you don't want in the image. |
| `enable_safety_checker` | boolean | `True` | If set to false, the safety checker will be disabled. |

---

## fal-ai/flux-pro
**Parameters**: 10 total, 1 required

### Required Parameters
- **`prompt`** (`string`): The prompt to generate an image from.

### Optional Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_images` | integer (1-4) | `1` | The number of images to generate. |
| `image_size` | ? | string | `landscape_4_3` | The size of the generated image. |
| `output_format` | string | `jpeg` | The format of the generated image. |
| `sync_mode` | boolean | `False` | If `True`, the media will be returned as a data URI and the output data won't be available in the re... |
| `safety_tolerance` | string | `2` | The safety tolerance level for the generated image. 1 being the most strict and 5 being the most per... |
| `guidance_scale` | number (1-20) | `3.5` | 
            The CFG (Classifier Free Guidance) scale is a measure of how close you want
           ... |
| `num_inference_steps` | integer (1-50) | `28` | The number of inference steps to perform. |
| `seed` | integer | - | 
            The same seed and the same prompt given to the same version of the model
            wi... |
| `enhance_prompt` | boolean | `False` | Whether to enhance the prompt for better results. |

---

## fal-ai/flux/dev
**Parameters**: 10 total, 1 required

### Required Parameters
- **`prompt`** (`string`): The prompt to generate an image from.

### Optional Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_images` | integer (1-4) | `1` | The number of images to generate. |
| `image_size` | ? | string | `landscape_4_3` | The size of the generated image. |
| `acceleration` | string | `none` | The speed of the generation. The higher the speed, the faster the generation. |
| `output_format` | string | `jpeg` | The format of the generated image. |
| `sync_mode` | boolean | `False` | If `True`, the media will be returned as a data URI and the output data won't be available in the re... |
| `enable_safety_checker` | boolean | `True` | If set to true, the safety checker will be enabled. |
| `seed` | integer | null | - | 
        The same seed and the same prompt given to the same version of the model
        will outpu... |
| `guidance_scale` | number (1-20) | `3.5` | 
        The CFG (Classifier Free Guidance) scale is a measure of how close you want
        the mod... |
| `num_inference_steps` | integer (1-50) | `28` | The number of inference steps to perform. |

---

## fal-ai/kling-video/v1_standard_image-to-video
**Parameters**: 8 total, 2 required

### Required Parameters
- **`prompt`** (`string`): The prompt for the video
- **`image_url`** (`string`): URL of the image to be used for the video

### Optional Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `duration` | string | `5` | The duration of the generated video in seconds |
| `negative_prompt` | string | `blur, distort, and low quality` |  |
| `static_mask_url` | string | - | URL of the image for Static Brush Application Area (Mask image created by users using the motion bru... |
| `dynamic_masks` | array<DynamicMask> | - | List of dynamic masks |
| `tail_image_url` | string | - | URL of the image to be used for the end of the video |
| `cfg_scale` | number (0-1) | `0.5` | 
            The CFG (Classifier Free Guidance) scale is a measure of how close you want
           ... |

---

## fal-ai/kling-video/v1_standard_text-to-video
**Parameters**: 7 total, 1 required

### Required Parameters
- **`prompt`** (`string`)

### Optional Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `aspect_ratio` | string | `16:9` | The aspect ratio of the generated video frame |
| `advanced_camera_control` |  | - | Advanced Camera control parameters |
| `cfg_scale` | number (0-1) | `0.5` | 
            The CFG (Classifier Free Guidance) scale is a measure of how close you want
           ... |
| `duration` | string | `5` | The duration of the generated video in seconds |
| `negative_prompt` | string | `blur, distort, and low quality` |  |
| `camera_control` | string | - | Camera control parameters |

---

## fal-ai/z-image/base
**Parameters**: 11 total, 1 required

### Required Parameters
- **`prompt`** (`string`): The prompt to generate an image from.

### Optional Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_images` | integer (1-4) | `1` | The number of images to generate. |
| `image_size` | ? | string | `landscape_4_3` | The size of the generated image. |
| `acceleration` | string | `regular` | The acceleration level to use. |
| `output_format` | string | `png` | The format of the generated image. |
| `sync_mode` | boolean | `False` | If `True`, the media will be returned as a data URI and the output data won't be available in the re... |
| `guidance_scale` | number (1-20) | `4` | The guidance scale to use for the image generation. |
| `num_inference_steps` | integer (1-50) | `28` | The number of inference steps to perform. |
| `enable_safety_checker` | boolean | `True` | If set to true, the safety checker will be enabled. |
| `negative_prompt` | string | `` | The negative prompt to use for the image generation. |
| `seed` | integer | - | 
            The same seed and the same prompt given to the same version of the model
            wi... |

---

