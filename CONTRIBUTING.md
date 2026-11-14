# Contributing

## Add a skill to an existing plugin

1. Create `plugins/<plugin>/skills/<skill-name>/SKILL.md` with front matter:

   ```markdown
   ---
   name: <skill-name>
   description: What it does and when to use it (this text decides when Claude triggers it).
   ---
   ```

2. Put long templates and checklists in `references/` and helper code in `scripts/`
   next to `SKILL.md`; refer to them from `SKILL.md` so they load only when needed.
   Reference scripts as `${CLAUDE_PLUGIN_ROOT}/skills/<skill-name>/scripts/...`.
3. Bump `version` in the plugin's `.claude-plugin/plugin.json` **and** its entry in
   `.claude-plugin/marketplace.json` (they must match).

## Add a new plugin

1. Create `plugins/<plugin-name>/` with:
   - `.claude-plugin/plugin.json` (`name`, `version`, `description`, `author`, `license`, …)
   - `README.md`
   - `skills/`, and optionally `commands/`, `agents/`, `hooks/`
2. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json` with
   `"source": "./plugins/<plugin-name>"`.
3. Update the plugin table in the root `README.md`.

## Validate and test locally

```bash
claude plugin validate . --strict                                  # marketplace
claude plugin validate plugins/<plugin> --strict --profile directory   # plugin, directory-ready

# Try it without publishing:
claude plugin marketplace add ./
claude plugin install <plugin>@research-stack
```

CI runs the same validation on every push and pull request.

## Release

```bash
claude plugin tag plugins/<plugin>   # creates <plugin>--v<version> after checking versions agree
git push --follow-tags
```

Users get the update with `claude plugin marketplace update research-stack`.
