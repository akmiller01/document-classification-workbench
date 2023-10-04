import time
import requests
import io
import os
import sys
from PyPDF2 import PdfReader
import olefile
import docx
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from tqdm import tqdm


def initialize_remote_browser():
    options = Options()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('prefs', {
        'download.default_directory': '/tmp/',
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing_for_trusted_sources_enabled': False,
        'safebrowsing.enabled': False
    })
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def find_pdf_links(driver):
    # Find all anchor elements (hyperlinks) on the page
    all_links = driver.find_elements(By.TAG_NAME, 'a')

    # Initialize a list to store the URLs
    pdf_links = []

    # Loop through all the links and check if the href attribute ends with 'pdf' (case-insensitive)
    for link in all_links:
        href = link.get_attribute('href')
        if href and href.lower().endswith('.pdf'):
            pdf_links.append(href)

    return pdf_links


def fetch_twitter(driver, url):
    driver.get(url)
    time.sleep(10)
    try:
        article = driver.find_element(By.XPATH, '//article')
    except:
        return {
            'title': None,
            'extension': None,
            'full_text': None,
            'bytes': None
        }
    try:
        hyperlink = article.find_element(By.XPATH, './/a[@target="_blank"]')
    except NoSuchElementException:
        title = driver.title
        return {
            'title': title,
            'extension': 'txt',
            'full_text': article.text,
            'bytes': None
        }
    return fetch_nonsocial(driver, hyperlink.get_attribute('href'))


def fetch_nonsocial(driver, url):
    headers = {'User-Agent': 'DI-Archivist/0.0.1 (Internal Knowledge Management System) https://devinit.org/contact-us/'}
    requests_failure = False
    try:
        get_request = requests.get(url, headers=headers, allow_redirects=True)
        time.sleep(10)
    except:
        requests_failure = True
    if requests_failure == True:
        try:
            driver.get(url)
            time.sleep(10)
            body_text = driver.find_element(By.XPATH, '/html/body').text
            if 'Checking if the site connection is secure' in body_text:
                time.sleep(60)
            pdf_links = find_pdf_links(driver)
            if len(pdf_links) > 0:
                time.sleep(10)
                pdf_link_results = fetch_nonsocial(driver, pdf_links[0])
                if pdf_link_results['full_text'] is not None and pdf_link_results['full_text'] != '':
                    return pdf_link_results
            title = driver.title
            try:
                meta_description = driver.find_element(By.XPATH,"//meta[@name='description']").get_attribute("content")
            except:
                meta_description = ''
            return {
                'title': title,
                'extension': 'txt',
                'full_text': title + '\n' + meta_description + '\n' + body_text,
                'bytes': None
            }
        except:
            return {
                'title': None,
                'extension': None,
                'full_text': None,
                'bytes': None
            }
    if get_request.ok:
        try:
            content_type = get_request.headers['Content-Type']
        except KeyError:
            return {
                'title': None,
                'extension': None,
                'full_text': None,
                'bytes': None
            }
        if content_type.startswith('text'):
            driver.get(url)
            time.sleep(10)
            body_text = driver.find_element(By.XPATH, '/html/body').text
            if 'Checking if the site connection is secure' in body_text:
                time.sleep(60)
            pdf_links = find_pdf_links(driver)
            if len(pdf_links) > 0:
                pdf_link_results = fetch_nonsocial(driver, pdf_links[0])
                if pdf_link_results['full_text'] is not None and pdf_link_results['full_text'] != '':
                    return pdf_link_results
            title = driver.title
            try:
                meta_description = driver.find_element(By.XPATH,"//meta[@name='description']").get_attribute("content")
            except:
                meta_description = ''
            return {
                'title': title,
                'extension': 'txt',
                'full_text': title + '\n' + meta_description + '\n' + body_text,
                'bytes': None
            }
        elif content_type.startswith('application/pdf'):
            try:
                text_content = []
                bytes_content = get_request.content
                pdf_content = io.BytesIO(bytes_content)
                pdf_reader = PdfReader(pdf_content)
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())
                return {
                    'title': None,
                    'extension': 'pdf',
                    'full_text': '\n'.join(text_content).replace('\x00',''),
                    'bytes': bytes_content
                }
            except Exception as e:
                return {
                    'title': None,
                    'extension': None,
                    'full_text': None,
                    'bytes': None
                }
        elif content_type == 'application/msword':
            try:
                bytes_content = get_request.content
                doc_content = io.BytesIO(bytes_content)
                with olefile.OleFileIO(doc_content) as ole:
                    stream = ole.openstream('WordDocument')
                    text_content = stream.read().decode('utf-8', errors='ignore')
                return {
                    'title': None,
                    'extension': 'doc',
                    'full_text': text_content.replace('\x00',''),
                    'bytes': bytes_content
                }
            except Exception as e:
                return {
                    'title': None,
                    'extension': None,
                    'full_text': None,
                    'bytes': None
                }
        elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            try:
                text_content = []
                bytes_content = get_request.content
                doc_content = io.BytesIO(bytes_content)
                doc = docx.Document(doc_content)
                for para in doc.paragraphs:
                    text_content.append(para.text)
                return {
                    'title': None,
                    'extension': 'docx',
                    'full_text': '\n'.join(text_content).replace('\x00',''),
                    'bytes': bytes_content
                }
            except Exception as e:
                return {
                    'title': None,
                    'extension': None,
                    'full_text': None,
                    'bytes': None
                }
    else:
        try:
            driver.get(url)
            time.sleep(10)
            body_text = driver.find_element(By.XPATH, '/html/body').text
            if 'Checking if the site connection is secure' in body_text:
                time.sleep(60)
            title = driver.title
            try:
                meta_description = driver.find_element(By.XPATH,"//meta[@name='description']").get_attribute("content")
            except:
                meta_description = ''
            return {
                'title': title,
                'extension': 'txt',
                'full_text': title + '\n' + meta_description + '\n' + body_text,
                'bytes': None
            }
        except:
            return {
                'title': None,
                'extension': None,
                'full_text': None,
                'bytes': None
            }
    return {
        'title': None,
        'extension': None,
        'full_text': None,
        'bytes': None
    }

def main(metadata_path):
    uncopied_documents = pd.read_csv(metadata_path)
    metadata_filename = os.path.basename(metadata_path)
    metadata_basename, _ = os.path.splitext(metadata_filename)
    textdata_folder = os.path.join('textdata', metadata_basename)
    os.makedirs(textdata_folder, exist_ok=True)

    driver = initialize_remote_browser()

    problematic_ids = []
    short_ids = []

    for document in tqdm(uncopied_documents.to_dict('records')):
        domain = urlparse(document['url']).netloc
        if domain in ['twitter.com']:
            new_title, extension, full_text, bytes = fetch_twitter(driver, document['url']).values()
        else:
            new_title, extension, full_text, bytes = fetch_nonsocial(driver, document['url']).values()

        filename = '{}/{}.txt'.format(textdata_folder, document['id'])
        if full_text is None:
            full_text = ''
        with open(filename, 'w') as txt_file:
            txt_file.write(full_text)

        if full_text == '':
            problematic_ids.append(document['id'])
        elif len(full_text.split(' ')) < 100:
            short_ids.append(document['id'])

    print(
        "Problematic IDs: {}".format(
            ", ".join([str(id) for id in problematic_ids])
        )
    )

    print(
        "Short IDs: {}".format(
            ", ".join([str(id) for id in short_ids])
        )
    )

    driver.close()

if __name__ == '__main__':
    main(sys.argv[1])
