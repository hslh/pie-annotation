#!/usr/bin/env python
# -*- coding: utf-8 -*-

''' 
Change format from v1 to v2: make context a list of sentences, and change offsets to be character offsets on middle context sentence. Also apply some manual corrections. 
'''

import json, argparse, os, re, copy
from bs4 import BeautifulSoup

# Read in arguments
parser = argparse.ArgumentParser()
parser.add_argument('corpus', metavar = 'DIRECTORY', type = str, help = "Specify the location of the Texts directory of the BNC-XML corpus.")
args = parser.parse_args()

# Read in manual offset corrections
correction_mapping = json.load(open('manual_offset_corrections.json', 'r'))

# Read in PIEs
full = json.load(open('PIE_annotations_all_no_sentences.json', 'r'))
full_documents = list(set([PIE['document_id'] for PIE in full]))
doc_dev = json.load(open('PIE_annotations_doc_dev_no_sentences.json', 'r'))
doc_test = json.load(open('PIE_annotations_doc_test_no_sentences.json', 'r'))
dev_documents = list(set([PIE['document_id'] for PIE in doc_dev]))
test_documents = list(set([PIE['document_id'] for PIE in doc_test]))
type_train = json.load(open('PIE_annotations_type_train_no_sentences.json', 'r'))
type_dev = json.load(open('PIE_annotations_type_dev_no_sentences.json', 'r'))
type_test = json.load(open('PIE_annotations_type_test_no_sentences.json', 'r'))
train_types = list(set([PIE['idiom'] for PIE in type_train]))
dev_types = list(set([PIE['idiom'] for PIE in type_dev]))
test_types = list(set([PIE['idiom'] for PIE in type_test]))

