import os
import sys
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
import torch
import pickle


def main(metadata_path, text):
    metadata_filename = os.path.basename(metadata_path)
    metadata_basename, _ = os.path.splitext(metadata_filename)
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

    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad():
        logits = model(**inputs).logits

    predicted_class_id = logits.argmax().item()
    print(model.config.id2label[predicted_class_id])


if __name__ == '__main__':
    text = """
    The paper provides a narrative, rationale, and a vision for global data governance with the objective of consolidating a United Nations system common understanding on the topic. UN has been providing national and global statistics for the UN Statistics Commission since 1947. Data are the lifeblood of the digital economy, driving international services trade, informing logistics, shaping markets, and shaping markets. UN OCHA, the GovLab and Center for Innovation propose an expanded framework based on six elements: technology, legal, governance, people, and network. The UN's Fundamental Principles of Official Statistics apply to international organisations, but there is no explicit commitment by Member States to these principles. UN data may not always meet the high standards required to inform global policy decisions. The UN could act as one of the repositories of privately generated data that have public global relevance. The private sector has a large concentration of data with probably more decision-making on how to collect, process and use certain data than most governments. There are opportunities to further support Member States efforts in progressing towards an accountable, agile, and fair international
    """
    main(sys.argv[1], text)
