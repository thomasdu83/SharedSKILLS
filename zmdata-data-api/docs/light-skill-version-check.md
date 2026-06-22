# Light Skill Version Check

Run this command before using the Skill:

```bash
python3 scripts/light_skill_check_update.py --brief
```

If the command prints `UPDATE_AVAILABLE`, tell the user a newer Skill package is available and provide the download URL.

If the command prints `UP_TO_DATE`, continue using the Skill.

If the command prints `SKIPPED_RECENTLY`, continue using the Skill. The checker already contacted the version service within the configured interval.

If the command prints `UPDATE_CHECK_UNAVAILABLE`, continue using the Skill and mention that the update check could not reach the version service.

Default frequency is once per day. Use this command when the user explicitly asks to check now:

```bash
python3 scripts/light_skill_check_update.py --force --brief
```

When the user explicitly asks to upgrade this Skill, run:

```bash
python3 scripts/light_skill_check_update.py --force --upgrade --brief
```

The upgrade command downloads the latest package from the `downloadUrl`, validates the zip layout and release metadata, backs up the current Skill directory, then replaces it in place. Backups are stored next to the Skill under `.light-skill-backups/<skill-id>/`.

If the upgrade fails, the script leaves the current Skill in place or restores it from the backup. Local edits are not merged into the new version; only runtime cache files such as `.light-skill-update-cache.json` are preserved.

Older downloaded Skill packages do not include the upgrade command. Download the Skill again from the Hub to get automatic upgrade support.
