# PyPI Upload Instructions

## Package Ready for Publication

**Version**: 2.0.0-beta
**Status**: Production-grade quality (84.6% test coverage)
**Files**: Built and validated

---

## Quick Upload (Test PyPI)

```bash
# 1. Get Test PyPI token
# Visit: https://test.pypi.org/manage/account/token/

# 2. Set credentials
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-TEST-PYPI-TOKEN-HERE

# 3. Upload
cd /Users/patrickroebuck/projects/memdocsRelease1/memdocs
twine upload --repository testpypi dist/*

# 4. Test installation
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  memdocs==2.0.0b0
```

---

## Production PyPI (After Testing)

```bash
# 1. Get Production PyPI token
# Visit: https://pypi.org/manage/account/token/

# 2. Set credentials
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-PRODUCTION-TOKEN-HERE

# 3. Upload
twine upload dist/*

# 4. Verify
# Visit: https://pypi.org/project/memdocs/

# 5. Test installation
pip install memdocs==2.0.0b0
```

---

## Permanent Setup (~/.pypirc)

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-TOKEN-HERE

[pypi]
username = __token__
password = pypi-YOUR-PRODUCTION-TOKEN-HERE
```

Then simply run:
```bash
twine upload --repository testpypi dist/*  # Test PyPI
twine upload dist/*                        # Production PyPI
```

---

## Package Contents

- **No wizards**: Excluded from distribution (cleaner separation)
- **Test coverage**: 84.6% (exceeds 80% production threshold)
- **Python support**: 3.10, 3.11, 3.12
- **Size**: 64.9 KB (wheel), 61.2 KB (tarball)
- **GitHub Release**: https://github.com/Smart-AI-Memory/memdocs/releases/tag/v2.0.0-beta1

---

## Verification Checklist

- [x] Package builds successfully
- [x] Twine validation passed
- [x] Wizards excluded from package
- [x] Installation tested (Python 3.10, 3.12)
- [x] GitHub release published
- [ ] Upload to Test PyPI
- [ ] Test installation from Test PyPI
- [ ] Upload to Production PyPI
- [ ] Verify on PyPI
- [ ] Test production installation

---

**Generated**: 2025-11-09
**Ready for publication!**
