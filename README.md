# AI Pal - Your Privacy-First Cognitive Partner

AI Pal is a hybrid AI architecture that combines local Small Language Models (SLMs) with cloud-based Large Language Models (LLMs) to create a powerful, privacy-preserving cognitive assistant. Built on the Agency Calculus for AI (AC-AI) framework, it prioritizes user autonomy, privacy, and ethical AI practices.

## 🌟 Core Philosophy

**Privacy First**: All user data is processed locally. Only anonymized, task-specific packets are sent to external LLMs.

**Agency Expansion**: Designed to measurably increase user autonomy and capabilities, not create dependency.

**Ethical Governance**: Every action passes through the "Four Gates" - mandatory ethical checks that ensure the system expands human agency without causing harm.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Local SLM Orchestrator                          │
│  • Manages all user state and data                          │
│  • Scrubs PII before external communication                 │
│  • Routes tasks to specialized modules                      │
│  • Synthesizes final responses                              │
└─────┬────────────────────────────────────────────────┬──────┘
      │                                                 │
┌─────▼──────────────────────┐              ┌─────────▼──────┐
│   Ethics Module (AC-AI)    │              │  Other Modules  │
│  • Four Gates Enforcement  │              │  • Learning     │
│  • Agency Measurement      │◄─────────────┤  • Echo Buster  │
│  • Epistemic Debt Monitor  │   Governs    │  • Dream        │
│  • RoP-AI Compliance       │   All        │  • Personal     │
└────────────────────────────┘              └────────────────┘
                     │
                     │ (Anonymized packets only)
                     │
┌────────────────────▼────────────────────────────────────────┐
│              External LLM APIs (Optional)                    │
│  • OpenAI  • Anthropic  • Cohere  • Others                  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Key Features

### Core Infrastructure
- **Hybrid Local/Cloud Architecture**: Best of both worlds - privacy + power
- **Automatic Hardware Detection**: Optimizes for your CPU/GPU configuration
- **Hot-Swappable Modules**: Add/remove features without restart
- **Multi-API Management**: Seamlessly work with multiple LLM providers
- **Intelligent Request Routing**: Optimal model selection based on task complexity

### Privacy & Security
- **PII Scrubbing**: Automatic removal of personally identifiable information
- **End-to-End Encryption**: All data encrypted at rest and in transit
- **Local Processing Priority**: Sensitive operations stay on your device
- **Data Portability**: Export all your data anytime
- **Granular Privacy Controls**: You decide what (if anything) goes to the cloud

### Agency & Ethics (AC-AI Framework)
- **Four Gates Implementation**:
  1. **Net-Agency Test**: Ensures aggregate agency increase ≥ 0
  2. **Extraction Test**: No dark patterns, coercion, or lock-ins
  3. **Humanity Override**: You can always override AI decisions
  4. **Non-Othering Test**: Equitable treatment of all groups
- **Real-time Agency Measurement**: Track how the AI affects your autonomy
- **Epistemic Debt Monitoring**: Detect and correct misinformation
- **Automatic Circuit Breakers**: System pauses if ethical thresholds are breached

### Specialized Modules

#### 🧠 Echo Chamber Buster
Provides balanced, multi-perspective analysis of complex topics:
- **The Critic**: Challenges assumptions and identifies flaws
- **The Challenger**: Builds the strongest counter-argument
- **The Synthesizer**: Creates balanced, nuanced conclusions

#### 📚 Learning Module
Personalized learning based on VARK model:
- Detects your learning style (Visual, Aural, Read/Write, Kinesthetic)
- Creates custom learning paths
- Tracks skill development
- Maintains optimal challenge level (Zone of Proximal Development)

#### 💭 Dream Module
Background processing during downtime:
- Consolidates patterns from interactions
- Explores hypothetical scenarios
- Pre-computes likely needed responses
- Proposes optimizations (must pass Four Gates before implementation)

#### 👤 Personal Data Module
Learn your preferences while respecting privacy:
- Builds personalized context
- Governed by Ethics Module
- Must pass Extraction Test
- Prevents harmful dependency

