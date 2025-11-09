# AI-Pal Team Setup & Collaboration Guide

Welcome to the AI-Pal development team! This guide will get you up and running quickly.

## 🚀 Quick Start (Choose Your Path)

### I'm a Developer (5 min setup)
```bash
# Clone and setup
git clone https://github.com/caseymrobbins/ai-pal.git
cd ai-pal

# Run setup script
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh

# Or manually:
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start development
python -m uvicorn ai_pal.api.main:app --reload --port 8000

# In another terminal, start dashboard
cd dashboard
npm run dev
```

### I'm a QA / Tester (5 min setup)
```bash
# Setup environment
git clone https://github.com/caseymrobbins/ai-pal.git
cd ai-pal

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run specific test category
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/security/      # Security tests
```

### I'm a DevOps / Infrastructure (5 min setup)
```bash
# Clone repository
git clone https://github.com/caseymrobbins/ai-pal.git
cd ai-pal

# Check Docker setup
docker build -t ai-pal:latest .
docker run -p 8000:8000 ai-pal:latest

# Check Kubernetes manifests
ls k8s/
kubectl apply --dry-run=client -f k8s/

# Check CI/CD workflows
ls .github/workflows/
```

---

## 📚 Documentation Roadmap

### By Role

#### 👨‍💻 Backend Developers
1. **Quick Start**: `QUICK_START_DEVELOPER.md` (5 min)
2. **Deep Dive**: `TEAM_COLLABORATION.md` - Development section (20 min)
3. **Reference**: `API_DOCUMENTATION.md` - Endpoint reference (as needed)
4. **Architecture**: `ARCHITECTURE.md` - System design (30 min)

#### 🎨 Frontend Developers
1. **Quick Start**: `dashboard/README.md` (5 min)
2. **Setup**: `dashboard/DEPLOYMENT.md` (10 min)
3. **API Integration**: `dashboard/API_INTEGRATION.md` (15 min)
4. **Deep Dive**: `TEAM_COLLABORATION.md` - Testing section (20 min)

#### 🧪 QA / Test Engineers
1. **Quick Start**: `QUICK_START_DEVELOPER.md` - Testing section (5 min)
2. **Testing Guide**: `TEAM_COLLABORATION.md` - Testing infrastructure (20 min)
3. **CI/CD**: `TEAM_COLLABORATION.md` - CI/CD pipeline (15 min)
4. **Reference**: `PROJECT_EXPLORATION_SUMMARY.md` - Test files (10 min)

#### 🚀 DevOps / Infrastructure
1. **Quick Start**: Deployment section below (10 min)
2. **Deployment**: `dashboard/DEPLOYMENT.md` (20 min)
3. **Infrastructure**: `PROJECT_EXPLORATION_SUMMARY.md` - CI/CD section (20 min)
4. **Architecture**: `ARCHITECTURE.md` (30 min)

#### 👔 Project Managers / Team Leads
1. **Overview**: `PROJECT_EXPLORATION_SUMMARY.md` - Executive summary (15 min)
2. **Architecture**: `ARCHITECTURE.md` (30 min)
3. **Workflows**: `TEAM_COLLABORATION.md` - Development workflow (20 min)
4. **All Docs**: `DOCUMENTATION_INDEX.md` - Complete navigation (5 min)

---

## 🔧 Development Setup (All Platforms)

### Prerequisites
- **Python 3.9+** (verify: `python --version`)
- **Node.js 18+** (verify: `node --version`)
- **Git** (verify: `git --version`)
- **Docker** (optional, for containerized testing)

### Step 1: Clone Repository
```bash
git clone https://github.com/caseymrobbins/ai-pal.git
cd ai-pal
```

### Step 2: Create Virtual Environment
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
# Backend dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend dependencies
cd dashboard
npm install
cd ..
```

### Step 4: Configure Environment
```bash
# Copy example files
cp .env.example .env
cp dashboard/.env.example dashboard/.env

# Edit .env with your API keys if needed
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

### Step 5: Run Code Quality Checks
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Step 6: Run Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific category
pytest -m unit tests/
pytest -m integration tests/
```

---

## 🌳 Git Workflow

### Branch Naming Convention
```
type/description

