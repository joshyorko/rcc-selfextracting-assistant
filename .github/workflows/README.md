# GitHub Actions Workflows

This directory contains CI/CD workflows for building and distributing the self-extracting RCC assistant.

## Available Workflows

### 1. Build Self-Extracting RCC Assistant (`build-assistant.yml`)

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests
- Git tags (e.g., `v1.0.0`)
- Manual dispatch with custom options

**What it does:**
1. Runs test suite to validate builder functionality
2. Builds self-extracting assistants for multiple platforms:
   - Ubuntu (Linux)
   - Windows
   - macOS
3. Tests each Python version: 3.10, 3.11, 3.12
4. Downloads RCC from official sources
5. Clones the robot repository (default: fetch-repos-bot)
6. Pre-builds Holotree for offline execution
7. Creates self-extracting `.py` files
8. Builds Windows `.exe` using PyInstaller
9. Uploads all artifacts to GitHub Actions
10. Creates GitHub Releases for tagged versions

**Artifacts produced:**
- `assistant-ubuntu-latest-py3.10.py`
- `assistant-ubuntu-latest-py3.11.py`
- `assistant-ubuntu-latest-py3.12.py`
- `assistant-windows-latest-py3.10.py`
- `assistant-windows-latest-py3.11.py`
- `assistant-windows-latest-py3.12.py`
- `assistant-macos-latest-py3.10.py`
- `assistant-macos-latest-py3.11.py`
- `assistant-macos-latest-py3.12.py`
- `RccAssistant.exe` (Windows executable)

### 2. Manual Build (`manual-build.yml`)

**Triggers:**
- Manual dispatch only (workflow_dispatch)

**Configuration options:**
- `robot_repo`: URL of the robot repository to bundle
- `robot_branch`: Branch or tag to use (default: main)
- `include_holotree`: Whether to pre-build Holotree (default: true)
- `output_name`: Name for the output file (default: assistant)

**What it does:**
1. Downloads RCC
2. Clones your specified robot repository
3. Optionally builds Holotree for offline mode
4. Creates self-extracting assistant
5. Validates the output
6. Uploads artifact

**Artifacts produced:**
- `<output_name>.py` (your custom assistant)

## Usage

### Automatic Build on Push

Simply push to `main`, `master`, or `develop`:

```bash
git add .
git commit -m "Update robot"
git push origin main
```

The workflow will automatically build assistants for all platforms.

### Manual Build with Custom Robot

1. Go to **Actions** tab in GitHub
2. Select **Manual Build** workflow
3. Click **Run workflow**
4. Fill in the parameters:
   - Robot repository URL: `https://github.com/yourorg/your-robot`
   - Robot branch: `main` (or any branch/tag)
   - Include Holotree: ✅ (for offline mode)
   - Output name: `my-custom-assistant`
5. Click **Run workflow**

Wait for the build to complete, then download from **Artifacts** section.

### Creating a Release

To create a GitHub Release with all platform binaries:

```bash
# Tag your commit
git tag v1.0.0
git push origin v1.0.0
```

The workflow will automatically:
1. Build all platform assistants
2. Build Windows .exe
3. Create a GitHub Release
4. Attach all artifacts as release assets

## Downloading Artifacts

### From Actions Tab

1. Go to **Actions** tab
2. Click on the workflow run
3. Scroll to **Artifacts** section
4. Click to download any artifact

### From Releases (for tagged builds)

1. Go to **Releases** section
2. Find your version (e.g., v1.0.0)
3. Download the platform-specific ZIP file

## Platform-Specific Notes

### Windows

- Downloads `rcc.exe` from official Robocorp releases
- Builds additional `.exe` bundle using PyInstaller
- Output location: `%LOCALAPPDATA%\MyRccAssistant`

### Linux

- Downloads `rcc` Linux binary
- Compatible with most Linux distributions
- Output location: `~/.local/share/MyRccAssistant`

### macOS

- Downloads `rcc` macOS binary
- Compatible with macOS 10.15+
- Output location: `~/.local/share/MyRccAssistant`

