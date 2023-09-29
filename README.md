# document-classification-workbench
A space to collect training data and classify documents for other projects

## Copy documents example

```
python3 copy_documents.py metadata/data_concepts.csv
# Fix errors in scraping
python3 create_train_data.py metadata/data_concepts.csv
python3 train_classifier.py metadata/data_concepts.csv
python3 score_classifier.py metadata/data_concepts.csv
python3 inference_classifier.py metadata/data_concepts.csv
```