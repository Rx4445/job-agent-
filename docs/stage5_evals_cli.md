# Stage 5: Agent Decision Benchmark & Interactive CLI

## Overview
Stage 5 bridges the gap between core backend orchestration and real-world utility:
1. **Agent Decision Benchmark (`eval_agent.py`):** An automated evaluation suite testing agent autonomy, gate accuracy, and gap recall across diverse candidate-job pairs without consuming tokens.
2. **Interactive CLI Copilot (`cli.py`):** An ergonomic terminal interface for live job hunting, supporting interactive terminal pasting, file paths, and headless automated execution.

---

## 1. Agent Decision & Safety Benchmark (`eval_agent.py`)

### Model Evals vs. Agent Decision Evals
- **Model Evals (`eval.py`):** Tests the LLM's comprehension of unstructured text (slow, consumes API quota).
- **Agent Decision Evals (`eval_agent.py`):** Tests the agent's deterministic business logic (matching engine, score thresholds, gate routing, and missing skill extraction). Runs in **0.05 seconds** with **zero Gemini calls**.

### Benchmark Test Bank (5 Scenarios)
1. **High Fit (100% Overlap):** Auto-Approved ($\ge 70\%$). Zero gaps.
2. **Moderate Fit (50% Overlap):** Operator Review Required ($50\%-69\%$). Accurately flags missing skills (`Docker`, `AWS`).
3. **Severe Mismatch (0% Overlap):** Operator Warning ($< 50\%$). Prevents wasteful applications for completely irrelevant disciplines.
4. **Field Pivot with High Technical Skills (75% Overlap):** Auto-Approved. Verifies that technical skill overlap overrides differing degree titles.
5. **Single Critical Missing Requirement (75% Overlap):** Auto-Approved with gap tracking. Flags `Kubernetes` as missing requirement.

### Benchmark Results
```text
Decision Gate Accuracy: 5/5 (100.0%)
Skill Gap Recall:       5/5 (100.0%)
Total Latency:          < 0.01s
```

---

## 2. Interactive Job Hunter CLI (`cli.py`)

### Usage Modes

#### A. Interactive Multiline Paste (Default)
```powershell
python cli.py
```
Prompts the user to paste job text directly into the terminal, concluding with `END` on a new line.

#### B. Direct File Input
```powershell
python cli.py --file path/to/job_posting.txt
```

#### C. Headless / Automated Mode
```powershell
python cli.py --file path/to/job_posting.txt --non-interactive
```
Automatically follows recommendation thresholds without pausing for console input.

---

## 3. Verification & Test Suite

Run the full project test suite:
```powershell
python -m unittest discover
```
- **46 unit tests passing** across 7 modules (`test_extract.py`, `test_resume.py`, `test_matcher.py`, `test_generator.py`, `test_main.py`, `test_agent.py`, `test_db.py`, `test_cli.py`) in ~0.71 seconds.

Run the decision benchmark:
```powershell
python eval_agent.py
```
