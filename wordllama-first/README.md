# WordLlama
WordLlama is a fast, lightweight NLP toolkit designed for tasks like fuzzy deduplication, similarity computation, ranking, clustering, and semantic text splitting. It ships with a lightweight LLM.

It recycles components from large language models (LLMs) to create efficient and compact word representations, similar to GloVe, Word2Vec, or FastText.

> WordLlama: Recycled Token Embeddings from Large Language Models

## Methodology
To try out WordLlama, I'm going to use it to preprocess some Climate Change PDFs from [www.pdfdrive.com](www.pdfdrive.com) and save it to FAISS

Steps
- download Climate Change PDFs
- convert PDFs to Text via [PDF2GO](https://www.pdf2go.com/)
  - download texts at [OneDrive Link](https://1drv.ms/f/c/dbd966821cf37bbd/EoDIW4MtHOJLntlolJEribIBx3EaSunSu28GcsHkp7S9Ig?e=eIb0ic)
- preprocess using WordLlama
  - Semantic Text Splitting - split text into semantically coherent chunks
  - Fuzzy Deduplication - remove duplicate texts based on similarity threshold
  - Embedding Text - build embeddings
- save to FAISS vector datastore
  - NOTE: I used LangChain because I'm more familiar with it than the "faiss-cpu" library though it introduces overhead and requires me to convert text into `Document` objects
---
- validate by asking query and using WordLlama Top-K Retrieval
  - "Tell me about Capitalism's relationship to the Climate"

## WordLlama Features
- Embedding Text
- Calculating Similarity
- Ranking Documents
- Fuzzy Deduplication
- Clustering
- Filtering
- Top-K Retrieval
- [Semantic Text Splitting](https://github.com/dleemiller/WordLlama/blob/main/tutorials/blog/semantic_split/wl_semantic_blog.ipynb) - under the hood, WordLlama has an in-depth split to maximize information continuity, keeping related concepts and ideas together instead of naive fixed characters splits
  - requirements
    - Maximize information continuity, keeping related concepts and ideas together
    - Produce consistent chunk sizes
    - Maintain high performance with low computational requirements
  - implementation at a glance
    - split: Divide the original text into small chunks.
    - embed: Generate embeddings for each chunk.
    - reconstruct: Combine chunks based on similarity information up to target sizes

# Note
LangChain
- LangChain has an experimental text splitter to do the same Semantic Text Splitting: [https://python.langchain.com/v0.1/docs/modules/data_connection/document_transformers/](https://python.langchain.com/v0.1/docs/modules/data_connection/document_transformers/)
- LangChain has embedding text utilities

Better Results
- I need to preprocess the PDF text to remove all the non content related text like ISBN numbers, titles, table of contents, page numbers, glossary, indexes, URLs, etc.

<details>
<summary>Results</summary>

```

Top Retrieved Documents:
INFO:httpx:HTTP Request: POST http://127.0.0.1:11434/api/embed "HTTP/1.1 200 OK"
* but it is likely that without it about 75 of the pending 150 new coal fired power plants we stopped wouldhave been built instead.” He added, “What I do regret is the failure at the time to understand the scale andform that the shale gas and oil revolution would take, which led us to make inadequate investments ingetting ready for the assault that would soon be coming at states like Pennsylvania, West Virginia andColorado. That was a significant, and costly, failure of vision.”V. This reached truly absurd levels in December 2013 when two twentysomething antifracking activistswere charged with staging a “terrorism hoax” after they unfurled cloth protest banners at the headquartersof Devon Energy in Oklahoma City. Playing on the Hunger Games slogan, one of the banners said: “THEODDS ARE NEVER IN OUR FAVOR.” Standard, even benign activist fare—except for one detail.According to Oklahoma City Police captain Dexter Nelson, as the banner was lowered it shed a “blackpowder substance” that was meant to mimic a “biochemical assault,” as the police report put it. Thatnefarious powder, the captain stated, was “later determined to be glitter.” Never mind that the video of theevent showed absolutely no concern about the falling glitter from the assembled onlookers. “I could haveswept it up in two minutes if they gave me a broom,” said Stefan Warner, one of those charged and facingthe prospect of up to ten years in jail.


11
YOU AND WHAT ARMY?
Indigenous Rights and the Power of Keeping Our Word [{'title': 'This Changes Everything_ Capitalism vs. The Climate ( PDFDrive ).txt'}]

* Proceedings of the 10th International Modelica Conference, March 10–12, 2014, http://www.ep.liu.se.4. Personal interview with Nerida-Ann Steshia Hubert, March 30, 2012.5. Hermann Joseph Hiery, The Neglected War: The German South Pacific and the Influence of World War I(Honolulu: University of Hawai’i Press, 1995), 116–25, 241; “Nauru,” New Zealand Ministry of ForeignAffairs and Trade, updated December 9, 2013, http://wwww.mfat.govt.nz; “Nauru” (video), NFSA
Australia, NFSA Films.6. Charles J. Hanley, “Tiny Pacific Isle’s Citizens Rich, Fat and Happy—Thanks to the Birds,” AssociatedPress, March 31, 1985; Steshia Hubert interview, March 30, 2012.7. “Country Profile and National Anthem,” Permanent Mission of the Republic of Nauru to the UnitedNations, United Nations, http://www.un.int; Jack Hitt, “The Billion-Dollar Shack,” New York TimesMagazine, December 10, 2000.8. Hiery, The Neglected War, 116–25, 241; “Nauru,” New Zealand Ministry of Foreign Affairs and Trade.9. Hitt, “The Billion-Dollar Shack”; David Kendall, “Doomed Island,” Alternatives Journal, January 2009.10. “Nauru” (video), NFSA Films.11. Philip Shenon, “A Pacific Island Is Stripped of Everything,” New York Times, December 10, 1995.12. Hitt, “The Billion-Dollar Shack”; Robert Matau, “Road Deaths Force Nauru to Review Traffic Laws,”Islands Business, July 10, 2013; “The Fattest Place on Earth” (video), Nightline, ABC, January 3, 2011;Steshia Hubert interview, March 30, 2012. [{'title': 'This Changes Everything_ Capitalism vs. The Climate ( PDFDrive ).txt'}]
```
</details>