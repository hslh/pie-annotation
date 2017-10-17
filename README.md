# Corpus of Potentially Idiomatic Expressions
This is an evaluation corpus for the automatic detection of potentially idiomatic expressions (PIEs), based on the British National Corpus (BNC). Potentially idiomatic expressions are like idiomatic expressions, but the term also covers literal uses of idiomatic expressions, such as 'I leave work at the end of the day.' for the idiom 'at the end of the day'. Using a pre-defined set of 591 PIEs and a set of 23 documents from the BNC, we extracted all sentences possibly containing one of these PIEs in one form or another, thus including literal uses. The resulting 2239 PIE-sentence pairs were then annotated for whether they really contained the PIE in question, and if so, in what sense it was used.

## Contents & Usage
This repository contains three json-files containing the annotations. `PIE_annotations_all_no_sentences.json` contains all 2239 PIEs with annotations, while `PIE_annotations_dev_no_sentences.json` and `PIE_annotations_test_no_sentences.json` contain the same data, but split into a development and test set, respectively. Due to copyright restrictions on the BNC, the sentence containing the PIE and the 2-sentence context window around that have been removed from these files. 

To add the sentence and context, download a copy of the BNC-XML from [here](http://www.natcorp.ox.ac.uk/), and run `python add_sentences.py /path/to/BNC/2554/download/Texts/`. This will create three new `PIE_annotations_*.json` files, which do contain the sentences and 2-sentence context window. 

## Format
The json-files contain a list of Python dictionaries, with the following information:
* `idiom`: the dictionary form of the PIE
* `PIE_label`: label indicating whether this sentence contains the PIE in question (`'y'`) or not (`'n'`)
* `sense_label`: label indicating the sense of the PIE, can be idiomatic (`'y'`), literal (`'n'`), other (`'o'`), or non-applicable, in the case of a non-PIE (`'?'`)
* `document_id`: BNC document id
* `sentence_number`: BNC sentence number
* `sentence`: 5-sentence window containing the PIE, with the PIE always in the third sentence
* `offsets`: character offsets of the PIE's component words in the 5-sentence context window
