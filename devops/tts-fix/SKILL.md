---
name: tts-fix
description:凡涉 TTS 语音配置、语言匹配、audio 返回异常时，即当加载。
---

# TTS 语音匹配之道

## 症结
`text_to_speech` 返「No audio was received」，因文本语言与配置语音不符

## 解法

改 `~/.hermes/config.yaml` 中 `tts.edge.voice`：

| 文本语言 | 语音 |
|:---|:---|
| 中文 | zh-CN-XiaoxiaoNeural |
| 英文 | en-US-AriaNeural |

## 验证

```python
import asyncio, edge_tts
async def test():
    c = edge_tts.Communicate("测试", "zh-CN-XiaoxiaoNeural")
    await c.save("/tmp/t.mp3")
asyncio.run(test())
```

---

## PipeWire 音频播放修复

### 症状
TTS 已生成音频文件，但扬声器无声。君系统无 PulseAudio/ALSA 播放器

### 诊断
```bash
which pw-play # PipeWire 原生播放器
which play # sox
which ffplay # ffmpeg
which aplay # alsa-utils
```

### 根因
`play_audio_file()`（`tools/voice_mode.py`）在 Linux 上仅有 `aplay`（ALSA）、`ffplay`（默认 ALSA 输出），均无法作用于 PipeWire

### 修复
在 `tools/voice_mode.py` 的 `play_audio_file()` 中，Linux 播放器优先级调整为：

```python
# Linux 优先顺序
players.append(["pw-play", file_path]) # PipeWire 原生 ← 新增
players.append(["play", file_path]) # sox (可设 AUDIODEV=pipewire)
players.append(["aplay", "-q", file_path]) # ALSA fallback
players.append(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path])
```

`pw-play` 为 PipeWire 原生播放器，无需额外配置，优先于所有 fallback

### 验声
```bash
pw-play /tmp/test_tts.ogg # 直接播放，测 PipeWire 输出
```
