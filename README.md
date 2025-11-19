# RCC Self-Extracting Assistant

A single-file, self-contained Python launcher that embeds a complete RCC environment, inspired by [Copyparty](https://github.com/9001/copyparty)'s self-extracting design.

## Overview

This project provides tools to create a **single `.py` file** that contains:
- `rcc.exe` (your custom RCC fork)
- A pre-baked `.rcc_home` Holotree catalog
- A robot project
- All necessary bootstrap logic

When executed, the file automatically:
1. Extracts the embedded payload to `%LOCALAPPDATA%/MyRccAssistant` (Windows) or `~/.local/share/MyRccAssistant` (Linux/Mac)
2. Sets up the `ROBOCORP_HOME` environment
3. Runs your robot using the embedded RCC

Subsequent runs skip extraction if the payload hasn't changed, enabling fast startup.

## Features

- ✅ **Zero Installation**: No Python packages, RCC installation, or Holotree building required for end users
- ✅ **Offline Capable**: Embeds everything needed to run offline
- ✅ **Smart Extraction**: Only extracts when payload changes (version detection via hash)
- ✅ **Cross-Platform**: Works on Windows, Linux, and macOS
- ✅ **Minimal Dependencies**: Uses only Python standard library (3.10+)
- ✅ **Logging**: Comprehensive logs for debugging
- ✅ **Reproducible Builds**: Deterministic build process
- ✅ **CI/CD Integration**: GitHub Actions workflows for automated builds
- ✅ **Multi-Platform Artifacts**: Automatic builds for Windows, Linux, and macOS

## Quick Start

### Option 1: Build with GitHub Actions (Recommended)

The easiest way to build your assistant is using GitHub Actions - no local setup required!

1. **Fork or clone this repository**
2. **Go to Actions tab** in GitHub
3. **Select "Manual Build"** workflow
4. **Click "Run workflow"** and configure:
   - Robot repository URL: `https://github.com/joshyorko/fetch-repos-bot`
   - Include Holotree: ✅ (for offline mode)
   - Output name: `my-assistant`
5. **Download** from Artifacts section when complete

Your assistant will be built automatically with all dependencies!

### Option 2: Build Locally

```bash
# 1. Clone this repository
git clone https://github.com/joshyorko/rcc-selfextracting-assistant.git
cd rcc-selfextracting-assistant

# 2. Prepare your components:
#    - rcc.exe (your custom RCC fork)
#    - .rcc_home/ (pre-built Holotree catalog)
#    - robot/ (your robot project with robot.yaml)

# 3. Build the self-extracting assistant
python builder.py \
    --rcc /path/to/rcc.exe \
    --rcc-home /path/to/.rcc_home \
    --robot /path/to/robot \
    --output assistant.py

# 4. Distribute assistant.py - that's it!
```

### Running the Assistant

```bash
# Just run it with Python
python assistant.py

# Or make it executable (Linux/Mac)
chmod +x assistant.py
./assistant.py
```

## Components

### `launcher.py`

The core extraction and execution logic:
- Searches for the `===RCC_PAYLOAD_START===` marker
- Extracts the embedded ZIP payload
- Locates `rcc.exe`, `robot.yaml`, and `.rcc_home`
- Executes RCC with proper environment setup
- Logs everything for debugging

### `builder.py`

The build tool that creates self-extracting files:
- Validates inputs
- Creates a payload ZIP with your RCC + Holotree + robot
- Combines `launcher.py` + marker + payload into a single file
- Adds metadata (build date, source paths, checksums)

### GitHub Actions Workflows

Automated CI/CD pipelines for building assistants:

**Main Workflow** (`build-assistant.yml`):
- Triggers on push, PR, or tags
- Builds for Windows, Linux, macOS
- Tests Python 3.10, 3.11, 3.12
- Creates Windows .exe bundle
- Produces GitHub Releases for tags

**Manual Workflow** (`manual-build.yml`):
- Build on-demand via GitHub UI
- Specify custom robot repository
- Choose Holotree inclusion
- Download as artifact

See [`.github/workflows/README.md`](.github/workflows/README.md) for detailed documentation.

## Detailed Usage

### Builder Options

```bash
python builder.py --help

Required arguments:
  --rcc PATH          Path to RCC executable (rcc.exe or rcc)
  --robot PATH        Path to robot project directory

Optional arguments:
  --rcc-home PATH     Path to .rcc_home directory (for offline mode)
  --output PATH       Output path (default: assistant.py)
  --launcher PATH     Custom launcher.py (default: ./launcher.py)
  --temp-dir PATH     Temporary directory for build artifacts
```

### Example: Building with fetch-repos-bot

```bash
# Clone the test robot
git clone https://github.com/joshyorko/fetch-repos-bot.git

# Build Holotree with your RCC fork (do this once)
./rcc.exe holotree variables fetch-repos-bot/robot.yaml

# Build the self-extracting assistant
python builder.py \
    --rcc rcc.exe \
    --rcc-home ~/.robocorp/holotree \
    --robot fetch-repos-bot \
    --output my-assistant.py

# Run it!
python my-assistant.py
```

### Launcher Behavior

On first run:
```
[INFO] RCC Self-Extracting Assistant Launcher
[INFO] Searching for embedded payload...
[INFO] Payload found at offset: 10543 bytes
[INFO] Target directory does not exist, extraction needed
[INFO] Extracting payload to: C:\Users\YourName\AppData\Local\MyRccAssistant
[INFO] Extraction complete: 4523 items extracted
[INFO] Found RCC: C:\Users\YourName\AppData\Local\MyRccAssistant\rcc.exe
[INFO] Found robot: C:\Users\YourName\AppData\Local\MyRccAssistant\robot\robot.yaml
[INFO] Using ROBOCORP_HOME: C:\Users\YourName\AppData\Local\MyRccAssistant\.rcc_home
[INFO] Running RCC...
```

On subsequent runs:
```
[INFO] RCC Self-Extracting Assistant Launcher
[INFO] Payload found at offset: 10543 bytes
[INFO] Payload unchanged, skipping extraction
[INFO] Running RCC...
```

### Using GitHub Actions for Automated Builds

#### Automatic Builds on Push

Every push to `main` automatically builds assistants for all platforms:

```bash
git add .
git commit -m "Update robot configuration"
git push origin main
```

Navigate to **Actions** tab to download artifacts for Windows, Linux, and macOS.

#### Manual Build with Custom Robot

1. Go to **Actions** → **Manual Build** → **Run workflow**
2. Configure:
   - **Robot repo**: `https://github.com/yourorg/your-robot`
   - **Branch**: `main` (or any branch/tag)
   - **Include Holotree**: ✅ (recommended for offline)
   - **Output name**: `my-custom-assistant`
3. Click **Run workflow**
4. Download from **Artifacts** when complete

#### Creating Releases

Tag your commits to create GitHub Releases with binaries:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow automatically:
- Builds for all platforms
- Creates Windows .exe
- Publishes GitHub Release
- Attaches all artifacts

Download releases from the **Releases** page.

#### Downloading Built Artifacts

**From Actions:**
1. Go to **Actions** tab
2. Click on workflow run
3. Scroll to **Artifacts** section
4. Download your platform's assistant

**From Releases:**
1. Go to **Releases** section
2. Find your version
3. Download platform-specific ZIP

## Integration with Existing Projects

### Using with fetch-repos-bot

The [fetch-repos-bot](https://github.com/joshyorko/fetch-repos-bot) repository is a perfect candidate for bundling:

```bash
# 1. Clone and prepare the robot
git clone https://github.com/joshyorko/fetch-repos-bot.git
cd fetch-repos-bot

# 2. Build Holotree (if not already done)
rcc holotree variables robot.yaml

# 3. Go back to the builder directory
cd ../rcc-selfextracting-assistant

# 4. Build the bundle
python builder.py \
    --rcc /path/to/your/custom/rcc.exe \
    --rcc-home ~/.robocorp/holotree \
    --robot ../fetch-repos-bot \
    --output fetch-repos-assistant.py

# 5. Test it
python fetch-repos-assistant.py
```

## Advanced Topics

### Payload Structure

The self-extracting file has this structure:

```
┌─────────────────────────┐
│ launcher.py code        │  Python script with extraction logic
├─────────────────────────┤
│ # Marker comment        │  Human-readable separator
├─────────────────────────┤
│ ===RCC_PAYLOAD_START=== │  Binary marker
├─────────────────────────┤
│                         │
│   ZIP Payload:          │  Standard ZIP archive
│   ├── rcc.exe           │
│   ├── .rcc_home/        │
│   │   └── (Holotree)    │
│   └── robot/            │
│       └── robot.yaml    │
│                         │
└─────────────────────────┘
```

### Version Detection

The launcher automatically detects payload changes:
- Calculates SHA256 hash of the embedded payload
- Stores hash in `.payload_hash` after extraction
- Re-extracts if hash changes (e.g., updated bundle)

This allows you to distribute updated assistants - users just replace the file and run it again.

### Creating a Windows .exe

You can optionally wrap the `.py` file into a standalone `.exe` using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --name MyAssistant assistant.py

# The result is in dist/MyAssistant.exe
```

**Note**: The `.exe` will be larger (~10-15 MB) due to embedded Python interpreter, but it won't require Python installation.

Alternatively, use tools like:
- [Nuitka](https://nuitka.net/) - compiles Python to C
- [cx_Freeze](https://cx-freeze.readthedocs.io/) - creates executables
- [py2exe](http://www.py2exe.org/) - Windows-specific

### Customizing the Launcher

You can modify `launcher.py` to:
- Change the extraction directory
- Add custom pre/post-execution hooks
- Modify logging behavior
- Add GUI progress dialogs (with tkinter)
- Implement auto-updates

Example: Custom extraction path:
```python
def get_extraction_path():
    """Custom extraction directory."""
    return Path("C:/MyCompany/Assistants/MyRccAssistant")
```

### Build Automation

Create a `Makefile` or build script:

```makefile
# Makefile example
.PHONY: build clean

RCC := rcc.exe
RCC_HOME := $(HOME)/.robocorp/holotree
ROBOT := ../fetch-repos-bot
OUTPUT := assistant.py

build:
	python builder.py \
		--rcc $(RCC) \
		--rcc-home $(RCC_HOME) \
		--robot $(ROBOT) \
		--output $(OUTPUT)
	@echo "Build complete: $(OUTPUT)"

clean:
	rm -f $(OUTPUT)

test: build
	python $(OUTPUT)
```

Or a Python build script:

```python
#!/usr/bin/env python3
"""build.py - Automated build script"""
import subprocess
import sys

def main():
    cmd = [
        "python", "builder.py",
        "--rcc", "rcc.exe",
        "--rcc-home", ".rcc_home",
        "--robot", "fetch-repos-bot",
        "--output", "assistant.py"
    ]
    
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
```

## Troubleshooting

### "No embedded payload found"

The launcher couldn't find the `===RCC_PAYLOAD_START===` marker. This means:
- You're running `launcher.py` directly (you should run `assistant.py` built by `builder.py`)
- The build process failed partway through

**Solution**: Build the assistant properly with `builder.py`

### "Could not find rcc.exe in extracted payload"

The payload was extracted but RCC executable wasn't found. Check:
- Does your RCC executable exist at the path you specified to `--rcc`?
- Is it named `rcc.exe` or `rcc`?

### "Could not find robot.yaml in extracted payload"

The robot project was included but doesn't have a `robot.yaml`. Check:
- Does your robot directory have a `robot.yaml` file?
- Is the file name exactly `robot.yaml` (case-sensitive on Linux)?

### Extraction fails with "Permission denied"

The target directory isn't writable. Check:
- Do you have write permissions to `%LOCALAPPDATA%` (Windows) or `~/.local/share` (Linux)?
- Is another instance of the assistant running?

### RCC execution fails

Check the logs in `%LOCALAPPDATA%/MyRccAssistant/launcher.log` for details.

Common issues:
- RCC isn't compatible with your OS
- Robot has missing dependencies
- `.rcc_home` Holotree is incomplete or corrupted

## Future Enhancements

Planned features for future versions:

- [ ] Auto-updater: detect new payload versions and re-extract
- [ ] Embedded metadata viewer (`assistant.py --info`)
- [ ] Checksum validation of Holotree layers
- [ ] Support for multiple robots in one bundle
- [ ] GUI launcher with progress bars
- [ ] Delta updates (only download changed files)
- [ ] Signature verification for secure distribution

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Specify your license here]

## Credits

- Inspired by [Copyparty](https://github.com/9001/copyparty)'s self-extracting design
- Built for [Robocorp RCC](https://github.com/robocorp/rcc)

## See Also

- [fetch-repos-bot](https://github.com/joshyorko/fetch-repos-bot) - Example robot for bundling
- [Robocorp RCC](https://github.com/robocorp/rcc) - Robot automation framework
- [Copyparty](https://github.com/9001/copyparty) - Inspiration for self-extracting design