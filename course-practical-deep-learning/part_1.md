Part 1 is the Core Deep Learning chapters

# Overall
Through "Practical Deep Learning for Coders," I learned about DL topics which are shaping modern AI tools. This website includes links to the textbook chapters, relevant Notebooks on Kaggle/GitHub, tutorials, and code snippet
1. setup
  - Kaggle + Jupyter Notebook usage
2. Deployment of "Cats vs Dogs Recognizer"
  - training (fastai)
  - web app (Gradio)
  - deployment (HuggingFace Spaces)
3. Neural Net foundations
  - train MNIST Digit Classifier
4. Natural Language (NLP)
  - NLP pipelines before DL
  - NLP pipelines today
  - trained Text Generator
  - trained and fine-tuned Review Classifier
5. NN from-scratch model
  - build NN for Titanic Survival prediction
  - build equivalent NN via framework (`fastai`)

## Lesson 1 - setup
https://course.fast.ai/Lessons/lesson1.html

- kaggle account
  - load real datasets
  - free cloud notebooks
    - got an error, not sure how to fix (moving to local)
  - VSCode setup - poetry + Jupyter extension
- Jupyter Notebook
  - https://www.kaggle.com/code/jhoward/jupyter-notebook-101
- resources
  - https://github.com/fastai/course22
    - holds all course notebooks
  - https://github.com/fastai/fastbook
    - free version of below book
  - https://www.amazon.com/Deep-Learning-Coders-fastai-PyTorch-ebook-dp-B08C2KM7NR/dp/B08C2KM7NR

Steps for Local setup
- terminal
  ```
  poetry init
  poetry env use 3.11.13
  poetry add --group dev ipykernel
  ```
- VSCode
  - install Jupyter extension
  - select interpreter and set path
    - run `poetry env info` to get path
- create `.ipynb` file


## Lesson 2 - deep learning deployment of "Cats vs Dogs Recognizer"
https://course.fast.ai/Lessons/lesson2.html

- loaded dataset of Pets from FastAI
- **trained Vision Learner for Cats vs Dogs**
  - FastAI - DL library built on top of PyTorch to simplify training neural networks for specific tasks
  - A ResNet (Residual Network) is a deep neural network architecture introduced by Microsoft Research in 2015. Its key innovation is the residual block, which allows a model to “skip” layers using skip connections (also called shortcut connections).
- **built web app with Gradio**
  - Gradio - build UI for ML models, APIs, and data science workflows
  - Note that for any Gradio interface, there will be an API available which you can see in the "View the API" link at the bottom of the interface
- **deployed web app to Hugging Face Spaces**

Steps to Deploy on Hugging Face Spaces
- Hugging Face UI | click on Profile -> create Space
- setup local
  - install git LFS (Large File Storage)
    ```
    git lfs install
    ```
    - required to handle `model.pkl`
  - install Hugging Face CLI
    ```
    # Make sure the hf CLI is installed
    curl -LsSf https://hf.co/cli/install.sh | bash
    # Download the Space
    hf download chibichomusuke/Cats_vs_Dogs --repo-type=space
    ```
  - pick a directory for where to put the git repo
    ```
    # When prompted for a password, use an access token with write permissions.
    # Generate one from your settings: https://huggingface.co/settings/tokens
    git clone https://huggingface.co/spaces/chibichomusuke/Cats_vs_Dogs
    ```
- inside directory, add the files `app.py`, `requirements.txt`, `export.pkl`, and `README.md` (metadata) files
- after deployment, you can access Gradio web app via API:
  ```python
  r = requests.post(url='https://hf.space/embed/tmabraham/fastai_pet_classifier/+/api/predict/', json={"data":[data]})
  ```

Caveats
- Installation of FastAI comes with PyTorch. That version of PyTorch is CPU only and will NOT be able to utilize local Nvidia GPUs.
- attempt that did not work
  ```
  poetry source add pytorch-repo https://download.pytorch.org/whl/cu121
  poetry add torch --source pytorch-repo
  ```

## Lesson 3 - Digit Classifier
https://course.fast.ai/Lessons/lesson3.html

- Computer Vision - most basic unit is a pixel (set of numbers to describe color and brightness of an individual tiny square on the screen)
- **NumPy Arrays** - multidimensional table of data, with all items of same type
  ```python
  np.array([2, 5])
  ```
  - raw image is array shaped like (height, width, channels)
    - eg: RGB image of (224, 224, 3)
  - batch of images can be (batch_size, height, width, channels)
