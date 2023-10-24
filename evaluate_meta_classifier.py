import os
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
import torch
import pickle
from tqdm import tqdm


model_mapping = [
    {
        'id': 0,
        'meta': 'metadata/data_concepts.csv',
        'pickle': 'traindata/data_concepts.pkl',
        'name': 'Data Ecosystems'
    },
    {
        'id': 1,
        'meta': 'metadata/humanitarian_concepts.csv',
        'pickle': 'traindata/humanitarian_concepts.pkl',
        'name': 'Humanitarian'
    },
    {
        'id': 2,
        'meta': 'metadata/development_concepts.csv',
        'pickle': 'traindata/development_concepts.pkl',
        'name': 'Development Finance'
    },
]


def main():
    model_dir = 'models/meta'

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
    for data_model in model_mapping:
        with open(data_model['pickle'], 'rb') as f:
            _, _, text_data = pickle.load(f)
            text_data_texts = text_data['text']
            for text in text_data_texts:
                words = tokenizer.tokenize(text)
                words = [
                    w for w in words if 
                    w not in tokenizer.all_special_tokens and 
                    '#' not in w and
                    len(w) > 2
                ]
                all_words.update(words)
    all_words = list(all_words)

    word_results = []

    for i in tqdm(range(0, len(all_words))):
        word = all_words[i]
        inputs = tokenizer(word, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits[0].tolist()
        scores_obj = {model['name']: logits[model['id']] for model in model_mapping}
        scores_obj['All'] = sum(logits)
        scores_obj['word'] = word
        word_results.append(scores_obj)
    
    for data_model in model_mapping:
        sorted_asc = sorted(word_results, key=lambda x: x[data_model['name']])
        sorted_desc = sorted(word_results, key=lambda x: x[data_model['name']], reverse=True)
        twenty_least = ", ".join([obj['word'] for obj in sorted_asc[:20]])
        twenty_most = ", ".join([obj['word'] for obj in sorted_desc[:20]])
        print("For {}:".format(data_model['name']))
        print("Twenty most negatively correlated tokens: {}".format(twenty_least))
        print("Twenty most postively correlated tokens: {}".format(twenty_most))
        print("\n")

    sorted_asc = sorted(word_results, key=lambda x: x['All'])
    sorted_desc = sorted(word_results, key=lambda x: x['All'], reverse=True)
    twenty_least = ", ".join([obj['word'] for obj in sorted_asc[:20]])
    twenty_most = ", ".join([obj['word'] for obj in sorted_desc[:20]])
    print("For all categories:")
    print("Twenty most negatively correlated tokens: {}".format(twenty_least))
    print("Twenty most postively correlated tokens: {}".format(twenty_most))

if __name__ == '__main__':
    main()