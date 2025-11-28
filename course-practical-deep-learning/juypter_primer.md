(ty ChatGPT)

# Jupyter Notebook
Jupyter Notebook is basically a mix of a code editor, a word processor, and a lab notebook—all in the browser. This primer walks through the core ideas, following the structure of Jeremy Howard’s **“Jupyter Notebook 101”** notebook on Kaggle (mirrored on CoCalc/GitHub). ([CoCalc][1])

---

## 1. What *is* a Jupyter Notebook?

A **notebook** is a document made of **cells**:

* **Code cells** – where you write and run code (e.g. Python).
* **Markdown cells** – where you write formatted text, explanations, images, etc. ([CoCalc][1])

You run code in a cell (for example `1+1`) and the **output appears right below it**, and stays there when you save the notebook. That makes notebooks perfect for experiments, reports, tutorials, and demos: code, reasoning, and results all live in one place.

---

## 2. Basic Workflow: Editing & Running Cells

### Creating cells

Most notebook UIs (Kaggle, JupyterLab, VS Code, etc.) have buttons like:

* **“+ Code”** – add a new code cell
* **“+ Markdown”** – add a new markdown cell ([CoCalc][1])

You can:

1. Click **+ Markdown** and type:
   `My first markdown cell`
2. Run the cell (see shortcuts below) to render it as formatted text.
3. Click **+ Code**, type `3/2`, run it, and you’ll see `1.5` appear as output.

### Running cells & moving around

In Jupyter, a few keyboard actions are used constantly: ([CoCalc][1])

* **Shift + Enter** – run the current cell and move to the next
* **Up / Down arrows** – move selection between cells
* **b** (in command mode) – create a new cell *below*
* **0 then 0** (zero twice) – restart the kernel (the Python process)

You’ll see a label like `In [1]:` next to code cells and an output section `Out [1]:` below them.

---

## 3. Two Modes: Command Mode vs Edit Mode

This is a *big* Jupyter concept.

* **Edit Mode** – you’re editing the *contents* of a cell
* **Command Mode** – you’re manipulating *cells* (add/delete, move, convert types, etc.) ([CoCalc][1])

How to tell:

* **Green border** → Edit Mode (you can type inside the cell)
* **Blue border** → Command Mode (cell is selected, not being edited)

How to switch:

* **Enter** – go from Command → Edit
* **Esc** – go from Edit → Command

Many shortcuts only work in **Command Mode**.

---

## 4. Markdown Cells: Writing Text, Headings, Lists, and Images

### Switching to Markdown

* Select a cell, then:

  * Use the dropdown (Code → Markdown), **or**
  * In Command Mode, press **m** to turn the cell into Markdown. ([CoCalc][1])

### Basic formatting

Some key Markdown patterns: ([CoCalc][1])

* *Italics*: `_text_` or `*text*`
* **Bold**: `__text__` or `**text**`
* `inline code`: `` `code` ``
* Blockquote:

  ```markdown
  > This is a quote
  ```
* Links:

  ```markdown
  [link text](https://example.com)
  ```

### Headings

Use `#` at the start of a line: ([CoCalc][1])

```markdown
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
```

### Lists

Three common list types: ([CoCalc][1])

* **Ordered list**

  ```markdown
  1. First
  2. Second
  3. Third
  ```
* **Unordered list**

  ```markdown
  - Item A
  - Item B
  ```
* **Task list**

  ```markdown
  - [ ] Learn Jupyter
  - [x] Install Python
  ```

### Images

You can insert images in Markdown like this: ([CoCalc][1])

```markdown
![alt text](attachment:image.png)
```

Many UIs also let you paste an image directly into a Markdown cell; they handle the attachment magic for you.

---

## 5. Code Cells: Variables, Output, and Plots

Code cells execute in a live Python session (the **kernel**). For example: ([CoCalc][1])

```python
a = 1
b = a + 1
c = b + a + 1
d = c + b + a + 1
a, b, c, d
```

You’ll see the tuple `(1, 2, 4, 7)` as output.

You can also do plotting inline:

