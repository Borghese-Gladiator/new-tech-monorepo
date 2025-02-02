**01/31/2025**
BrowserUse does not work that well and has problems locally with Ollama

Does NOT Work that Well
- when searching Reddit for a relevant post to "Browser Use", it clicked on a login button and then got stuck on the modal and is unable to X out of it. It tried to search for "Browser Use" on the username field.

Problems with Ollama
- They have examples which is why I'm confused on what I'm doing wrong, but based on the 174 issues (01/31) of other people encountering the same error with a variety of local models (Llama3, DeepSeek-R1, etc.), I believe it's not just me
- > https://github.com/browser-use/browser-use/issues?q=sort%3Aupdated-desc%20is%3Aissue%20state%3Aopen


#  BrowserSource - Open Source ChatGPT Operator
ChatGPT Operator is an AI agent to perform tasks for you using a browser. It costs like $200/month. BrowserUse is the alternative open source version.

> https://apidog.com/blog/how-to-use-deepseek-r1-to-build-an-open-source-chatgpt-operator-alternative/

This article tells you to:
- run DeepSeek locally with Ollama
- run Browser Use

NOTE: Their instructions are a little wrong. I followed the instructinos from the repo instead: [browser-use](https://github.com/browser-use/browser-use) + [docs](https://docs.browser-use.com/quickstart)
- run DeepSeek locally only shows the API call and not the script
- `browser-use` comes as a pip package and does not need to be run from source 

## Steps to Implement
```
poetry init

#==============
#  OLLAMA
#==============
# DEEPSEEK
# For the 7B model (default):
ollama pull deepseek-r1:7b

# For a smaller 1.5B model:
ollama pull deepseek-r1:1.5b

# For larger models like 70B:
ollama pull deepseek-r1:70b

# Distilled specialized versions - Qwen architecture
ollama run deepseek-r1:7b-qwen-distill
# Distilled specialized versions - Llama architecture
ollama run deepseek-r1:70b-llama-distill

# QWEN
ollama pull qwen2.5:latest

#==============
#  Browser Use
#==============
poetry add browser-use
playwright install  # NOTE: this installs playwright globally
```

## Troubleshoooting
- double check poetry environment is created with Python 3.11 or higher!
  - `poetry env info`