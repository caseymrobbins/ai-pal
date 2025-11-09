# Cloud LLM Setup Guide

Quick setup guide for using cloud AI models with AI-PAL.

## Supported Providers

AI-PAL now supports **7 cloud providers**:

| Provider | Models | Best For | Cost (per 1M tokens) |
|----------|--------|----------|---------------------|
| **Groq** ⚡ | llama-3.1-8b-instant, mixtral-8x7b | Ultra-fast inference | $0.05/$0.10 (8B) 🔥 |
| **Google Gemini** | gemini-1.5-flash, gemini-1.5-pro | Fast, cheap, vision | $0.075/$0.30 (Flash) ⭐ |
| **Anthropic (Claude)** | claude-3.5-sonnet, claude-3-opus, claude-3-haiku | Privacy, quality, coding | $3/$15 (Sonnet), $0.25/$1.25 (Haiku) |
| **OpenAI** | gpt-4-turbo, gpt-3.5-turbo | General purpose | $10/$30 (GPT-4), $0.50/$1.50 (GPT-3.5) |
| **Cohere** | command-r-plus, command-r | RAG, multilingual | $3/$15 (R+), $0.50/$1.50 (R) |
| **Mistral AI** | mistral-large, mistral-small | European data, coding | $4/$12 (Large), $1/$3 (Small) |
| **Local** | phi-2, tinyllama | Privacy, offline | $0 (FREE) |

## Quick Setup (For 8GB MacBook Air)

### Option 1: Google Gemini (Recommended - You Already Pay For This!)

**Why Gemini for you:**
- ✓ You already pay for it
- ✓ Cheapest option ($0.075 per 1M tokens)
- ✓ Fastest cloud model (600ms latency)
- ✓ Zero memory usage on your Mac
- ✓ Great quality

**Setup (30 seconds):**

1. **Get your API key:**
   - Go to: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy the key

2. **Set environment variable:**
   ```bash
   export GOOGLE_API_KEY="your-key-here"
   ```

3. **Done! Just chat:**
   ```bash
   ai-pal chat
   ```

### Option 2: Anthropic Claude (Recommended - You Use Me!)

