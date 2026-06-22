---
name: zm-skills-manager
description: Use when users want to find, inspect, download, install, update, or upload ZM App Store Skills from an agent or IDE without opening the Hub web UI.
---
<!-- light-skill-version-check:start -->
## Version Check

Before using this Skill, run:

```bash
python3 scripts/light_skill_check_update.py --brief
```

If the command prints `UPDATE_AVAILABLE`, tell the user a newer Skill package is available and provide the download URL. If the user explicitly asks to upgrade this Skill, run:

```bash
python3 scripts/light_skill_check_update.py --force --upgrade --brief
```

For details, read `docs/light-skill-version-check.md`.
<!-- light-skill-version-check:end -->

# ZM Skills Manager

Use this Skill when the user asks to find, download, install, update, or upload Skills.

Before using this Skill, run the standard version check if present:

```bash
python3 scripts/light_skill_check_update.py --brief
```

Use `scripts/skills_manager.py` for all operations:

```bash
python3 scripts/skills_manager.py find "data api"
python3 scripts/skills_manager.py info zmdata-data-api
python3 scripts/skills_manager.py install zmdata-data-api --target codex
python3 scripts/skills_manager.py update --all --target codex
python3 scripts/skills_manager.py upload ./my-skill --name "My Skill" --owner "Team"
```

If multiple target IDE skills directories exist and the user did not specify `--target` or `--dest`, ask which target to use. User-uploaded Skills are available immediately and are marked with `sourceKind=uploaded` plus the `分享` tag.

