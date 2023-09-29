import sys
import os
import csv
from tqdm import tqdm
import transformers
import math
import pickle


def chunk_by_tokens(tokenizer, input_text, model_max_size):
    chunks = list()
    tokens = tokenizer.encode(input_text)
    token_length = len(tokens)
    desired_number_of_chunks = math.ceil(token_length / model_max_size)
    calculated_chunk_size = math.ceil(token_length / desired_number_of_chunks)
    for i in range(0, token_length, calculated_chunk_size):
        chunks.append(tokenizer.decode(tokens[i:i + calculated_chunk_size]))
    return chunks


def main(metadata_path):
    metadata_filename = os.path.basename(metadata_path)
    metadata_basename, _ = os.path.splitext(metadata_filename)
    textdata_folder = os.path.join('textdata', metadata_basename)

    tokenizer = transformers.AutoTokenizer.from_pretrained("distilbert-base-uncased")
    text_data = {'text': [], 'label': []}
    id2label = {}
    label2id = {}
    # First time through to create labels
    label_index = 0
    with open(metadata_path) as csv_file:
        reader = csv.reader(csv_file)
        header = True
        for row in reader:
            if header:
                header = False
                continue
            subconcept = row[2]
            if subconcept not in id2label.values():
                id2label[label_index] = subconcept
                label2id[subconcept] = label_index
                label_index += 1
    # Second time through to create test/train
    with open(metadata_path) as csv_file:
        reader = csv.reader(csv_file)
        header = True
        for row in tqdm(reader):
            if header:
                header = False
                continue
            doc_id = row[0]
            subconcept = row[2]
            subconcept_id = label2id[subconcept]
            full_text_path = os.path.join(textdata_folder, "{}.txt".format(doc_id))
            with open(full_text_path, 'r') as txt_file:
                full_text = txt_file.read()
                pages = chunk_by_tokens(tokenizer, full_text, 500)
                for page in pages:
                    text_data['text'].append(page)
                    text_data['label'].append(subconcept_id)
    with open('traindata/{}.pkl'.format(metadata_basename), 'wb') as f:
        pickle.dump((
            id2label,
            label2id,
            text_data
        ), f)

if __name__ == '__main__':
    main(sys.argv[1])