**Why Claude:**
- ✓ You're already talking to me (Claude)!
- ✓ Great at coding and analysis
- ✓ Privacy-focused (doesn't train on your data)
- ✓ Haiku is cheap ($0.25/$1.25 per 1M tokens)

**Setup:**

1. **Get API key:**
   - Go to: https://console.anthropic.com
   - Create account (if needed)
   - Get $5 free credit!
   - Generate API key

2. **Set environment variable:**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```

3. **Chat:**
   ```bash
   ai-pal chat
   ```

### Option 3: Groq (Blazing Fast - Free Tier!)

**Why Groq:**
- ✓ FREE tier with generous limits
- ✓ ULTRA-FAST (100-150ms latency!)
- ✓ Cheapest paid option ($0.05/$0.10 per 1M tokens)
- ✓ Great for rapid prototyping

**Setup:**

1. **Get API key:**
   - Go to: https://console.groq.com
   - Create account (free!)
   - Generate API key

2. **Set environment variable:**
   ```bash
   export GROQ_API_KEY="gsk-your-key-here"
   ```

3. **Chat:**
   ```bash
   ai-pal chat
   ```

### Option 4: OpenAI (GPT-4/GPT-3.5)

**Setup:**

```bash
export OPENAI_API_KEY="sk-your-key-here"
ai-pal chat
```

### Option 5: Cohere (RAG & Multilingual)

**Setup:**

```bash
export COHERE_API_KEY="your-key-here"
ai-pal chat
```

Get key at: https://dashboard.cohere.com/api-keys

### Option 6: Mistral AI (European, Privacy-Focused)

**Setup:**

```bash
export MISTRAL_API_KEY="your-key-here"
ai-pal chat
```

Get key at: https://console.mistral.ai/

## Make It Permanent

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# Groq (ultra-fast, free tier)
export GROQ_API_KEY="gsk-your-key-here"

# Google Gemini (fast, cheap)
export GOOGLE_API_KEY="your-key-here"

# Anthropic Claude (best for coding)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# OpenAI (optional)
export OPENAI_API_KEY="sk-your-key-here"

# Cohere (optional - RAG, multilingual)
export COHERE_API_KEY="your-key-here"

# Mistral AI (optional - European)
export MISTRAL_API_KEY="your-key-here"
```

Then reload:
```bash
source ~/.zshrc  # or ~/.bashrc
```

## How AI-PAL Uses Them

### Intelligent Fallback Chain

**When you run `ai-pal chat`:**

1. **Tries local first** (phi-2, tinyllama) - FREE
   - If works: ✓ Uses local
   - If fails (no RAM/model): ↓ Falls back

2. **Tries Groq Llama 3.1 8B** ⚡ - $0.05/$0.10 per 1M tokens 🔥
   - Ultra-fast (100ms), cheapest!
   - If works: ✓ Uses Groq
   - If fails (no API key): ↓ Falls back

3. **Tries Gemini Flash** - $0.075/$0.30 per 1M tokens ⭐
   - Fast, vision support
   - If works: ✓ Uses Gemini
   - If fails: ↓ Falls back

4. **Tries Cohere Command R** - $0.50/$1.50 per 1M tokens
   - Good for RAG tasks
   - If works: ✓ Uses Cohere
   - If fails: ↓ Falls back

5. **Tries Claude Haiku** - $0.25/$1.25 per 1M tokens
   - Fast, high quality
   - If works: ✓ Uses Claude
   - If fails: ↓ Falls back

6. **Tries Mistral Small** - $1/$3 per 1M tokens
   - European data residency
   - If works: ✓ Uses Mistral
   - If fails: ↓ Falls back

7. **Tries GPT-3.5** - $0.50/$1.50 per 1M tokens
   - Reliable fallback
   - If works: ✓ Uses GPT
   - If fails: ↓ Falls back

8. **Tries Gemini Pro** - Backup option
   - Last resort before giving up

### Task-Based Selection

**Simple chat:**
→ Uses local model (or cheapest cloud if no local)

**Complex tasks** (code generation, analysis):
→ Orchestrator automatically upgrades to:
- Gemini 1.5 Pro
- Claude Opus
- GPT-4 Turbo

You get the best model for the job!

## Cost Estimates

**For typical usage (100 conversations/day, ~500 tokens each):**

| Scenario | Daily Tokens | Daily Cost | Monthly Cost |
|----------|--------------|------------|--------------|
| All local | 50K | $0.00 | $0.00 |
| Groq only | 50K | ~$0.01 | ~$0.30 🔥 |
| Gemini Flash only | 50K | ~$0.02 | ~$0.60 |
| Claude Haiku only | 50K | ~$0.06 | ~$1.80 |
| Cohere Command R | 50K | ~$0.10 | ~$3.00 |
| GPT-3.5 only | 50K | ~$0.10 | ~$3.00 |
| Mistral Small | 50K | ~$0.20 | ~$6.00 |
| Mixed (local + fallback) | 50K | ~$0.01 | ~$0.30 |

**For self-improvement (AI fixing bugs):**
- ~5-10 patches per month
- ~10K tokens per patch
- **Gemini:** ~$0.40/month
- **Claude:** ~$1.25/month
- **GPT-4:** ~$4.00/month

## Testing Your Setup

```bash
# Test that API key works
ai-pal chat

You: hi
AI: [Should respond using cloud model if local fails]

# Check which model was used (shown in output)
# Example: "Model: google/gemini-1.5-flash"
```

## Troubleshooting

### "No API key found"

**Problem:** API key not set

**Solution:**
```bash
# Check if set:
echo $GOOGLE_API_KEY
echo $ANTHROPIC_API_KEY

# If empty, set them:
export GOOGLE_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

### "API key invalid"

**Problem:** Wrong/expired API key

**Solutions:**
1. Check for typos
2. Regenerate key from provider dashboard
3. Check API key format:
   - Google: Usually starts with `AI...`
   - Anthropic: Starts with `sk-ant-`
   - OpenAI: Starts with `sk-`

### "Rate limit exceeded"

**Problem:** Too many requests

**Solutions:**
1. Wait a few minutes
2. Upgrade to paid tier
3. Add multiple providers as fallbacks

## Recommended Setup for You

**Based on your hardware (8GB MacBook Air M1):**

### Best Setup (Free + Paid Mix):

```bash
# Primary: Groq (FREE tier, blazing fast!)
export GROQ_API_KEY="gsk-your-groq-key"

# Backup 1: Gemini (you pay for it anyway!)
export GOOGLE_API_KEY="your-gemini-key"

# Backup 2: Claude (you know me!)
export ANTHROPIC_API_KEY="your-claude-key"

# Chat works immediately, no downloads needed
ai-pal chat
```

**This gives you:**
- ✓ Zero memory usage
- ✓ ULTRA-FAST responses (~100ms with Groq!)
- ✓ Nearly free ($0.01/day typical with free tier)
- ✓ Self-repair works
- ✓ Triple fallback safety
- ✓ Best quality for complex tasks

### Budget-Conscious Setup:

Just use Groq's free tier:
```bash
export GROQ_API_KEY="gsk-your-groq-key"
ai-pal chat
```

**Free tier limits:**
- 14,400 requests/day
- 7,000 requests/minute
- More than enough for personal use!

## Cost Optimization Tips

1. **Set preferred model to cheapest:**
   ```bash
   # Let orchestrator use Gemini Flash for simple tasks
   ai-pal chat  # Automatically uses cheapest capable model
   ```

2. **Use local for simple chat** (when you have time to download):
   - Download TinyLlama (1.1GB, overnight)
   - Use for basic chat (free!)
   - Fallback to cloud for complex tasks

3. **Mix local + cloud:**
   - Simple Q&A → TinyLlama (free, local)
   - Code generation → Gemini Pro (smart upgrade)
   - Deep analysis → Claude Opus (best quality)

## Free Tier Limits

**Groq:** ⭐
- FREE tier: 14,400 requests/day, 7,000 req/min
- Best free tier available!

**Google Gemini:**
- Free tier: 60 requests/minute
- Plenty for personal use!

**Anthropic Claude:**
- $5 free credit on signup
- ~20K-50K tokens free

**OpenAI:**
- $5 free credit on signup
- ~3M tokens (GPT-3.5)

**Cohere:**
- Free trial available
- Limited production use

**Mistral AI:**
- Free trial credits
- Pay-as-you-go thereafter

## Privacy Comparison

| Provider | Trains on Data | Retention | Data Location | Best For |
|----------|----------------|-----------|---------------|----------|
| Local | Never | 0 days | Your Mac | Maximum privacy |
| Anthropic | No (paid tier) | 0 days | US | High privacy, coding |
| Mistral AI | No | 0 days | EU | European data residency |
| Google | No (paid tier) | 18 months | US | Balanced, vision |
| OpenAI | No (API) | 30 days | US | General use |
| Groq | No | 30 days | US | Speed, free tier |
| Cohere | No (paid tier) | 30 days | Multi-region | RAG, multilingual |

## Next Steps

### Quick Start (5 minutes):

1. **Set up Groq** (FREE tier, fastest!)
   ```bash
   # Visit: https://console.groq.com
   # Get API key, then:
   export GROQ_API_KEY="gsk-your-key"
   ```

2. **Set up Gemini** (since you pay for it!)
   ```bash
   export GOOGLE_API_KEY="your-key"
   ```

3. **Test it:**
   ```bash
   pip install -e .  # Install new dependencies
   ai-pal chat
   ```

4. **Optional:** Add Claude as backup (since you like me!)
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key"
   ```

**You're ready to go!** 🚀

The system will automatically:
- Use cheapest capable model
- Upgrade for complex tasks
- Fall back if one fails
- Track costs and performance

Just chat and let AI-PAL handle the rest!
