---
name: custom-gpt-image-2
description: Generate images through the user's custom OpenAI-compatible image endpoint at the configured base URL using gpt-image-2. Use when the user explicitly asks to use the custom gpt-image-2 endpoint, custom image API, private image gateway, or wants generation through that configured service. This skill is the generic backend capability and should not impose any specific poster style by itself.
---

# Custom GPT Image 2

Use this skill to generate raster images with the user's custom OpenAI-compatible image endpoint.

This skill is intentionally style-agnostic. It provides the transport and generation backend, not a default visual style.

If another specialized skill exists for a specific poster style, layout, or brand system, that specialized skill should own the prompt design, while this skill only provides the configured image generation path.

## Quick Start

Run the bundled script:

```bash
python "$HOME/.codex/skills/custom-gpt-image-2/scripts/generate_image.py" \
  --prompt "A hand-drawn sketchnote poster about AI research workflows" \
  --out output/imagegen/example.png \
  --size 1024x1536 \
  --quality high
```

For long prompts, write a prompt file and use `--prompt-file`.

## Configuration

The script reads private config from:

```text
$HOME/.config/codex-custom-gpt-image-2/config.json
```

Expected fields:

```json
{
  "base_url": "http://host:port",
  "api_key": "sk-...",
  "model": "gpt-image-2"
}
```

Do not print the API key. Do not write the key into project files.

## Output Handling

- Save project-bound final images under the current workspace, usually `output/imagegen/<topic>/`.
- Use PNG by default.
- When the request includes visible text, write the prompt so gpt-image-2 generates the image and the requested text together in a single pass.
- Do not plan a separate local text-overlay step unless the user explicitly asks for post-processing after generation.
- After generation, inspect the image when visual quality matters.

## Script Notes

The script calls:

```text
POST {base_url}/v1/images/generations
```

It supports image responses as `b64_json` or temporary `url`.
