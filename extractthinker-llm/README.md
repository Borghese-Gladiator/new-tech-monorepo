# WARNING: Following script is NOT TESTED and likely does NOT WORK!

ExtractThinker is a flexible document intelligence tool that leverages Large Language Models (LLMs) to extract and classify structured data from documents, functioning like an ORM for seamless document processing workflows.

Here we use ExtractThinker as an open-source framewok to orchestrate OCR, classification, and data extraction pipelines for LLMs.

This repo is a **fully on-premise Document Intelligence Solution** via:
- ExtractThinker - open-source framewok to orchestrate OCR, classification, and data extraction pipelines for LLMs
- Ollama - run local models
- Docling (advanced) OR MarkItDown (simple) - document parsing

## Problem Statement
Frontier models are excessively difficult to run on-premise which is REQUIRED for banks and financial institutions.

In order to take advantage of this, organizations can build on-premise or Small Language Model (SLM) setups to keep data in-house and maintaing compliance with GDPR, HIPAAA, or other financial directives.

## Solutions
1. LLMs in local - On-Premise Document Intelligence Solution
  - An on-premise Document Intelligence Solution addresses this by keeping all data on-premise and never pushing it to the cloud.
2. LLMs in cloud - PII Masking pipeline
  - PII masking pipeline runs tools like Presidio to automatically detect and redact personal identifiers before sending to the LLM which lets you remain model-agnostic and maintain compliance

## Steps to Build
- `pip install extract-thinker`
- `pip install markdown-it-py`

1. pick model - text vs vision
2. process documents
3. run local model
4. split documents lazily (avoid exceeding model's input capacity)

# Resources
> https://pub.towardsai.net/building-an-on-premise-document-intelligence-stack-with-docling-ollama-phi-4-extractthinker-6ab60b495751

Alternatives to Ollama
- LocalAI - mimic OpenAI's API locally and can run Llama2 or Mistral via simple endpoint
- OpenLLM - same as above, but optimized for throughput and low latency
- LLama.cpp - lower-level approach to run Llama models w/ custom configurations. Great for granular control or HPC setups, but more complex

