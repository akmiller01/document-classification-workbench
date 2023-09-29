import os
import sys
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
import torch
import pickle
from tqdm import tqdm


def threshold_logits(logits, threshold=0):
    indicies = []
    for i in range(0, len(logits[0])):
        if logits[0][i] > threshold:
            indicies.append(i)
    return indicies


def main(metadata_path):
    metadata_filename = os.path.basename(metadata_path)
    metadata_basename, _ = os.path.splitext(metadata_filename)
    traindata_path = os.path.join('traindata', '{}.pkl'.format(metadata_basename))
    model_dir = os.path.join('models', metadata_basename)

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

    with open(traindata_path, 'rb') as f:
        id2label, label2id, text_data = pickle.load(f)

    score = 0
    possible_score = 0
    hit_dict = {}
    miss_dict = {}

    for i in tqdm(range(0, len(text_data['text']))):
        text = text_data['text'][i]
        label = text_data['label'][i]
        subconcept = id2label[label]
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits
        point = label in threshold_logits(logits)
        if point:
            score += 1
            if subconcept not in hit_dict.keys():
                hit_dict[subconcept] = 1
            else:
                hit_dict[subconcept] += 1
        else:
            if subconcept not in miss_dict.keys():
                miss_dict[subconcept] = 1
            else:
                miss_dict[subconcept] += 1
        possible_score += 1
    print('{}/{}'.format(score, possible_score))
    print('Hits', hit_dict)
    print('Misses', miss_dict)

if __name__ == '__main__':
    main(sys.argv[1])