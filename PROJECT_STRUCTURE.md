# Project Structure

This document provides an overview of the RCC Self-Extracting Assistant project structure.

## Core Components

### `launcher.py`
**Purpose**: Core self-extracting launcher logic  
**Lines**: ~320  
**Key Functions**:
- `find_payload_offset()` - Locates embedded ZIP payload
- `extract_payload()` - Extracts ZIP to local directory
- `should_extract()` - Smart extraction with hash-based versioning
- `run_rcc()` - Executes RCC with proper environment
- `main()` - Entry point

**Dependencies**: Python stdlib only (os, sys, zipfile, logging, hashlib, pathlib, subprocess)

### `builder.py`
**Purpose**: Build tool for creating self-extracting assistants  
**Lines**: ~350  
**Key Functions**:
- `validate_inputs()` - Validates RCC, robot, and Holotree paths
- `create_payload_zip()` - Packages components into ZIP
- `create_self_extracting_file()` - Combines launcher + payload
- `add_metadata()` - Adds build information to output

**Dependencies**: Python stdlib only (argparse, logging, shutil, zipfile, hashlib, pathlib, datetime)

### `test_build.py`
**Purpose**: Test suite for validating functionality  
**Lines**: ~270  
**Tests**:
- Payload marker detection
- Builder ZIP creation
- Extraction path detection
- End-to-end build process

**Coverage**: Core functionality (launcher extraction, builder packaging, payload validation)

## Build Automation

### `Makefile`
**Purpose**: Unix-style build automation  
**Targets**:
- `make build` - Build self-extracting assistant
- `make test` - Build and test
- `make clean` - Remove artifacts
- `make build-example` - Build with fetch-repos-bot

**Variables**: RCC, RCC_HOME, ROBOT, OUTPUT

### `build.py`
**Purpose**: Python-based build script (alternative to Makefile)  
**Features**:
- Auto-detection of RCC home
- Optional robot repository download
- Sensible defaults
- Cross-platform

## GitHub Actions Workflows

### `.github/workflows/build-assistant.yml`
**Purpose**: Main CI/CD pipeline  
**Triggers**: Push, PR, tags  
**Jobs**:
1. `test` - Run test suite
2. `build-assistant` - Matrix build (3 OS × 3 Python versions)
3. `build-windows-exe` - PyInstaller executable
4. `create-release` - GitHub release (on tags)
5. `summary` - Build report

**Matrix**: 
- OS: ubuntu-latest, windows-latest, macos-latest
- Python: 3.10, 3.11, 3.12

**Artifacts**: 9 .py assistants + 1 .exe = 10 total

**Permissions**:
- Most jobs: `contents: read` (principle of least privilege)
- Release job: `contents: write` (needed for GitHub releases)

### `.github/workflows/manual-build.yml`
**Purpose**: On-demand manual builds  
**Triggers**: workflow_dispatch only  
**Inputs**:
- `robot_repo` - Robot repository URL
- `robot_branch` - Branch/tag to use
- `include_holotree` - Pre-build Holotree (boolean)
- `output_name` - Custom output name

**Use Cases**:
- Testing different robot configurations
- Building from private repositories
- Custom builds without code changes

### `.github/workflows/README.md`
**Purpose**: Workflow documentation  
**Sections**:
- Workflow descriptions
- Usage instructions
- Platform-specific notes
- Customization guide
- Troubleshooting
- Security considerations

## Documentation

### `README.md`
**Main project documentation**  
**Sections**:
- Overview and features
- Quick start (GitHub Actions + local)
- Components description
- Detailed usage
- Integration examples
- Advanced topics (payload structure, .exe creation)
- Troubleshooting

### `GITHUB_ACTIONS_GUIDE.md`
**Quick start guide for GitHub Actions**  
**Sections**:
- 3 build methods (manual, auto, release)
- Step-by-step instructions
- Method comparison table
- Downloading artifacts
- Advanced scenarios
- Troubleshooting
- Tips and tricks

## Configuration Files

### `.gitignore`
**Purpose**: Exclude build artifacts and dependencies  
**Excludes**:
- Build artifacts (assistant.py, *.zip)
- Python bytecode (__pycache__, *.pyc)
- Testing artifacts (.pytest_cache, .coverage)
- IDE files (.vscode, .idea)
- OS files (.DS_Store, Thumbs.db)
- RCC artifacts (.rcc_home, robot/, rcc.exe)

## File Tree

```
rcc-selfextracting-assistant/
├── .github/
│   └── workflows/
│       ├── build-assistant.yml      # Main CI/CD workflow
│       ├── manual-build.yml         # Manual build workflow
│       └── README.md                # Workflow documentation
│
├── launcher.py                      # Core extraction logic
├── builder.py                       # Build system
├── test_build.py                    # Test suite
│
├── build.py                         # Python build script
├── Makefile                         # Unix build automation
│
├── README.md                        # Main documentation
├── GITHUB_ACTIONS_GUIDE.md          # GitHub Actions guide
│
└── .gitignore                       # Git ignore rules
```

