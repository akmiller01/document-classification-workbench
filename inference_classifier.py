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
        # print("Most recent checkpoint folder:", most_recent_checkpoint)
    else:
        print("No checkpoint folders found in", model_dir)

    tokenizer = AutoTokenizer.from_pretrained(most_recent_checkpoint)
    model = AutoModelForSequenceClassification.from_pretrained(most_recent_checkpoint)

    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad():
        logits = model(**inputs).logits

    predicted_class_id = logits.argmax().item()
    print("Output: {}".format(model.config.id2label[predicted_class_id]))


if __name__ == '__main__':
    text = """
    Poverty reduction and diminution of internal an transnational migration in Nicaragua and Costa Rica POVERTY REDUCTION AND DIMINUTION OF INTERNAL AN TRANSNATIONAL MIGRATION IN NICARAGUA AND COSTA RICA Poverty reduction and diminution of internal an transnational migration in Nicaragua and Costa Rica
    """
    print("Input: {}".format(text))
    main(sys.argv[1], text)

    text = """
    Documentation of the Early 19th-Century First Baptist Church in Mawlamyine DOCUMENTATION OF THE EARLY 19TH-CENTURY FIRST BAPTIST CHURCH IN MAWLAMYINE Though the architecture of the church is Western in design, the materials and building methods used in its construction stemmed from Burmese craft traditions, resulting in a masterful blend of Burmese and Western styles. This project includes a condition survey, conservation plan, and site documentation.
    """
    print("Input: {}".format(text))
    main(sys.argv[1], text)
