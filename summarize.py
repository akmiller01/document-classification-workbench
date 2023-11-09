import sys
import os
import csv
from tqdm import tqdm
import transformers
import math
import pickle
import transformers
import math


SUMMARIZER = transformers.pipeline("summarization", model='philschmid/distilbart-cnn-12-6-samsum')


def chunk_by_tokens(tokenizer, input_text, model_max_size):
    chunks = list()
    tokens = tokenizer.encode(input_text)
    token_length = len(tokens)
    desired_number_of_chunks = math.ceil(token_length / model_max_size)
    calculated_chunk_size = math.ceil(token_length / desired_number_of_chunks)
    for i in range(0, token_length, calculated_chunk_size):
        chunks.append(tokenizer.decode(tokens[i:i + calculated_chunk_size]))
    return chunks


def recursive_summarize_text(summarizer, input_text, model_max_size, summary_min_size, summary_max_size, depth):
    depth += 1
    summaries = []
    batches = chunk_by_tokens(summarizer.tokenizer, input_text, model_max_size)
    for substring in batches:
        summary = summarizer(substring, min_length=summary_min_size, max_length=summary_max_size)
        summaries.append(summary[0]['summary_text'])
    new_input_text = ' '.join(summaries)
    new_input_length = len(new_input_text.split(' '))
    if new_input_length < summary_max_size:
        return new_input_text
    else:
        return recursive_summarize_text(summarizer, new_input_text, model_max_size, summary_min_size, summary_max_size, depth)


def summarize_full_text(summarizer, full_text):
    return recursive_summarize_text(summarizer, full_text, 998, 100, 300, 0)


def main(metadata_path):
    metadata_filename = os.path.basename(metadata_path)
    metadata_basename, _ = os.path.splitext(metadata_filename)
    textdata_folder = os.path.join('textdata', metadata_basename)
    result_path = os.path.join('gdc', 'summaries.csv')

    result = []
    with open(metadata_path) as csv_file:
        reader = csv.reader(csv_file)
        header = True
        for row in tqdm(reader):
            if header:
                header = False
                continue
            doc_id = row[0]
            url = row[1]
            title = row[2]
            full_text_path = os.path.join(textdata_folder, "{}.txt".format(doc_id))
            with open(full_text_path, 'r') as txt_file:
                full_text = txt_file.read()
                full_summary = summarize_full_text(SUMMARIZER, full_text)
            result_row = [doc_id, url, title, full_summary]
            result.append(result_row)

    with open(result_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'URL', 'Title', 'Summary'])
        for result_row in result:
            writer.writerow(result_row)

if __name__ == '__main__':
    main(sys.argv[1])