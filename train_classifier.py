import sys
import os
import pickle
from transformers import AutoTokenizer
from datasets import Dataset
from transformers import DataCollatorWithPadding
import evaluate
import numpy as np
from transformers import AutoModelForSequenceClassification, TrainingArguments, Trainer


tokenizer = AutoTokenizer.from_pretrained('climatebert/distilroberta-base-climate-f')
def preprocess_function(examples):
    return tokenizer(examples['text'], truncation=True)


accuracy = evaluate.load('accuracy')
def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return accuracy.compute(predictions=predictions, references=labels)


def main(metadata_path):
    metadata_filename = os.path.basename(metadata_path)
    metadata_basename, _ = os.path.splitext(metadata_filename)
    traindata_path = os.path.join('traindata', '{}.pkl'.format(metadata_basename))

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    with open(traindata_path, 'rb') as f:
        id2label, label2id, text_data = pickle.load(f)
    text_dataset = Dataset.from_dict(text_data).class_encode_column("label").train_test_split(
        test_size=0.3,
        stratify_by_column="label",
        shuffle=True,
    )
    tokenized_data = text_dataset.map(preprocess_function, batched=True)


    model = AutoModelForSequenceClassification.from_pretrained(
        'climatebert/distilroberta-base-climate-f', num_labels=len(id2label.keys()), id2label=id2label, label2id=label2id
    )


    training_args = TrainingArguments(
        output_dir='models/{}'.format(metadata_basename),
        learning_rate=1e-4,
        per_device_train_batch_size=36,
        per_device_eval_batch_size=36,
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
    main(sys.argv[1])