### Self-Improvement
- **RLHF**: Learns from your feedback
- **Automated Fine-Tuning**: LoRA/QLoRA for personalization
- **Experience Replay**: Reviews past interactions to improve
- **Performance Auto-Tuning**: Optimizes speed and accuracy
- **Constitutional AI**: Value-aligned self-improvement

### Learning & Personalization
- **VARK Learning Style Detection**
- **Skill Gap Analysis**
- **Personalized Learning Paths**
- **Progress Visualization**
- **Zone of Proximal Development Targeting**

### Behavioral Change & Habits
- **Atomic Habits Implementation**
- **Pattern Recognition**
- **Smart Reminder System**
- **Streak Tracking**
- **Micro-Habit Formation**

### Memory Systems
- **Long-Term Memory**: Remembers all conversations
- **Episodic Memory**: Specific interaction memories
- **Semantic Memory**: Knowledge graph of user information
- **Working Memory**: Current conversation context
- **Prospective Memory**: Future commitments and reminders

## 📦 Installation

### Prerequisites
- Python 3.9 or higher
- (Optional) CUDA-compatible GPU for local model acceleration
- 8GB+ RAM (16GB+ recommended for larger local models)

## Windows Desktop App (Easy Install)

This method uses a PowerShell script to install all dependencies (Git, Docker Desktop, Python) and create a simple desktop application to launch AI-Pal.

### Installation

