# fal-setup Skill

Configure fal.ai API key and initialize the skill system.

## Usage

```
/fal-setup
```

## What it does

1. Prompts user for fal.ai API key
2. Validates the key by testing API connection
3. Saves key securely to `~/.config/fal-skill/.env`
4. Tests model discovery
5. Creates initial model cache

## Instructions

When this skill is invoked:

1. **Check for existing configuration**:
   ```bash
   ls -la ~/.config/fal-skill/.env 2>/dev/null
   ```

2. **If config exists**, ask user:
   > "API key already configured. Would you like to update it? (yes/no)"

3. **If no config or user wants to update**:
   - Display instructions:
   ```
   Let me help you configure fal.ai integration.

   Step 1: Get your API key
   Visit: https://fal.ai/dashboard/keys
   Create a new API key and paste it here.

   (Your API key should start with something like "abc123-...")
   ```

4. **Get API key from user** using AskUserQuestion tool:
   - Question: "Please paste your fal.ai API key:"
   - Single text input
   - Store in variable: `api_key`

5. **Create config directory and save key**:
   ```bash
   mkdir -p ~/.config/fal-skill
   echo "FAL_KEY=${api_key}" > ~/.config/fal-skill/.env
   chmod 600 ~/.config/fal-skill/.env
   ```

6. **Validate the key**:
   ```bash
   python3 scripts/fal_api.py validate
   ```

7. **If validation succeeds**:
   - Display: "✓ Valid API key configured successfully!"
   - Initialize model cache:
   ```bash
   python3 scripts/fal_api.py discover > /tmp/fal_initial_discovery.json
   wc -l /tmp/fal_initial_discovery.json
   ```
   - Display: "✓ Discovered X models from fal.ai"

8. **If validation fails**:
   - Display: "✗ API key validation failed. Please check your key and try again."
   - Remove invalid config:
   ```bash
   rm ~/.config/fal-skill/.env
   ```
   - Suggest: "Get a valid key from https://fal.ai/dashboard/keys"

9. **Show next steps**:
   ```
   Configuration complete! 🎉

   Try these commands:
   - /fal-generate "a wizard cat"          # Generate an image
   - /fal-generate-image "sunset"          # Image generation
   - /fal-remove-bg [image]                # Remove background

   Model registry location: models/curated.yaml
   Cache location: ~/.config/fal-skill/cache/
   ```

## Error Handling

- **No internet connection**: "Cannot reach fal.ai API. Please check your internet connection."
- **Invalid API key format**: "API key format looks incorrect. It should be a long alphanumeric string."
- **Permission errors**: "Cannot write to ~/.config/fal-skill/. Please check file permissions."

## Security Notes

- API key stored in `~/.config/fal-skill/.env` with `chmod 600` (user-only access)
- Never log or display the full API key
- Key is never committed to git (in .gitignore)
