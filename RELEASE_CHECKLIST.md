# 🚀 Release Checklist for Search Fusion MCP

## Pre-Release Checklist

### 📋 Code Quality
- [x] All Python files use English comments and strings
- [x] No Chinese characters in code
- [x] Consistent import structure
- [x] All deprecated files removed
- [x] Code follows PEP 8 style guidelines

### 🧪 Testing
- [x] MCP tools registration works correctly
- [x] All search engines initialize properly
- [x] Web fetching with pagination works
- [x] Wikipedia search functions
- [x] Configuration loading works with environment variables

### 📚 Documentation
- [x] README.md is up to date
- [x] README_zh.md is up to date
- [x] API documentation is complete
- [x] Installation instructions are clear
- [x] Configuration examples are correct

### 🔧 Configuration
- [x] requirements.txt contains all necessary dependencies
- [x] setup.py has correct metadata
- [x] pyproject.toml is properly configured
- [x] MANIFEST.in includes all necessary files

### 🏗️ Build Preparation
- [x] Version number updated in setup.py
- [x] Version number updated in pyproject.toml
- [x] Changelog is updated (if exists)
- [x] All temporary files removed

## Release Process

### 🔨 Build
```bash
# 1. Clean environment
python build.py

# 2. Alternative manual build
python setup.py sdist bdist_wheel

# 3. Check package
twine check dist/*
```

### 🧪 Test Installation
```bash
# Test wheel installation
pip install dist/*.whl

# Test from TestPyPI
pip install -i https://test.pypi.org/simple/ search-fusion-mcp
```

### 📦 Upload

#### Test Upload (TestPyPI)
```bash
twine upload --repository testpypi dist/*
```

#### Production Upload (PyPI)
```bash
twine upload dist/*
```

## Post-Release

### ✅ Verification
- [ ] Package installs correctly from PyPI
- [ ] All tools work in MCP environment
- [ ] Documentation links work
- [ ] GitHub release created
- [ ] Version tags created

### 📢 Communication
- [ ] Update project README with new version
- [ ] Announce in relevant communities
- [ ] Update any dependent projects

## 🔧 Build Commands Quick Reference

```bash
# Install build dependencies
pip install setuptools wheel twine

# Clean build
rm -rf build dist *.egg-info

# Build package
python setup.py sdist bdist_wheel

# Check package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## 📋 Environment Variables for Upload

```bash
# PyPI credentials (optional, can use interactive)
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=your_pypi_token

# TestPyPI credentials
export TWINE_REPOSITORY_URL=https://test.pypi.org/legacy/
```

## 🐛 Common Issues

1. **Import errors**: Check relative imports in package
2. **Missing files**: Update MANIFEST.in
3. **Dependencies**: Verify requirements.txt
4. **Metadata**: Check setup.py configuration
5. **MCP not working**: Verify entry points in setup.py
