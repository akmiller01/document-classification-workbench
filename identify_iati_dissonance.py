import os
import math
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
import torch
import pickle
from tqdm import tqdm
import csv


def binary_logits_max(logits):
    if logits[0][0] > logits[0][1]:
        return 0
    return 1


def chunk_by_tokens(tokenizer, input_text, model_max_size):
    chunks = list()
    tokens = tokenizer.encode(input_text)
    token_length = len(tokens)
    desired_number_of_chunks = math.ceil(token_length / model_max_size)
    calculated_chunk_size = math.ceil(token_length / desired_number_of_chunks)
    for i in range(0, token_length, calculated_chunk_size):
        chunks.append(tokenizer.decode(tokens[i:i + calculated_chunk_size]))
    return chunks


def fetch_iati_identifiers(tokenizer, metadata_path):
    metadata_filename = os.path.basename(metadata_path)
    metadata_basename, _ = os.path.splitext(metadata_filename)
    textdata_folder = os.path.join('textdata', metadata_basename)
    chunk_ids = []
    with open(metadata_path) as csv_file:
        reader = csv.reader(csv_file)
        header = True
        for row in tqdm(reader):
            if header:
                header = False
                continue
            doc_id = row[0]
            iati_identifier = row[1]
            full_text_path = os.path.join(textdata_folder, "{}.txt".format(doc_id))
            with open(full_text_path, 'r') as txt_file:
                full_text = txt_file.read()
                pages = chunk_by_tokens(tokenizer, full_text, 500)
                for _ in pages:
                    chunk_ids.append(iati_identifier)
    return chunk_ids


def main():
    model_dir = 'models/iati_climate_pilot_balanced'

    # Get a list of all folders in model_dir that start with "checkpoint"
    checkpoint_folders = [folder for folder in os.listdir(model_dir) if folder.startswith("checkpoint")]

    # Sort the checkpoint folders by modification time in descending order
    checkpoint_folders.sort(key=lambda folder: os.path.getmtime(os.path.join(model_dir, folder)), reverse=True)

    # Get the most recent checkpoint folder
    if checkpoint_folders:
        most_recent_checkpoint = os.path.join(model_dir, checkpoint_folders[0])
        print("Most recent checkpoint folder:", most_recent_checkpoint)
    else:
        print("No checkpoint folders found in", model_dir)

    tokenizer = AutoTokenizer.from_pretrained(most_recent_checkpoint)
    model = AutoModelForSequenceClassification.from_pretrained(most_recent_checkpoint)

    data_iati_identifiers = fetch_iati_identifiers(tokenizer, metadata_path="metadata/iati_climate_pilot_balanced.csv")

    label_not_predict_climate = []
    label_climate_predict_not = []
    pickle_path = "traindata/iati_climate_pilot_balanced.pkl"
    with open(pickle_path, 'rb') as f:
        id2label, label2id, text_data = pickle.load(f)

    for i in tqdm(range(0, len(text_data['text']))):
        text = text_data['text'][i]
        id = text_data['label'][i]
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits
        predicted_id = binary_logits_max(logits)
        if id == 0 and predicted_id == 1:
            matching_id = data_iati_identifiers[i]
            label_not_predict_climate.append(matching_id)
        if id == 1 and predicted_id == 0:
            matching_id = data_iati_identifiers[i]
            label_climate_predict_not.append(matching_id)

    print(
        "Projects labeled not climate that should be: {}".format(
            ", ".join(
                label_not_predict_climate
            )
        )
    )
    print("\n")
    print(
        "Projects labeled climate that should not be: {}".format(
            ", ".join(
                label_climate_predict_not
            )
        )
    )

if __name__ == '__main__':
    main()