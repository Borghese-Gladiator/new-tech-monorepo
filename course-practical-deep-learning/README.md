# [Practical Deep Learning for Coders](https://course.fast.ai/)
Free course for coders to learn deep learning and machine learning for practical problems

They teach "“top down”: start with complete useful solutions to real world problems, and gradually work down to the basic foundations. Education experts recommend this approach for more effective learning."

## Course Contents
Machine Learning
- create dataset
- train model with dataset
- deploy application to web
  - Hugging Face Space w/ Gradio

## Local - VSCode w/ Notebook setup
- ```
  poetry init
  poetry env use 3.11.13
  poetry run pip install ipykernel
  ```
- VSCode 
  - install Jupyter extension
  - select interpreter and set path
    - run `poetry env info` to get path
- create `.ipynb` file