# LLM Behaviour Control Experiments

This folder contains experiments for building a **basic Gradio UI** to interact with a small GGUF LLM model (Phi-3).  
It focuses on understanding and controlling the model’s **response behaviour** through parameters like **temperature**, **top-k**, and **top-p sampling**.

---

## Model Setup

The experiments use the **Phi-3 mini 4k instruct GGUF model**:

---
# Download the model
!wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf -O phi3.gguf
---

# Key Parameters
# 1. Temperature
Controls randomness in responses.

* Low (0.0–0.3): Deterministic, safe, reliable. Ideal for coding, math, or factual answers.

* Medium (0.5–0.8): Balanced creativity and accuracy.

* High (1.0–1.5): Creative, unpredictable, sometimes nonsensical but occasionally insightful.

Internal Mechanism:
Temperature scales the model’s logits before converting to probabilities. Lower temperature = sharper probability distribution (less randomness), higher temperature = flatter distribution (more randomness).

# 2. Top-K Sampling
Selects the next token from the top K most probable tokens.

* Low K (10–50): Conservative, safe.

* Medium K (50–200): Balanced generation.

* High K (500+): Closer to fully random sampling.

Purpose: Prevents rare or low-probability words from appearing unexpectedly.

# 3. Top-P (Nucleus Sampling)
Selects tokens from the smallest set whose cumulative probability ≥ P.

* Low P (0.7–0.8): Conservative.

* Medium P (0.9): Balanced.

* High P (0.95–1.0): More open-ended, creative.

Advantage over Top-K: Adaptive selection based on context rather than a fixed token count.

**Classic Parameter Setups**

Style	Temperature	Top-P	Top-K	Use Case.

Deterministic / Formal	0.1	1.0	0	Coding, math, factual responses.

Smart Creative	0.7	0.9	50	Brainstorming, content generation
Maximum Creativity	1.2	0.95	200	Highly creative, experimental outputs
Controlled but Natural	0.5	0.9	40	Balanced and conversational responses

Folder Contents
gradio_ui.ipynb — Notebook demonstrating a basic interactive Gradio interface.

Additional notebooks (if any) with variations on temperature, top-k, and top-p settings.

# How to Run
1- Open the notebook in Google Colab.

2- Ensure the model phi3.gguf is downloaded in the working directory.

3- Run the cells sequentially to launch the Gradio interface and test different behaviour controls.

4- Adjust temperature, top-k, and top-p sliders to explore different response behaviours.

# Notes
Experiments are exploratory and designed for learning and demonstration.

Not intended for production use.

Frequent updates will add new notebooks and parameter experiments.

Fine-tuning the balance between randomness and creativity can dramatically change the quality and style of responses. Experiment, observe, and iterate!

