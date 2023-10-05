import os
import pickle
from transformers import AutoTokenizer
from datasets import Dataset
from transformers import DataCollatorWithPadding
import evaluate
import numpy as np
from transformers import AutoModelForSequenceClassification, TrainingArguments, Trainer


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


tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
def preprocess_function(examples):
    return tokenizer(examples['text'], truncation=True)


accuracy = evaluate.load('accuracy')
def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return accuracy.compute(predictions=predictions, references=labels)


def main():
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    id2label = {model['id']: model['name'] for model in model_mapping}
    label2id = {model['name']: model['id'] for model in model_mapping}


    all_text_data_dicts = {
        'text': [],
        'label': []
    }
    for model in model_mapping:
        with open(model['pickle'], 'rb') as f:
            _, _, text_data = pickle.load(f)
            text_data_texts = text_data['text']
            for text in text_data_texts:
                all_text_data_dicts['text'].append(text)
                all_text_data_dicts['label'].append(model['id'])

    text_dataset = Dataset.from_dict(all_text_data_dicts).train_test_split(test_size=0.33)
    tokenized_data = text_dataset.map(preprocess_function, batched=True)


    model = AutoModelForSequenceClassification.from_pretrained(
        'distilbert-base-uncased', num_labels=len(id2label.keys()), id2label=id2label, label2id=label2id
    )


    training_args = TrainingArguments(
        output_dir='models/meta',
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=10,
        weight_decay=0.01,
        evaluation_strategy='epoch',
        save_strategy='epoch',
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_data['train'],
        eval_dataset=tokenized_data['test'],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()


if __name__ == '__main__':
    main()