- **PyTorch Tensors** - same with restrictions
  ```python
  pt.tensor([2, 5])
  ```
  - restrictions
    - must use basic numeric type
    - cannot be jagged
  - additional capabilities
    - can run on GPU
  - Note, the mathematical concept of Tensor which is an abstract concept to generalize scalars, vectors, and matrices and is a little different.
- **Broadcasting**
  - metric - number calculated based on predictions of model and correct labels. Determines how good model is
    ```python
    # calculates "mean absolute error"
    def mnist_distance(a,b): return (a-b).abs().mean((-1,-2))
    ```
    - eg: mean squared error
    - eg: mean absolute error
  - broadcasting - automatically expand tensor with smaller rank to have same size as one with larger rank. This simplifies tensor code
- **Stochastic Gradient Descent (SGD)**
  - weight assessment - way of improving basd on testing effectiveness of weight assessment
  - steps
    - initialization - initial parameter values
    - random selection - pick single training sample at random
    - gradient calculation - compute gradient of loss function for that single sample
    - parameter update - adjust parameters in opposite direction of gradient, scaled by learning rate
    - iteration - repeat 2-4 until desired convergence
  - **backpropagation** - process for calculating derivative of each layer
  - "backward pass" - gradients calcluated
  - "forward pass" - activations calculated 

Digit Classifier
- load dataset
- Pixel Similarity
  - build average "ideal" picture of 3
  - find similarity between validation image and "ideal image"
  - Pros - easy, fast
  - Cons - no learning that enables model to get better and better
- Stochastic Gradient Descent
  - look at each individual pixel and come up with a set of weights for each one, such that highest weights are associated with pixels most likely to be black for that particular category.
  - steps
    - initialize weights
    - iteration
      - use weights to predict 3 or 7
      - calulcate how good model is (loss) based on prediction
      - calculate gradient, for each weight, how changing weight affects loss
      - step (change) all weights based on gradient

## Lesson 4 - Natural Language (NLP)
(PRIMER from ChatGPT)
NLP - enable AI to understand, generate, interact with human language

NLP pipeline (before Deep Learning)
- Tokenization
  - splitting text into pieces (words, subwords, characters)
- Normalization
  - lowercase
  - remove punctuation
  - stemming (connect, connecting -> connect)
  - lemmatization (convert to dictionary form)
- Vectorization
  - bag of words
  - TF-IDF
  - n-grams
- Statistical model
  - naive bayes
  - logistic regression
  - SVMs

NLP DL Advances
- word embeddings
  - word2vec
  - GloVe
  - FastText
  - continuous vectors capture meaning
    - eg: king -> man AND woman -> queen
- RNNs, LSTMs, GRUs - neural architecture to process text sequentially
- Transformer - self-attention
  - advances
    - models can "look" at all words at once
    - easily parallelized
    - handles long contexts better
  - steps
    - tokenization
    - embeddings - tokens -> vectors
    - self-attention - each token looks at all others and weighs importance
    - feedforward layers - nonlinear transformations
    - stacked layers - deeper == smarter
    - output head - predicts next token (GPT) or masked token (BERT)

NLP pipeline (w/ DL)
- pretraining
- fine-tuning - adapt to specific task (eg: classification)
- instruction tuning & RLHF (Reinforcement Learning from Human Feedback)

(Textbook)
- Text Preprocessing
- Tokenization
  ```python
  spacy = WordTokenizer()
  tokens = first(spacy([txt]))
  ```
  - word
  - subword
    - eg: Chinese/Japanese have no spaces
  - character
  - token - one element of a list created by tokenization process
  - special tokens - fastai tokens to make it easier for model to recognize important parts of a sentence
    - `xxbos` - Indicates the beginning of a text (here, a review)
    - `xxmaj` - Indicates the next word begins with a capital (since we lowercased everything)
    - `xxunk` - Indicates the word is unknown
- Numericalization - map tokens to integers, equivalent steps as previous used to create a `Category` variable
  - make list of all possible levels (vocab)
  - replace each level with its index in vocab
