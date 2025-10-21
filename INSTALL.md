# AI Pal Installation Guide

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ai-pal.git
cd ai-pal

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Set up configuration
cp .env.example .env
# Edit .env with your preferences

# 5. Download spaCy model for PII detection
python -m spacy download en_core_web_lg

# 6. Initialize AI Pal
ai-pal init

# 7. Start using AI Pal!
ai-pal chat
```

## Detailed Installation

### Prerequisites

- **Python 3.9+** (required)
- **8GB+ RAM** (16GB+ recommended for local models)
- **CUDA-compatible GPU** (optional, for faster local model inference)
- **10GB+ free disk space** (for local models)

### System-Specific Setup

#### Ubuntu/Debian Linux

```bash
# Install Python and dependencies
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip

# For GPU support (NVIDIA)
# Follow https://docs.nvidia.com/cuda/cuda-installation-guide-linux/

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install AI Pal
pip install -e .
```

#### macOS

```bash
# Install Python (via Homebrew)
brew install python@3.9

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install AI Pal
pip install -e .

# For Apple Silicon (M1/M2/M3), PyTorch will automatically use Metal acceleration
```

#### Windows

```powershell
# Install Python from python.org (3.9+)

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install AI Pal
pip install -e .

# For GPU support (NVIDIA)
pip install torch --extra-index-url https://download.pytorch.org/whl/cu118
```

### GPU Acceleration

#### NVIDIA GPU (CUDA)

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA-enabled PyTorch (if needed)
pip install torch --extra-index-url https://download.pytorch.org/whl/cu118
```

#### AMD GPU (ROCm)

```bash
# Follow ROCm installation guide: https://docs.amd.com/
pip install torch --extra-index-url https://download.pytorch.org/whl/rocm5.6
```

#### Apple Silicon (M1/M2/M3)

Metal acceleration is automatically enabled with standard PyTorch installation.

```bash
# Check MPS availability
python -c "import torch; print(torch.backends.mps.is_available())"
```

### Configuration

#### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required (choose one):
# Option 1: Cloud API (requires API keys)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Option 2: Local models (download models first)
DEFAULT_LOCAL_MODEL=mistralai/Mistral-7B-Instruct-v0.2
LOCAL_MODELS_PATH=./models

# Privacy settings (recommended)
ENABLE_PII_SCRUBBING=true
LOCAL_ONLY_MODE=false  # Set to true to never use cloud APIs

# Ethics settings (required)
ENABLE_FOUR_GATES=true  # Cannot be disabled
MIN_AGENCY_DELTA=0.0
```

#### Download Local Models

To use local models without cloud APIs:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# Example: Download Mistral-7B
model_name = "mistralai/Mistral-7B-Instruct-v0.2"
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Save to local directory
model.save_pretrained("./models/mistral-7b-instruct")
tokenizer.save_pretrained("./models/mistral-7b-instruct")
```

Or use the CLI (future feature):
```bash
ai-pal models download mistral-7b-instruct
```

### Verify Installation

```bash
# Check system info
ai-pal info

# Check status
ai-pal status

# Run basic health check
python examples/basic_usage.py
```

Expected output:
```
AI Pal - Basic Usage Example

1. Initializing orchestrator...
   ✓ Orchestrator initialized

2. Making a request...
   Response: [AI response here]
   Model used: local:mistral-7b-instruct
   Processing time: 1234ms
   PII scrubbed: true
   ...
```

## Troubleshooting

### Common Issues

#### "No module named 'ai_pal'"

**Solution:**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in editable mode
pip install -e .
```

#### "CUDA out of memory"

**Solution:**
```bash
# Reduce max GPU memory usage in .env
MAX_GPU_MEMORY=0.5  # Use only 50% of VRAM

# Or use quantization (add to .env)
# Smaller models will automatically use 8-bit or 4-bit quantization
```

#### "PII detection errors"

**Solution:**
```bash
# Install required spaCy model
python -m spacy download en_core_web_lg

# Or disable PII scrubbing temporarily
ENABLE_PII_SCRUBBING=false  # Not recommended for production
```

#### "Local model not found"

**Solution:**
```bash
# Check model path
ls -la ./models/

# Download model using transformers
python -c "from transformers import AutoModel; AutoModel.from_pretrained('model_name')"

# Or use cloud APIs temporarily
OPENAI_API_KEY=your_key_here
```

### Getting Help

- **Documentation**: See [docs/](docs/) for detailed guides
- **Examples**: Check [examples/](examples/) for usage examples
- **Issues**: Report bugs at [GitHub Issues](https://github.com/yourusername/ai-pal/issues)
- **Discussions**: Ask questions at [GitHub Discussions](https://github.com/yourusername/ai-pal/discussions)

## Next Steps

After installation:

1. **Read the documentation**: [docs/architecture.md](docs/architecture.md)
2. **Try the examples**: `python examples/basic_usage.py`
3. **Start chatting**: `ai-pal chat`
4. **Customize**: Edit `.env` and configure modules
5. **Explore modules**: Try Echo Chamber Buster, Learning Module, etc.

## Development Installation

For contributors:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linters
black src/
ruff check src/
mypy src/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development guide.
