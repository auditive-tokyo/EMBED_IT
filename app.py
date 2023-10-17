from flask import Flask, request, render_template, send_file, jsonify, after_this_request
from werkzeug.utils import secure_filename
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor
from scrapy.settings import Settings
from spider import MySpider, MySitemapSpider
from pdf2csv import pdf2csv
from webpilot import webpilot
from embedding import load_api_key, process_csv_files, save_to_csv, save_to_json, load_json, create_embeddings, save_vectors, remove_file
import json
import os
from multiprocessing import Process
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import zipfile
import pandas as pd

app = Flask(__name__)

class FlaskWebInterface:

    def __init__(self):
        pass  # CrawlerRunnerはここでは初期化しない

    def crawl(self, spider, *args, **kwargs):
        process = CrawlerProcess(get_project_settings())
        process.crawl(spider, *args, **kwargs)
        process.start()

@app.route('/', methods=['GET'])
def form():
    return render_template('index.html')

@app.route('/webpilot', methods=['POST'])
def run_webpilot():
    webpilot_url = request.form.get('webpilot_url')
    webpilot_output = request.form.get('webpilot_output')
    webpilot(webpilot_url, webpilot_output)
    return '''
    <p>WebPilot task done.</p>
    <button onclick="window.location.href = '/';">Go back</button>
    '''

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return 'No file part', 400
    file = request.files['pdf_file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        filename = secure_filename(file.filename)  # ファイル名を安全な形式に変換
        filepath = os.path.join('pdfs', filename)
        file.save(filepath)
        pdf2csv(filepath, os.path.join('output', filename + '.csv'))  # 関数を直接呼び出す
        os.remove(filepath)  # ファイルの削除
        return '''
        <p>File uploaded and processed.</p>
        <button onclick="window.location.href = '/';">Go back</button>
        '''
        
@app.route('/list_files', methods=['GET'])
def list_files():
    files = os.listdir('output/')
    return jsonify(files=files)

@app.route('/get_csv_data', methods=['POST'])
def get_csv_data():
    filename = request.json['filename']
    data = pd.read_csv('output/' + filename)
    return data.to_json(orient='records')

@app.route('/update_csv_data', methods=['POST'])
def update_csv_data():
    updated_data = request.json['data']
    filename = request.json['filename']
    df = pd.DataFrame(updated_data)
    df.to_csv('output/' + filename, index=False)
    return jsonify(status='success')

@app.route('/save_edited_data', methods=['POST'])
def save_edited_data():
  json_data = request.json
  df = pd.DataFrame(json_data) 
  df.to_csv('edited.csv', index=False)
  return "OK"

@app.route('/delete_file', methods=['POST'])
def delete_file():
    data = request.get_json()
    filename = data.get('filename')
    file_path = os.path.join('output/', filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return jsonify(success=True)

@app.route('/embedding', methods=['POST'])
def run_embedding():
    # Load settings and set OpenAI API key
    load_api_key()

    # Process CSV files and merge dataframes
    folder_path = 'output/'
    df = process_csv_files(folder_path)

    # Save the merged dataframe to a CSV file for checking
    save_to_csv(df, 'for_cheking.csv')

    # Convert the merged dataframe to JSON and save
    save_to_json(df, 'reference.json')

    # Load the text from the local JSON file
    data = load_json('reference.json')

    # Create embeddings
    embeddings = create_embeddings(data)

    # Save the vectors to the local disk
    save_vectors(embeddings, "vectors.npy")

    # Remove the file if it exists
    remove_file('embedded.json')

    # Create a ZIP file
    with zipfile.ZipFile('embedding_files.zip', 'w') as zipf:
        zipf.write('for_cheking.csv')
        zipf.write('reference.json')
        zipf.write('vectors.npy')
        
    # Remove the original files after they have been added to the ZIP file
    remove_file('for_cheking.csv')
    remove_file('reference.json')
    remove_file('vectors.npy')

    # Send the ZIP file to the user
    @after_this_request
    def remove_zip_file(response):
        try:
            os.remove('embedding_files.zip')
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
        return response

    return send_file('embedding_files.zip', as_attachment=True)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    try:
        new_settings = request.get_json()  # 新しい設定を取得

        # 既存の設定を読み込む
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                existing_settings = json.load(f)
        else:
            existing_settings = {}

        # 既存の設定に新しい設定を追加
        existing_settings.update(new_settings)

        # 設定をファイルに保存
        with open('settings.json', 'w') as f:
            json.dump(existing_settings, f)

        return 'Settings saved.'
    except Exception as e:
        return f'Error saving settings: {str(e)}', 500

@app.route('/load_settings', methods=['GET'])
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)  # ファイルからJSONデータを読み込む
        return settings  # JSONデータをレスポンスとして返す
    except FileNotFoundError:
        # デフォルトの設定を返す
        return {
            "scrape_url": {
                "url": "",
                "include_elements": "",
                "exclude_tags": "",
                "exclude_elements": "",
                "output_file": "",
                "site_name": "" 
            }
        }
    except json.JSONDecodeError:
        return 'Error decoding settings file.', 500
    except Exception as e:
        return f'Error loading settings: {str(e)}', 500

def run_spider_in_new_process(url, include_elements, exclude_tags, exclude_elements, output_file):
    configure_logging()
    runner = CrawlerRunner(Settings({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'DEBUG',
        'FEED_FORMAT': 'csv',  # or 'json'
        'FEED_URI': os.path.join('output', output_file),  # ユーザーが指定したファイル名を使用
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEED_EXPORT_FIELDS': ['title', 'url', 'text'],
    }))

    # URLがサイトマップを指しているかどうかをチェック
    if 'sitemap' in url:
        spider = MySitemapSpider
        spider.sitemap_urls = [url]
    else:
        spider = MySpider
        spider.start_urls = [url]

    runner.crawl(spider, include_elements=include_elements, exclude_tags=exclude_tags, exclude_elements=exclude_elements)
    reactor.run(installSignalHandlers=0)  # the script will block here until the crawling is finished

# スパイダーを別のプロセスで実行
@app.route('/run_spider', methods=['POST'])
def run_spider():
    url = request.form.get('url')
    include_elements = request.form.get('include_elements')
    exclude_tags = request.form.get('exclude_tags')
    exclude_elements = request.form.get('exclude_elements')
    output_file = request.form.get('output_file') or 'default.csv'

    # Ensure the output file has the .csv extension
    if not output_file.endswith('.csv'):
        output_file += '.csv'

    p = Process(target=run_spider_in_new_process, args=(url, include_elements, exclude_tags, exclude_elements, output_file))
    p.start()
    p.join()
    

if __name__ == '__main__':
    app.run(port=45451)