1.  **Download the Installer Script:**
    * **[Install_AI_Pal_App.ps1](https://raw.githubusercontent.com/caseymrobbins/ai-pal/refs/heads/main/Install_AI_Pal_App.ps1)**
    * **Important:** Right-click the link and select **"Save as..."** or **"Save link as..."** to download the file. Remember where you save it (e.g., your `Downloads` folder).

2.  **Open PowerShell as Administrator:**
    * Click the Start menu.
    * Type `PowerShell`.
    * Right-click on "Windows PowerShell" and select **"Run as administrator"**.

3.  **Allow the Script to Run (for this session):**
    * In the blue Administrator PowerShell window, copy and paste the following command, then press Enter. This is necessary to get around Windows' default script security policy.
    ```powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    ```

4.  **Navigate to the Script and Run It:**
    * First, change to the directory where you saved the file. For example, if you saved it to your `Downloads` folder:
    ```powershell
    cd $HOME\Downloads
    ```
    * (If you saved it elsewhere, use `cd C:\path\to\your\folder`)
    * Now, run the script by typing its name and pressing Enter:
    ```powershell
    .\Install_AI_Pal_App.ps1
    ```

5.  **Follow the On-Screen Prompts:**
    * Press **Enter** to continue when the script starts.
    * You **must** approve all User Account Control (UAC) prompts that appear for installing Git, Docker, and Python.
    * When prompted, enter your `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`. You can press Enter to skip either key.
    * The script will clone the repository and create a new "AI-Pal" shortcut on your desktop.

6.  **Reboot Your Computer:**
    * **CRITICAL:** Once the script shows "Part 1 Complete! REBOOT REQUIRED", you **must reboot your computer**. This is a one-time step required for the Docker installation to finalize.

### How to Start AI-Pal

1.  After your computer has rebooted, double-click the new **"AI-Pal"** icon on your desktop.
2.  A small application window will open. Click the **"Start AI-Pal"** button inside this window.
3.  The app will automatically start Docker Desktop in the background (if it's not already running) and wait for it to be ready. It will then build and launch the AI-Pal containers.
4.  Once the server is running, the window will automatically load the AI-Pal interface (http://localhost:8000).
5.  To stop the application, you can either click the **"Stop AI-Pal"** button in the app window or simply close the window, which will also shut down the containers.
   
## macOS Desktop App (Easy Install)

This method uses a Terminal script to install all dependencies (Homebrew, Git, Docker Desktop, Python) and create a simple macOS application to launch AI-Pal.

### Installation

1.  **Download the Installer Script:**
    * **[Install_AI_Pal_App.sh](https://raw.githubusercontent.com/caseymrobbins/ai-pal/refs/heads/main/Install_AI_Pal_App.sh)**
    * **Important:** Right-click the link and select **"Save as..."** or **"Save link as..."** to download the `Install_AI_Pal_App.sh` file. Save it to your `Downloads` folder.

2.  **Open the Terminal:**
    * Go to `Applications` > `Utilities` > `Terminal.app`.
    * Alternatively, press `Cmd + Space`, type `Terminal`, and press Enter.

3.  **Navigate to the Script and Run It:**
    * First, change to your Downloads folder:
        ```bash
        cd ~/Downloads
        ```
    * Next, make the script executable:
        ```bash
        chmod +x Install_AI_Pal_App.sh
        ```
    * Now, run the script:
        ```bash
        ./Install_AI_Pal_App.sh
        ```

4.  **Follow the On-Screen Prompts:**
    * The script will first check for **Homebrew**. If you don't have it, it will ask for your password to install it. This is safe and necessary.
    * It will then use Homebrew to install Docker Desktop, Git, and Python. This may take several minutes.
    * Approve any prompts from Docker as it installs.
    * When prompted in the terminal, enter your `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`. You can press Enter to skip either key.
    * The script will clone the repository and create a new **"AI-Pal.app"** application on your Desktop.

### How to Start AI-Pal

1.  After the script is finished, find the new **"AI-Pal"** app on your desktop (it looks like a gray AppleScript icon).
2.  Double-click the "AI-Pal" app to open it.
3.  A small application window will open. Click the **"Start AI-Pal"** button inside this window.
4.  The app will automatically start Docker Desktop in the background (if it's not already running) and wait for it to be ready. It will then build and launch the AI-Pal containers.
5.  Once the server is running, the window will automatically load the AI-Pal interface (http://localhost:8000).
6.  To stop the application, you can either click the **"Stop AI-Pal"** button in the app window or simply close the window, which will also shut down the containers.


### Manual Quick Start Guide

```bash
# Clone the repository
git clone git@github.com:caseymrobbins/ai-pal.git
cd ai-pal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment configuration
cp .env.example .env

# Edit .env with your preferences (API keys optional)
nano .env

# Download spaCy model for PII detection
python -m spacy download en_core_web_lg

# Initialize database
ai-pal init

# Run the system
ai-pal start
```

### Hardware-Specific Setup

**For GPU users (NVIDIA):**
```bash
pip install -e . --extra-index-url https://download.pytorch.org/whl/cu118
```

**For Apple Silicon (M1/M2/M3):**
```bash
# PyTorch with Metal acceleration
pip install -e .
# MPS backend will be automatically detected
```

**For CPU-only:**
```bash
pip install -e .
# System will optimize for CPU execution
```

## 🎯 Usage

### Command Line Interface

```bash
# Start interactive session
ai-pal chat

# Run with specific module
ai-pal chat --module echo-chamber-buster

# Check system status
ai-pal status

# View agency metrics
ai-pal metrics --agency

# Run dream processing manually
ai-pal dream --duration 30

# Export your data
ai-pal export --format json --output my_data.json

# Check Four Gates status
ai-pal ethics-check
```

### Python API

```python
from ai_pal import Orchestrator, EthicsModule

# Initialize orchestrator
orchestrator = Orchestrator()

# Make a request (automatically scrubbed for PII)
response = await orchestrator.process(
    "Help me prepare for my job interview at TechCorp"
)

# Check agency impact
ethics = EthicsModule()
agency_delta = await ethics.measure_agency_impact(
    action="provide_interview_prep",
    context={"user_id": "anonymous"}
)

print(f"Agency Delta: {agency_delta}")  # Should be ≥ 0
```

### API Server

```bash
# Start API server
ai-pal serve --host 0.0.0.0 --port 8000

# Access interactive docs at http://localhost:8000/docs
```

Example API request:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I learn next?",
    "context": {"current_skills": ["python", "react"]}
  }'
```

## 🔧 Configuration

### Local Model Selection

AI Pal automatically detects your hardware and selects the best local model. You can override this:

```bash
# List available models
ai-pal models list

# Download a specific model
ai-pal models download mistral-7b-instruct

# Set default model
ai-pal config set default_model mistral-7b-instruct
```

### Module Configuration

Enable/disable modules in `.env`:

```bash
ENABLE_ETHICS_MODULE=true       # Required - cannot disable
ENABLE_ECHO_CHAMBER_BUSTER=true
ENABLE_LEARNING_MODULE=true
ENABLE_DREAM_MODULE=true
ENABLE_PERSONAL_DATA_MODULE=true
```

### Privacy Controls

```bash
# PII scrubbing (highly recommended)
ENABLE_PII_SCRUBBING=true

# What gets scrubbed:
# - Names, emails, phone numbers
# - Addresses, SSN, credit cards
# - IP addresses, API keys
# - Custom patterns (configurable)

# Data retention
MAX_HISTORY_DAYS=90

# Local-only mode (no cloud APIs)
LOCAL_ONLY_MODE=true
```

## 📊 Agency Metrics Dashboard

AI Pal tracks how it affects your autonomy:

```bash
ai-pal dashboard
```

Key metrics:
- **ΔAgency**: Net change in your agency (must be ≥ 0)
- **Task Efficacy**: How well you can accomplish tasks
- **Opportunity Expansion**: New capabilities unlocked
- **Autonomy Retention Index**: Decision-making independence
- **Epistemic Debt**: Information quality score
- **BHIR**: Beyond-Horizon Impact Ratio

## 🛡️ Ethics & Safety

### The Four Gates

Every significant action must pass all four gates:

1. **Net-Agency Test**: ✅ Aggregate ΔAgency ≥ 0, subgroup floors hold
2. **Extraction Test**: ❌ Fail if dark patterns, lock-ins, or deceptive practices detected
3. **Humanity Override**: ✅ Real appeals process with authority to override
4. **Non-Othering Test**: ✅ Floor parity for all groups, no dehumanizing outputs

### Circuit Breakers

Automatic shutdowns if:
- Agency floors breached for any subgroup
- Epistemic debt enters "red" zone twice
- Beyond-Horizon Impact Ratio ≤ 1
- Goodhart Divergence alarm triggered twice
- Post-audit Extraction or Non-Othering failure

System automatically rolls back to last validated safe version.

### Humanity Override

You can always override AI decisions:

```bash
ai-pal override --action <action_id> --reason "your reason"
```

The system learns from overrides and updates its decision-making to prevent future issues.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_pal --cov-report=html

# Run specific test suite
pytest tests/test_ethics_module.py

# Run Four Gates validation
pytest tests/test_four_gates.py -v
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key areas needing help:
- Additional LLM provider integrations
- Module development
- VARK learning style detection improvements
- Multi-language PII detection
- Mobile/tablet interfaces

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built on the Agency Calculus for AI (AC-AI) framework
- Inspired by principles of Constitutional AI
- PII detection powered by Microsoft Presidio
- Local LLM support via Hugging Face Transformers

## 📚 Documentation

Full documentation available at [docs/](docs/):

- [Architecture Guide](docs/architecture.md)
- [Module Development](docs/module-development.md)
- [AC-AI Framework Implementation](docs/ac-ai-framework.md)
- [Privacy & Security](docs/privacy-security.md)
- [API Reference](docs/api-reference.md)

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ai-pal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai-pal/discussions)
- **Security**: Report vulnerabilities to security@aipal.dev

## 🗺️ Roadmap

- [x] Phase 1: Core infrastructure and orchestrator
- [x] Phase 2: Ethics module and Four Gates
- [x] Phase 3: Basic modules (Echo Buster, Learning)
- [ ] Phase 4: Advanced personalization and fine-tuning
- [ ] Phase 5: Mobile applications
- [ ] Phase 6: Federated learning across instances
- [ ] Phase 7: Advanced dream module capabilities
- [ ] Phase 8: Community module marketplace

---

**Built with ❤️ for human agency and autonomy**
