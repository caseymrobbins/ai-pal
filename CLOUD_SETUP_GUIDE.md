# Cloud LLM Setup Guide

Quick setup guide for using cloud AI models with AI-PAL.

## Supported Providers

AI-PAL now supports **4 cloud providers**:

| Provider | Models | Best For | Cost (per 1M tokens) |
|----------|--------|----------|---------------------|
| **Google Gemini** | gemini-1.5-flash, gemini-1.5-pro, gemini-pro | Fast, cheap, vision | $0.075/$0.30 (Flash) ⭐ |
| **Anthropic (Claude)** | claude-3-opus, claude-3-haiku | Privacy, quality | $15/$75 (Opus), $0.25/$1.25 (Haiku) |
| **OpenAI** | gpt-4-turbo, gpt-3.5-turbo | General purpose | $10/$30 (GPT-4), $0.50/$1.50 (GPT-3.5) |
| **Cohere** | command | Specialized tasks | Varies |

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

### Option 3: OpenAI (GPT-4/GPT-3.5)

**Setup:**

```bash
export OPENAI_API_KEY="sk-your-key-here"
ai-pal chat
```

## Make It Permanent

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# Google Gemini (fastest, cheapest)
export GOOGLE_API_KEY="your-key-here"

# Anthropic Claude (best for coding)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# OpenAI (optional)
export OPENAI_API_KEY="sk-your-key-here"
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

2. **Tries Gemini Flash** - $0.075/$0.30 per 1M tokens ⭐
   - If works: ✓ Uses Gemini
   - If fails (no API key): ↓ Falls back

3. **Tries Claude Haiku** - $0.25/$1.25 per 1M tokens
   - If works: ✓ Uses Claude
   - If fails: ↓ Falls back

4. **Tries GPT-3.5** - $0.50/$1.50 per 1M tokens
   - If works: ✓ Uses GPT
   - If fails: ↓ Falls back

5. **Tries Gemini Pro** - Backup option
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
| Gemini Flash only | 50K | ~$0.02 | ~$0.60 |
| Claude Haiku only | 50K | ~$0.06 | ~$1.80 |
| GPT-3.5 only | 50K | ~$0.10 | ~$3.00 |
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

```bash
# Use Gemini as primary (you pay for it anyway!)
export GOOGLE_API_KEY="your-gemini-key"

# Use Claude as backup (you know me!)
export ANTHROPIC_API_KEY="your-claude-key"

# Chat works immediately, no downloads needed
ai-pal chat
```

**This gives you:**
- ✓ Zero memory usage
- ✓ Fast responses (~600ms)
- ✓ Cheap ($0.02/day typical)
- ✓ Self-repair works
- ✓ Automatic fallback
- ✓ Best quality for complex tasks

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

**Google Gemini:**
- Free tier: 60 requests/minute
- Plenty for personal use!

**Anthropic Claude:**
- $5 free credit on signup
- ~20K-50K tokens free

**OpenAI:**
- $5 free credit on signup
- ~3M tokens (GPT-3.5)

## Privacy Comparison

| Provider | Trains on Data | Retention | Best For |
|----------|----------------|-----------|----------|
| Local | Never | 0 days | Maximum privacy |
| Anthropic | No (paid tier) | 0 days | High privacy |
| Google | No (paid tier) | 18 months | Balanced |
| OpenAI | No (API) | 30 days | General use |

## Next Steps

1. **Set up Gemini** (since you pay for it!)
2. **Set up Claude** (since you like me!)
3. **Test it:** `ai-pal chat`
4. **Optional:** Download TinyLlama for offline use later

**You're ready to go!** 🚀

The system will automatically:
- Use cheapest capable model
- Upgrade for complex tasks
- Fall back if one fails
- Track costs and performance

Just chat and let AI-PAL handle the rest!