# Read in BNC documents, extract context to add
subdirectories = sorted(os.listdir(args.corpus))
for subdirectory in subdirectories:
	subdirectory_path = os.path.join(args.corpus, subdirectory)
	if os.path.isdir(subdirectory_path):
		subsubdirectories = sorted(os.listdir(subdirectory_path))
		for subsubdirectory in subsubdirectories:
			subsubdirectory_path = os.path.join(subdirectory_path, subsubdirectory)
			if os.path.isdir(subsubdirectory_path):
				document_ids = sorted(os.listdir(subsubdirectory_path))
				document_ids = [document_id for document_id in document_ids if re.match('.*\.xml', document_id)]
				# Cycle through documents
				for document_id in document_ids:
					if document_id[:-4] in full_documents:
						# Parse document
						print 'Processing document {0}'.format(document_id)
						document_path = os.path.join(subsubdirectory_path, document_id)
						parsed_xml = BeautifulSoup(open(document_path), 'lxml-xml')
						# Cycle through sentences, extract unicode string
						document_sentences = []
						for sentence in parsed_xml.find_all('s'):
							sentence_number = unicode(sentence['n'])
							sentence_string = ''
							sentence_string_tokenized = []
							for descendant in sentence.descendants:
								if descendant.name in ['c', 'w']:
									sentence_string += unicode(descendant.string)
									sentence_string_tokenized.append(unicode(descendant.string).strip())
							sentence_string_tokenized = ' '.join(sentence_string_tokenized)
							# Store sentences
							document_sentences.append((sentence_number, sentence_string, sentence_string_tokenized))
						# Add sentence context
						for PIE in full:
							if PIE['document_id'] == document_id[:-4]:
								# Sentence numbers are not necessarily consecutive, some are missing
								# So, cannot take sentence numbers as list indices, but find list index based on sentence number
								for idx, document_sentence in enumerate(document_sentences):
									if PIE['sentence_number'] == document_sentence[0]:
										sentence_index = idx
										PIE_sentence = document_sentence[1]
										PIE_sentence_tokenized = document_sentence[2]
								# Take 2 additional sentences of context, avoid going outside of document boundaries, add padding in those cases
								pre_context = document_sentences[max(0, sentence_index - 2):sentence_index]
								pre_padding = 2 - len(pre_context)
								pre_context = pre_padding * [(u'', u'', u'')] + pre_context
								pre_context_tokenized = [pre_context_sentence[2] for pre_context_sentence in pre_context]
								pre_context = [pre_context_sentence[1] for pre_context_sentence in pre_context]
								post_context = document_sentences[sentence_index + 1:min(sentence_index + 3, len(document_sentences) - 1)]
								post_padding = 2 - len(post_context)
								post_context += post_padding * [(u'', u'', u'')]
								post_context_tokenized = [post_context_sentence[2] for post_context_sentence in post_context]
								post_context = [post_context_sentence[1] for post_context_sentence in post_context]
								# Store newly extracted contexts, remove old context
								PIE['context_untokenized'] = pre_context + [PIE_sentence] + post_context
								PIE['context'] = pre_context_tokenized + [PIE_sentence_tokenized] + post_context_tokenized
								del PIE['sentence']
								# Adjust offsets by n, taking into account pre-padding length
								adjustment = len(' '.join(PIE['context_untokenized'][:2])) + 1 - pre_padding
								adjusted_offsets = [[offset[0] - adjustment, offset[1] - adjustment] for offset in PIE['offsets']]
								# Sort offsets so that they follow word order
								adjusted_offsets = sorted(adjusted_offsets, key = lambda x: x[0])
								# Convert from offsets on untokenized context to offsets on tokenized context by counting non-whitespace characters
								tokenized_offsets = []
								for pair in adjusted_offsets:
									new_pair = []
									len_untokenized = len(re.sub(r'\s', '', PIE_sentence[:pair[0]]))
									len_tokenized = len(re.sub(r'\s', '', PIE_sentence_tokenized[:pair[0]]))
									# Adjust offsets until number of non-whitespace characters matches
									if len_tokenized <= len_untokenized:
										r = range(0,30,1)
									else:
										r = range(-29,1,1)
									for adjustment in r:
										if len(re.sub(r'\s', '', PIE_sentence_tokenized[:pair[0] + adjustment])) == len_untokenized:
											new_pair = [offset + adjustment for offset in pair]
									tokenized_offsets.append(new_pair)
								# Check equivalence of untokenized and tokenized offsets
								old_span = PIE_sentence[adjusted_offsets[0][0]:adjusted_offsets[-1][-1]]
								new_span = PIE_sentence_tokenized[tokenized_offsets[0][0]:tokenized_offsets[-1][-1]]
								if re.sub(r'\s', '', old_span) != re.sub(r'\s', '', new_span):
									# Some manual corrections for very special cases
									if new_span == u'n Home Run ':
										tokenized_offsets = [[42,44], [50, 53]]
									elif new_span == u'to manufacture CCCP T-':
										tokenized_offsets = [[35,37], [55,56]]
									elif new_span == u'carry Government health warnings , so why ca ':
										tokenized_offsets = [[49,54], [91,93]]
								# Apply manual corrections if available
								PIE_id = '{0}-{1}-{2}'.format(PIE['idiom'], PIE['document_id'], PIE['sentence_number'])
								if PIE_id in correction_mapping:
									tokenized_offsets = correction_mapping[PIE_id]
								# Store new offsets
								PIE['offsets'] = tokenized_offsets

# Get dev and test set
doc_dev = [PIE for PIE in full if PIE['document_id'] in dev_documents]
doc_test = [PIE for PIE in full if PIE['document_id'] in test_documents]
type_train = [PIE for PIE in full if PIE['idiom'] in train_types]
type_dev = [PIE for PIE in full if PIE['idiom'] in dev_types]
type_test = [PIE for PIE in full if PIE['idiom'] in test_types]

# Output PIEs with sentence contest
json.dump(full, open('PIE_annotations_all_v2.json', 'w'))
json.dump(doc_dev, open('PIE_annotations_doc_dev_v2.json', 'w'))
json.dump(doc_test, open('PIE_annotations_doc_test_v2.json', 'w'))
json.dump(type_train, open('PIE_annotations_type_train_v2.json', 'w'))
json.dump(type_dev, open('PIE_annotations_type_dev_v2.json', 'w'))
json.dump(type_test, open('PIE_annotations_type_test_v2.json', 'w'))
