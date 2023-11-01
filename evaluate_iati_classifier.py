import os
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
import torch
import pickle
from tqdm import tqdm


def main():
    model_dir = 'models/iati_climate_pilot_icf_balanced'

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

    all_words = set()
    pickle_path = "traindata/iati_climate_pilot_icf_balanced.pkl"
    with open(pickle_path, 'rb') as f:
        id2label, label2id, text_data = pickle.load(f)
        text_data_texts = text_data['text']
        for text in text_data_texts:
            words = tokenizer.tokenize(text)
            words = [
                w for w in words if 
                w not in tokenizer.all_special_tokens and 
                '#' not in w and
                len(w) > 3
            ]
            bigrams = ['{} {}'.format(word1, word2) for word1, word2 in zip(words, words[1:])]
            all_words.update(words)
            all_words.update(bigrams)
    all_words = list(all_words)

    word_results = []

    for i in tqdm(range(0, len(all_words))):
        word = all_words[i]
        inputs = tokenizer(word, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits[0].tolist()
        scores_obj = {id2label[id]: logits[id] for id in id2label}
        scores_obj['word'] = word
        word_results.append(scores_obj)
    
    count = 20
    for label in label2id:
        sorted_asc = sorted(word_results, key=lambda x: x[label])
        sorted_desc = sorted(word_results, key=lambda x: x[label], reverse=True)
        twenty_least = ", ".join([obj['word'] for obj in sorted_asc[:count]])
        twenty_most = ", ".join([obj['word'] for obj in sorted_desc[:count]])
        print("For {}:".format(label))
        print("{} most negatively correlated tokens: {}".format(count, twenty_least))
        print("{} most postively correlated tokens: {}".format(count, twenty_most))
        print("\n")

if __name__ == '__main__':
    main()