```python
import matplotlib.pyplot as plt

plt.plot([a, b, c, d])
plt.show()
```

With the right setting (see `%matplotlib inline` below), plots and other rich outputs stay *inside* the notebook when you save and share it.

---

## 6. Running Jupyter: Cloud vs Local

From the notebook: ([CoCalc][1])

You can run notebooks:

* In the **cloud** (e.g. Kaggle, GitHub Codespaces, Google Colab, Amazon Sagemaker Studio Lab, Paperspace, etc.)
* **Locally** on your machine via Jupyter Notebook or JupyterLab

Typical local setup:

1. Install [Anaconda] or Python, then:

   ```bash
   pip install jupyter
   ```
2. In a terminal, in the folder where your projects live, run:

   ```bash
   jupyter notebook
   ```
3. A browser tab should open at a URL like `http://localhost:8888`.
   If it doesn’t, copy or CTRL+Click the printed link in the terminal. ([CoCalc][1])

That opens the **Jupyter dashboard**, from which you can create and open notebooks.

---

## 7. Autosave, Kernel Status, and “Is it stuck?”

A few important status cues: ([CoCalc][1])

* **Autosave**: notebooks save automatically every ~120 seconds (exact timing can vary by platform). There’s also usually a **manual save** button.
* **Kernel status**: look for a small circle/icon near the notebook name:

  * **Filled/spinning** → kernel is busy (running code)
  * **Empty/idle** → kernel is ready

If things get weird (long-running cells, stuck state), a common tactic is to **restart the kernel** (`0` then `0` in Command Mode, or use the menu) and re-run cells from the top.

---

## 8. Essential Command-Mode Shortcuts

From the “Shortcuts and Tricks” section: ([CoCalc][1])

In **Command Mode**:

* **m** – convert cell to Markdown
* **y** – convert cell to Code
* **d, d** – delete the selected cell
* **o** – toggle output on/off for a cell
* **Shift + Up / Down** – select multiple cells (then you can run, copy, or merge them together)
* **Shift + M** – merge selected cells

And remember the big three:

* **Esc** – Command Mode
* **Enter** – Edit Mode
* **Shift + Enter** – run cell, go to next

You can always see a full list with **h** (for help) in Command Mode. ([CoCalc][1])

---

## 9. Helpful “In-Cell” Tricks

Jupyter gives you nice tooling to explore code right in the notebook. ([CoCalc][1])

Within a **code cell**:

* `?function_name` – show help/docstring for a function
* `??function_name` – show source code (when available)
* **Shift + Tab** (once) – quick tooltip of parameters
* **Shift + Tab** (3×) – expanded help panel

Example:

```python
?print
```

will open the documentation for Python’s built-in `print` function.

---

## 10. Shell Commands from Inside a Notebook

You can run shell commands by prefixing them with `!`: ([CoCalc][1])

```python
!pwd      # prints the current working directory
!ls       # lists files
!cat file.txt
```

This is especially handy for quick file checks without leaving the notebook UI.

---

## 11. Line Magics: `%timeit`, `%matplotlib inline`, and Friends

**Line magics** are special commands that start with `%` and apply to the rest of the line. Helpful ones from the notebook: ([CoCalc][1])

* `%matplotlib inline`
  Ensures that Matplotlib plots appear *inside* the notebook and are saved with it.

  ```python
  %matplotlib inline
  import matplotlib.pyplot as plt
  ```

* `%timeit`
  Runs an expression many times and prints the average execution time.

  ```python
  %timeit [i + 1 for i in range(1000)]
  ```

There’s also `%debug` to drop into a debugger after an error, so you can inspect variables interactively. ([CoCalc][1])

---

## 12. Where to Go from Here

The original notebook closes by pointing out that there’s an entire book written *as* notebooks, and encouraging you to play, explore shortcuts, and try more advanced tricks. ([CoCalc][1])

If you can:

1. Create Markdown and Code cells
2. Switch between Edit and Command modes
3. Run code, plot simple graphs, and use help popups
4. Restart the kernel and re-run a notebook cleanly

…you’ve basically got the core Jupyter skillset.