## Customizing the Workflows

### Using Your Custom RCC Fork

Edit `build-assistant.yml` and replace the RCC download step:

```yaml
- name: Download RCC
  run: |
    # Download from your fork instead
    curl -L https://github.com/yourorg/rcc/releases/latest/download/rcc.exe -o rcc.exe
    chmod +x rcc.exe
```

### Changing Default Robot

Edit the default robot repository in both workflows:

```yaml
robot_repo:
  description: 'Robot repository URL'
  required: false
  default: 'https://github.com/yourorg/your-robot'  # Change this
```

### Adjusting Retention

Artifacts are kept for 90 days by default. To change:

```yaml
- name: Upload assistant artifact
  uses: actions/upload-artifact@v4
  with:
    retention-days: 30  # Change this
```

## Troubleshooting

### Build fails: "RCC executable not found"

The RCC download step may have failed. Check:
- Robocorp download URLs are accessible
- No rate limiting from GitHub Actions
- Correct platform detection

### Build fails: "robot.yaml not found"

The robot repository structure is incorrect. Ensure:
- Repository has a `robot.yaml` at the root or in a subdirectory
- Branch/tag exists
- Repository is public or you have access

### Holotree build fails

This is often non-critical. The assistant will still work but will need internet on first run.

### Artifact too small

The payload wasn't included. Check:
- Builder script completed successfully
- Payload marker validation passed
- Temporary directory had enough space

## Security Considerations

### Secrets

If your robot requires secrets (API keys, credentials):

1. Add them to GitHub repository secrets
2. Pass them as environment variables:

```yaml
- name: Build self-extracting assistant
  env:
    MY_API_KEY: ${{ secrets.MY_API_KEY }}
  run: |
    # Your build command
```

**⚠️ Warning:** Secrets will be embedded in the assistant. Only do this for trusted distribution.

### Private Repositories

For private robot repositories:

1. Create a Personal Access Token (PAT) with `repo` scope
2. Add it as a secret: `ROBOT_REPO_TOKEN`
3. Use it in clone:

```yaml
- name: Clone robot repository
  run: |
    git clone https://x-access-token:${{ secrets.ROBOT_REPO_TOKEN }}@github.com/yourorg/private-robot.git robot-project
```

## Examples

### Example 1: Build on Every Push

```yaml
# Just push your changes
git add .
git commit -m "Update assistant"
git push
```

### Example 2: Build Specific Version

```yaml
# Tag a release
git tag v2.0.0
git push origin v2.0.0

# Workflow creates GitHub Release with binaries
```

### Example 3: Build with Custom Robot

In GitHub UI:
1. Actions → Manual Build → Run workflow
2. Robot URL: `https://github.com/joshyorko/my-special-robot`
3. Branch: `feature-branch`
4. Include Holotree: Yes
5. Output name: `special-assistant`

### Example 4: Quick Test Build

```yaml
# Use workflow_dispatch to build without pushing
gh workflow run manual-build.yml \
  -f robot_repo=https://github.com/joshyorko/test-robot \
  -f output_name=test-assistant \
  -f include_holotree=false
```

## Integration with CI/CD

### As Part of a Pipeline

```yaml
# In your robot repository
name: Build and Release

on:
  release:
    types: [published]

jobs:
  build-assistant:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger assistant build
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.PAT }}
          repository: yourorg/rcc-selfextracting-assistant
          event-type: build-robot
          client-payload: '{"robot_repo": "${{ github.repository }}", "version": "${{ github.ref_name }}"}'
```

## Performance Tips

1. **Holotree caching**: Consider caching RCC Holotree between runs
2. **Parallel builds**: Matrix strategy builds all platforms in parallel
3. **Artifact compression**: Artifacts are automatically compressed by GitHub

## Support

For issues with workflows:
1. Check workflow logs in Actions tab
2. Review the [GitHub Actions documentation](https://docs.github.com/en/actions)
3. Open an issue in this repository