## Typical File Sizes

After building:

| File | Size | Notes |
|------|------|-------|
| launcher.py | ~10 KB | Pure Python, no deps |
| builder.py | ~11 KB | Pure Python, no deps |
| test_build.py | ~8 KB | Test suite |
| assistant.py | 50 MB - 500 MB | Depends on Holotree size |
| RccAssistant.exe | 60 MB - 510 MB | Includes Python runtime |

## Data Flow

### Build Process

```
Input Files                Builder                  Output
-----------                -------                  ------
rcc.exe          ──────>                     
.rcc_home/       ──────>  builder.py  ──────>  assistant.py
robot/           ──────>  +launcher.py         (self-extracting)
                 
```

### Execution Process

```
User                Launcher              Filesystem
----                --------              ----------
python assistant.py
                    │
                    ├──> Find payload marker
                    ├──> Calculate hash
                    ├──> Check if extraction needed
                    │                     
                    ├──> Extract ZIP ─────> %LOCALAPPDATA%/MyRccAssistant/
                    │                       ├── rcc.exe
                    │                       ├── .rcc_home/
                    │                       └── robot/
                    │
                    ├──> Locate rcc.exe
                    ├──> Locate robot.yaml
                    ├──> Set ROBOCORP_HOME
                    │
                    └──> Execute RCC ─────> Robot runs!
```

### GitHub Actions Flow

```
Trigger (push/PR/tag)
  │
  ├──> test job ─────────────────> Run test_build.py
  │                                      │
  │                                      ✓ Pass
  │
  ├──> build-assistant job (matrix)
  │    ├──> Download RCC
  │    ├──> Clone robot
  │    ├──> Build Holotree
  │    ├──> Run builder.py
  │    └──> Upload artifact ──────> assistant-{os}-py{version}.py
  │
  ├──> build-windows-exe job
  │    ├──> Download assistant
  │    ├──> PyInstaller
  │    └──> Upload artifact ──────> RccAssistant.exe
  │
  └──> create-release job (if tagged)
       ├──> Download all artifacts
       ├──> Create archives
       └──> Create GitHub Release ─> v1.0.0 with all files
```

## Extension Points

Where to customize:

1. **Extraction location**: Modify `get_extraction_path()` in `launcher.py`
2. **RCC source**: Edit download URLs in `.github/workflows/*.yml`
3. **Robot defaults**: Change default in workflow inputs
4. **Build matrix**: Modify `strategy.matrix` in `build-assistant.yml`
5. **Artifact retention**: Change `retention-days` in upload steps
6. **Payload marker**: Change `PAYLOAD_MARKER` in both launcher and builder
7. **Logging**: Modify `setup_logging()` in `launcher.py`

## Dependencies

### Runtime (Launcher)
- Python 3.10+
- Standard library only
- No pip packages required

### Build Time (Builder)
- Python 3.10+
- Standard library only
- No pip packages required

### GitHub Actions
- actions/checkout@v4
- actions/setup-python@v5
- actions/upload-artifact@v4
- actions/download-artifact@v4
- softprops/action-gh-release@v1

### Optional
- PyInstaller (for .exe creation)
- Make (for Makefile usage)

## Testing Strategy

### Unit Tests
- `test_payload_marker_detection()` - Validates marker search
- `test_builder_basic()` - Validates ZIP creation
- `test_extraction_path()` - Validates path detection
- `test_end_to_end_build()` - Validates full build

### Integration Tests
- GitHub Actions workflows test real builds
- Matrix testing across platforms
- Artifact validation in workflows

### Manual Testing
User should test:
1. Build with real RCC and robot
2. Run on target platform
3. Verify offline operation
4. Test re-extraction with updated payload

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Payload marker search | <1s | Fast binary search |
| First extraction | 10-60s | Depends on payload size |
| Subsequent runs | <1s | Skips extraction |
| Build (no Holotree) | 5-30s | Just packaging |
| Build (with Holotree) | 5-15 min | Includes Holotree build |
| CI/CD full matrix | 15-30 min | Parallel builds |

## Security Considerations

1. **Workflow permissions**: Least privilege (contents: read/write)
2. **Secret handling**: Not embedded by default (user must add)
3. **Code execution**: Only runs user-provided RCC and robot
4. **Payload integrity**: SHA256 hash validation
5. **No external deps**: Reduces supply chain risk

## Maintenance

### Regular Updates
- RCC version: Update download URLs when new versions release
- Python versions: Update matrix when new versions are supported
- Action versions: Keep actions up to date for security

### Monitoring
- GitHub Actions status
- Test suite results
- CodeQL security alerts
- Artifact download counts

### Troubleshooting Resources
- Launcher logs: `%LOCALAPPDATA%/MyRccAssistant/launcher.log`
- Workflow logs: GitHub Actions tab
- Test output: `python test_build.py`

---

**Version**: 1.0.0  
**Last Updated**: 2024-11-19  
**Maintainer**: See repository contributors
