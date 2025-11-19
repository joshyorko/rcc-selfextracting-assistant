# Quick Start Guide: Building with GitHub Actions

This guide shows you how to build your self-extracting RCC assistant using GitHub Actions - no local Python or RCC installation required!

## 🚀 Method 1: Manual Build (Easiest)

Perfect for one-off builds or testing different configurations.

### Steps:

1. **Navigate to Actions**
   - Go to your GitHub repository
   - Click the **Actions** tab at the top

2. **Select Manual Build Workflow**
   - Find **Manual Build** in the workflows list on the left
   - Click on it

3. **Run the Workflow**
   - Click the **Run workflow** dropdown button (top right)
   - Configure the build:
     - **Robot repository URL**: Enter your robot's GitHub URL
       - Example: `https://github.com/joshyorko/fetch-repos-bot`
     - **Robot branch**: Branch or tag to use (default: `main`)
     - **Include Holotree**: ✅ Check this for offline mode
     - **Output name**: Name for your assistant (default: `assistant`)
   - Click **Run workflow** button

4. **Wait for Build to Complete**
   - Watch the workflow run (refresh page to see progress)
   - Typically takes 3-10 minutes depending on robot size

5. **Download Your Assistant**
   - Once complete, click on the workflow run
   - Scroll to **Artifacts** section at the bottom
   - Click to download your assistant `.py` file

### Example Configuration:

```
Robot repository URL: https://github.com/joshyorko/fetch-repos-bot
Robot branch: main
Include Holotree: ✅ (checked)
Output name: my-fetch-bot
```

Result: You'll get `my-fetch-bot.py` that runs completely offline!

## 🔄 Method 2: Automatic Builds on Push

Best for continuous delivery - every push automatically builds your assistant.

### Setup:

1. **Push to Main Branch**
   ```bash
   git add .
   git commit -m "Update robot"
   git push origin main
   ```

2. **Workflow Runs Automatically**
   - GitHub Actions detects the push
   - Builds assistants for all platforms:
     - `assistant-ubuntu-latest-py3.11.py`
     - `assistant-windows-latest-py3.11.py`
     - `assistant-macos-latest-py3.11.py`
     - Plus Python 3.10 and 3.12 versions
     - Plus `RccAssistant.exe` for Windows

3. **Download Artifacts**
   - Go to **Actions** tab
   - Click on the latest workflow run
   - Download from **Artifacts** section

### When to Use:

- You're actively developing a robot
- You want automated builds for every change
- You need builds for multiple platforms

## 📦 Method 3: Create a Release

Best for versioned releases that users can download.

### Steps:

1. **Tag Your Commit**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Workflow Creates Release Automatically**
   - GitHub Actions detects the tag
   - Builds all platform assistants
   - Creates Windows .exe
   - Creates a GitHub Release
   - Attaches all files to the release

3. **Download from Releases**
   - Go to **Releases** section (right sidebar or `/releases`)
   - Find your version (e.g., `v1.0.0`)
   - Download the platform-specific ZIP file
   - Extract and run!

### Semantic Versioning:

```bash
v1.0.0  # Major release
v1.1.0  # Minor update (new features)
v1.1.1  # Patch (bug fixes)
```

## 🎯 Choosing the Right Method

| Method | Use Case | Speed | Flexibility |
|--------|----------|-------|-------------|
| Manual Build | Quick test or custom robot | Fast | High |
| Auto on Push | Active development | Auto | Medium |
| Release | Production deployment | Auto | Medium |

## 📥 Downloading and Using Your Assistant

### From Artifacts:

1. Click on the artifact name (e.g., `assistant-windows-latest-py3.11`)
2. Browser downloads a ZIP file
3. Extract the ZIP
4. Run the `.py` file:
   ```bash
   python assistant-windows-latest-py3.11.py
   ```

### From Releases:

1. Download the platform-specific ZIP
2. Extract it
3. Run the assistant:
   ```bash
   # Linux/Mac
   python assistant.py
   
   # Windows (or use .exe)
   python assistant.py
   # OR
   RccAssistant.exe
   ```

## 🔧 Advanced: Custom Robot Repository

Want to build an assistant from a different robot repository?

### Using Manual Build:

1. Actions → Manual Build → Run workflow
2. Set **Robot repository URL** to your repo:
   ```
   https://github.com/your-org/your-robot
   ```
3. Choose branch, configure Holotree
4. Run and download!

### Using Your Own Fork:

1. Fork this repository
2. Enable GitHub Actions in your fork
3. Modify `.github/workflows/build-assistant.yml`:
   ```yaml
   default: 'https://github.com/YOUR-ORG/YOUR-ROBOT'
   ```
4. Push to main - builds automatically!

## 🐛 Troubleshooting

### Build Failed: "Robot repository not found"

**Problem**: Can't clone the robot repository.

**Solutions**:
- Check the URL is correct
- Ensure the repository is public
- For private repos, add a Personal Access Token

### Build Failed: "robot.yaml not found"

**Problem**: Robot structure is incorrect.

**Solutions**:
- Verify `robot.yaml` exists in the repository
- Check the file name (case-sensitive!)
- Ensure it's at the root or in a standard location

### Holotree Build Warning

**Problem**: Holotree build partially failed.

**Impact**: Assistant will work but may need internet on first run.

**Solutions**:
- Check RCC compatibility with the robot
- Review workflow logs for specific errors
- Consider building without Holotree (online mode)

### Artifact Not Available

**Problem**: Can't find the artifact after build completes.

**Solutions**:
- Refresh the page
- Check workflow actually completed (green checkmark)
- Look in the correct workflow run
- Artifacts expire after 90 days - rebuild if needed

## 💡 Tips

### Speed Up Builds

- **Use Holotree caching**: Coming soon!
- **Smaller robots build faster**: Minimize dependencies
- **Build on-demand**: Use Manual Build instead of auto-builds

### Testing Locally First

Before using GitHub Actions, test locally:

```bash
# Run test suite
python test_build.py

# Test build with mock data
python builder.py --rcc rcc.exe --robot test-robot --output test.py
```

### Multiple Robots

Build different robots as different artifacts:

1. Manual Build → Set output name: `robot-a`
2. Manual Build → Set output name: `robot-b`
3. Download both from Artifacts

### Workflow Status Badge

Add to your README:

```markdown
![Build Status](https://github.com/yourname/rcc-selfextracting-assistant/workflows/Build%20Self-Extracting%20RCC%20Assistant/badge.svg)
```

## 📚 Learn More

- [GitHub Actions Documentation](.github/workflows/README.md)
- [Builder Documentation](README.md)
- [Launcher Details](launcher.py)
- [Builder Details](builder.py)

## ❓ Need Help?

1. Check workflow logs in Actions tab
2. Review [Troubleshooting](#-troubleshooting) section
3. Open an issue on GitHub
4. Check RCC documentation for robot-specific issues

---

**Pro Tip**: Start with Manual Build to test your configuration, then switch to automatic builds for continuous delivery!