Examples:
feature/add-ari-monitoring
bugfix/fix-auth-token-validation
refactor/optimize-goal-scoping
docs/update-api-docs
chore/update-dependencies
```

### Daily Workflow
```bash
# 1. Start work
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 2. Make changes and commit
git add .
git commit -m "feat: Add new feature

Description of what changed and why.
Fixes #123 (if fixing an issue)"

# 3. Push and create PR
git push origin feature/your-feature-name

# Visit GitHub to create a Pull Request
# Add description, link issues, request reviewers

# 4. After approval and CI passes
git checkout main
git pull origin main
git merge feature/your-feature-name
git push origin main

# 5. Clean up
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

Fixes #<issue_number>
```

**Types**: feat, fix, docs, style, refactor, perf, test, chore
**Scope**: Feature area (e.g., auth, goals, ari, dashboard)
**Subject**: Brief description (imperative mood, lowercase)
**Body**: Detailed explanation of changes

---

## ✅ Code Quality Standards

### Python Code Style
```bash
# Format with Black
black src/

# Check style
ruff check src/ --fix

# Type checking
mypy src/
```

**Standards**:
- Line length: 100 characters
- Indentation: 4 spaces
- Quotes: Double quotes (except where ' is preferred)
- Docstrings: Google style

### React/TypeScript Code Style
```bash
# Format
cd dashboard && npm run format

# Lint
npm run lint

# Type check
npm run type-check
```

### Pre-commit Checks
```bash
# Automatic checks before commit
# Black, Ruff, MyPy run automatically
# Tests verify Four Gates compliance
```

---

## 🧪 Testing Guidelines

### Test Categories
```bash
pytest -m unit          # Fast unit tests
pytest -m integration   # API integration tests
pytest -m e2e          # End-to-end tests
pytest -m slow         # Long-running tests
```

### Minimum Coverage
- **Overall**: 70% minimum
- **Critical paths**: 90% minimum (auth, gates, privacy)
- **Check coverage**: `pytest --cov=src --cov-report=html`

### Writing Tests
```python
# Example test structure
import pytest
from src.core.gates import gate_system

@pytest.mark.unit
def test_gate_validation():
    """Test that Gate 1 validates net agency."""
    result = gate_system.validate_gate_1(
        user_autonomy=0.8,
        ai_impact=0.3
    )
    assert result.passed == True
    assert result.delta_agency >= 0
```

---

## 🔄 CI/CD Pipeline (Four Gates)

### What Happens on Every Commit
```
1. Code Quality Checks
   ├─ Black formatting
   ├─ Ruff linting
   ├─ MyPy type checking
   └─ ESLint (frontend)

2. Unit Tests (70% coverage required)
   └─ Fail if coverage drops

3. Gate 1: Net Agency Test
   └─ Validates AI expands user capability

4. Gate 2: Extraction Analysis
   └─ Detects dark patterns and lock-ins

5. Gate 3: Humanity Override
   └─ Ensures user control mechanisms work

6. Gate 4: Performance Parity
   └─ Validates fair performance across groups

7. Integration Tests
   └─ Full system tests

8. Security Tests
   └─ Vulnerability scanning

9. Build & Deploy (main branch only)
   └─ Docker build, push to registry
   └─ Deploy to staging/production
```

### Viewing CI Results
1. Open your Pull Request on GitHub
2. Scroll to "Checks" section
3. Click on failed checks for details
4. Fix issues locally and push updates

---

## 🚀 Running the Full System Locally

### Terminal 1: Backend API
```bash
source venv/bin/activate
python -m uvicorn ai_pal.api.main:app --reload --port 8000

# API docs available at:
# http://localhost:8000/docs (Swagger)
# http://localhost:8000/redoc (ReDoc)
```

### Terminal 2: Dashboard Frontend
```bash
cd dashboard
npm run dev

# Dashboard available at:
# http://localhost:5173
```

### Terminal 3: Tests (Optional)
```bash
source venv/bin/activate
pytest tests/ --watch

# Or run specific tests
pytest tests/unit/ -v
```

### Testing the Integration
1. Open http://localhost:5173
2. Login with any email
3. Dashboard should fetch real data from backend on :8000
4. Check browser DevTools Network tab for API calls

---

## 📊 Key Project Statistics

| Metric | Value |
|--------|-------|
| **Total Python Files** | 114 |
| **Lines of Code** | 44,000+ |
| **Test Files** | 31 |
| **Test Coverage** | 80%+ |
| **Documentation Files** | 25+ |
| **API Endpoints** | 40+ |
| **React Components** | 10+ |
| **CI/CD Workflows** | 2 (with 4 gates) |

---

## 📞 Getting Help

### Finding Information
```bash
# Search documentation
grep -r "your search term" .