- Batching for Language Model (Splitting)
- Training Text Classifier
  - Language Model using `DataBlock`
    ```python
    get_imdb = partial(get_text_files, folders=['train', 'test', 'unsup'])

    dls_lm = DataBlock(
        blocks=TextBlock.from_folder(path, is_lm=True),
        get_items=get_imdb, splitter=RandomSplitter(0.1)
    ).dataloaders(path, path=path, bs=128, seq_len=80)
    ```
  - Fine-Tuning Language Model
    ```python
    learn = language_model_learner(
      dls_lm, AWD_LSTM, drop_mult=0.3, 
      metrics=[accuracy, Perplexity()]).to_fp16()
    ```
    - feed embeddings to RNN using AWD-LSTM (handled automatically in fastai code)
- Text Generation
  ```python
  TEXT = "I liked this movie because"
  N_WORDS = 40
  N_SENTENCES = 2
  preds = [learn.predict(TEXT, N_WORDS, temperature=0.75) 
          for _ in range(N_SENTENCES)]
  ```
- Classifier Fine-Tuning
  - create classifier
    ```python
    dls_clas = DataBlock(
      blocks=(TextBlock.from_folder(path, vocab=dls_lm.vocab),CategoryBlock),
      get_y = parent_label,
      get_items=partial(get_text_files, folders=['train', 'test']),
      splitter=GrandparentSplitter(valid_name='test')
    ).dataloaders(path, path=path, bs=128, seq_len=72)   
    ```
  - fine-tuning
    ```python
    # freezing whole model
    learn.unfreeze()
    learn.fit_one_cycle(2, slice(1e-3/(2.6**4),1e-3))
    ```
    - The last step is to train with discriminative learning rates and gradual unfreezing. In computer vision we often unfreeze the model all at once, but for NLP classifiers, we find that unfreezing a few layers at a time makes a real difference:
- Disinformation and Language Models

Relevant Libraries
- spaCy - NLP library with utilities for tokenization, PoS tagging, named entit recognition, and dependency parsing
- Hugging Face Transformers
- NLTK
- fastai
- PyTorch

Models
- BERT, RoBERTa, DistilBERT
- GPT-style models
- T5 / FLAN
- LlaMA, Mistral, Qwen

## Lesson 5 - NN from-scratch model
How to create a neural network from scratch using Python and PyTorch, and how to implement a training loop for optimising the weights of a model. We build up from a single layer regression model up to a neural net with one hidden layer, and then to a deep learning model. Along the way we’ll also look at how we can use a special function called sigmoid to make binary classification models easier to train, and we’ll also learn about metrics.

(PRIMER from ChatGPT)
- Neural Network steps
  - Initialization (happens once)
  - Forward Pass (happens every iteration)
  - Backward pass + Parameter Update (training only)
- Setup
  - number of layers
  - number of neurons per layer
  - activation functions
  - loss function
  - optimization algorithm
- Initialize parameters
- Forward pass (inference)
- Compute Loss
- Backward Pass (backpropagation)
- Parameter Update (optimization)
  - update weights
- repeats for every mini-batch of inputs

https://www.kaggle.com/code/jhoward/linear-model-and-neural-net-from-scratch
- clean data - tabular data as CSV
  - use `pandas` to squish big numbers (`log`) to make distribution more reasonable
  - replace categorical variables with numbers
- create independent/dependent variables
  ```python
  from torch import tensor
  t_dep = tensor(df.Survived)
  ```
- Setting up linear model
  ```python
  torch.manual_seed(442)

  n_coeff = t_indep.shape[1]
  coeffs = torch.rand(n_coeff)-0.5
  ```
- Training the linear model
  ```python
  def train_model(epochs=30, lr=0.01):
    torch.manual_seed(442)
    coeffs = init_coeffs()
    for i in range(epochs): one_epoch(coeffs, lr=lr)
    return coeffs
  ```
  - `RandomSplitter` - create training/validation sets
  - update coefficients
  - one full gradient descent step
  - initializing `coeffs` to random numbers
- Measuring accuracy
  ```python
  def acc(coeffs): return (val_dep.bool()==(calc_preds(coeffs, val_indep)>0.5)).float().mean()
  ```
  - sigmoid - mathematical function to map real-valued input into value between 0 and 1
    - fixes predictions to be between 0 and 1
- Submit trained model to Kaggle competition!

Tabular Modeling Deep Dive
- Generalization
  - structured data - ensembles of decision trees for structured data
    - `scikit-learn`
  - unstructured data - multilayered neural networks with SGD (shallow or deep learning)
    - `pytorch` / `fastai`
