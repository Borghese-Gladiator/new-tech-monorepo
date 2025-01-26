# ExtractThinker
ExtractThinker is a flexible document intelligence tool that leverages Large Language Models (LLMs) to extract and classify structured data from documents, functioning like an ORM for seamless document processing workflows.

## Steps
- `poetry add extract-thinker`
- `poetry add pypdf`

## Features
- Basic Extraction of Fields
- Classification
- Splitting Files - split a document and extract data based on classifications
- Batch Processing - asynchronous processing
- Local LLM Integration (Ollama)

## How It Works
Modular architecture like LangChain

- Document Loaders: Responsible for loading and preprocessing documents from various sources and formats.
- Extractors: Orchestrate the interaction between the document loaders and LLMs to extract - structured data.
- Splitters: Implement strategies to split documents into manageable chunks for processing.
Contracts: Define the expected structure of the extracted data using Pydantic models.
- Classifications: Classify documents or document sections to apply appropriate extraction contracts.
- Processes: Manage the workflow of loading, classifying, splitting, and extracting data from documents.

## Troubleshooting
ERROR: error when running `main.py`
```
C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\pydantic\_internal\_config.py:345: UserWarning: Valid config keys have changed in V2:
* 'fields' has been removed
  warnings.warn(message, UserWarning)
Traceback (most recent call last):
  File "C:\Users\Timot\Documents\GitHub\new-tech-monorepo\extractthinker-first\main.py", line 2, in <module>
    from extract_thinker import Extractor, DocumentLoaderPyPdf, Contract
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\extract_thinker\__init__.py", line 2, in <module>
    from .extractor import Extractor
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\extract_thinker\extractor.py", line 9, in <module>
    from extract_thinker.document_loader.document_loader import DocumentLoader
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\extract_thinker\document_loader\document_loader.py", line 9, in <module>
    import magic
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\magic\__init__.py", line 209, in <module>
    libmagic = loader.load_lib()
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\magic\loader.py", line 49, in load_lib
    raise ImportError('failed to find libmagic.  Check your installation')
ImportError: failed to find libmagic.  Check your installation
```
SOLUTION - install missing dependency `python-magic` used for libmagic file type identification -> https://github.com/Yelp/elastalert/issues/1927
- `pip install python-magic-bin==0.4.14`

<details>
<summary> Failed Steps</summary>

- `poetry add python-magic`
- 64-bit - `pip install python_magic_bin-0.4.14-py2.py3-none-win_amd64.whl`
- 32-bit - `pip install python_magic_bin-0.4.14-py2.py3-none-win32.whl`

</summary>


ERROR: error when running `main.py`
```
Traceback (most recent call last):
  File "C:\Users\Timot\Documents\GitHub\new-tech-monorepo\extractthinker-first\main.py", line 66, in <module>
    result = extractor.classify(
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\extract_thinker\extractor.py", line 589, in classify
    document_loader = self.get_document_loader_for_file(input)
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\extract_thinker\extractor.py", line 81, in get_document_loader_for_file
    raise ValueError("No suitable document loader found for the input.")
ValueError: No suitable document loader found for the input.
```
SOLUTION: Double check the document loader is actually set. Mine was not set though I thought I had run: `extractor.load_document_loader(document_loader)`
```
print("BEFORE", extractor.document_loader)
extractor.load_document_loader(document_loader)
print("AFTER", extractor.document_loader)

print("DOCUMENT LOADER: ", extractor.document_loader)
print("Loaders by File Type", extractor.document_loaders_by_file_type)
print("LLM: ", extractor.llm)
```


# Thoughts
Classifying doesn't work too well, but feature extraction si very good.

Error from Classification that I couldn't fix after fiddling with pydantic model + contract naming
```
Traceback (most recent call last):
  File "C:\Users\Timot\Documents\GitHub\new-tech-monorepo\extractthinker-first\main.py", line 90, in <module>
    classification: CVContract | JobOfferContract = extractor.classify(
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\extract_thinker\extractor.py", line 604, in classify
    return self._classify(content, classifications)
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\extract_thinker\extractor.py", line 344, in _classify
    return self._classify_text_only(content, classifications)
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\extract_thinker\extractor.py", line 555, in _classify_text_only
    response = self.llm.request(messages, ClassificationResponseInternal)
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\extract_thinker\llm.py", line 35, in request
    response = self.client.chat.completions.create(
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\instructor\client.py", line 176, in create
    return self.create_fn(
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\instructor\patch.py", line 193, in new_create_sync
    response = retry_sync(
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\extractthinker-first-Gm5UC3-z-py3.10\lib\site-packages\instructor\retry.py", line 181, in retry_sync
    raise InstructorRetryException(
instructor.exceptions.InstructorRetryException: 1 validation error for ClassificationResponseInternal
  Invalid JSON: trailing characters at line 4 column 6 [type=json_invalid, input_value='{\n        "name": "Job ... "confidence": 8\n    }', input_type=str]
    For further information visit https://errors.pydantic.dev/2.10/v/json_invalid
```