# Find specific files
find . -name "*.md" | grep -i "topic"

# Check GitHub Issues
# https://github.com/caseymrobbins/ai-pal/issues

# View discussions
# https://github.com/caseymrobbins/ai-pal/discussions
```

### Common Issues

**Issue**: Import errors
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Issue**: Tests failing
```bash
# Check Python version (need 3.9+)
python --version

# Reset and try again
pytest tests/ -v --tb=short
```

**Issue**: Backend connection failed
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check .env configuration
cat .env | grep API_URL
```

**Issue**: Dashboard not loading
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
cd dashboard && npm install
npm run dev
```

---

## 📋 Daily Checklist

### Before Starting Work
- [ ] Pull latest changes: `git pull origin main`
- [ ] Create feature branch: `git checkout -b feature/your-feature`
- [ ] Activate venv: `source venv/bin/activate`
- [ ] Update dependencies: `pip install -r requirements.txt`

### While Working
- [ ] Run tests frequently: `pytest tests/`
- [ ] Check code style: `black src/ && ruff check src/`
- [ ] Commit frequently with clear messages
- [ ] Push to feature branch regularly

### Before Creating Pull Request
- [ ] Run all tests: `pytest tests/ --cov=src`
- [ ] Format code: `black src/ && ruff check --fix src/`
- [ ] Type check: `mypy src/`
- [ ] Update documentation if needed
- [ ] Test integration locally

### After Pull Request
- [ ] Review CI/CD results
- [ ] Address any failing checks
- [ ] Request code review from teammates
- [ ] Respond to review comments
- [ ] Merge to main once approved

---

## 🎯 Project Goals & Philosophy

The AI-Pal project implements **Agency Calculus for AI (AC-AI)**, ensuring:

1. **Net Agency**: AI increases user autonomy, not dependency
2. **No Extraction**: No dark patterns, lock-ins, or coercion
3. **Humanity Override**: Users maintain ultimate control
4. **Performance Parity**: Fair treatment across all groups

These principles are enforced through the **Four Gates system**, which validates every significant AI action.

---

## 📚 Documentation Index

| Document | Purpose | Audience | Time |
|----------|---------|----------|------|
| **QUICK_START_DEVELOPER.md** | Fast setup reference | All developers | 5 min |
| **TEAM_COLLABORATION.md** | Comprehensive guide | Team members | 45 min |
| **PROJECT_EXPLORATION_SUMMARY.md** | Infrastructure audit | Architects, Leads | 20 min |
| **DOCUMENTATION_INDEX.md** | Navigation guide | All users | 5 min |
| **API_DOCUMENTATION.md** | API endpoint reference | Backend devs | 30 min |
| **dashboard/README.md** | Frontend guide | Frontend devs | 10 min |
| **dashboard/API_INTEGRATION.md** | Dashboard API integration | Frontend devs | 15 min |
| **ARCHITECTURE.md** | System design | All architects | 30 min |

---

## 🚀 Next Steps

1. **Read this document** (you're doing it! 👍)
2. **Choose your quick start** (top of this guide)
3. **Set up your environment** (follow setup steps)
4. **Run the tests** (verify everything works)
5. **Read QUICK_START_DEVELOPER.md** (reference guide)
6. **Pick your first task** and create a PR
7. **Join our discussions** on GitHub

---

## 💡 Tips for Success

- **Ask questions**: Use GitHub Discussions or reach out to team
- **Read the code**: Best documentation is well-written code
- **Run tests**: Before and after changes
- **Small commits**: Easier to review and debug
- **Descriptive messages**: Future you will thank present you
- **Code review**: Great learning opportunity
- **Check CI/CD**: Don't wait for slow feedback cycles

---

## 📞 Support Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and ideas
- **Pull Request Comments**: Code review feedback
- **Documentation**: Check docs before asking (RTFM)
- **Team Chat**: Real-time communication (if available)

---

**Welcome to the team! Happy coding! 🎉**

---

**Version**: 1.0.0
**Last Updated**: November 2024
**Maintained by**: AI-Pal Development Team
