import os
import json
import pandas as pd
import csv
import numpy as np
import re
from openai import OpenAI  # Updated import

client = None  # Global client variable

def load_api_key():
    global client
    # Check if settings.json exists
    if os.path.exists('settings.json'):
        # Load settings
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        # Initialize OpenAI client
        api_key = settings.get('set_api_key', {}).get('api_key', '')
        client = OpenAI(api_key=api_key)
    else:
        # Create settings.json with empty settings
        settings = {'set_api_key': {'api_key': ''}}
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
        # Initialize with empty key
        client = OpenAI(api_key='')

def process_csv_files(folder_path):
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    
    # 先頭に数字があるファイルとないファイルに分ける
    numbered_files = [f for f in csv_files if re.split('-|_|\\.', f)[0].isdigit()]
    non_numbered_files = [f for f in csv_files if not re.split('-|_|\\.', f)[0].isdigit()]

    # 数字があるファイルは逆ソートして後に読み込む
    non_numbered_files = sorted(non_numbered_files)
    numbered_files = sorted(numbered_files, reverse=True)

    # ファイルのリストを結合する
    csv_files = non_numbered_files + numbered_files

    df_list = []
    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        
        # Identify header rows
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            headers = [i for i, row in enumerate(reader) if row[0] == 'title' and row[1] == 'url' and row[2] == 'text']
        
        # Read the CSV file in chunks, skipping header rows
        chunks = []
        start = 0
        for end in headers[1:]:
            chunks.append(pd.read_csv(file_path, skiprows=start+1, nrows=end-start-1, names=['title', 'url', 'text']))
            start = end
        chunks.append(pd.read_csv(file_path, skiprows=start+1, names=['title', 'url', 'text']))
        
        df = pd.concat(chunks)
        df_list.append(df)

    merged_df = pd.concat(df_list)

    # Remove duplicate rows based on 'title' and 'url', keeping the last occurrence
    merged_df = merged_df.drop_duplicates(subset=['title', 'url'], keep='last')

    return merged_df

def save_to_csv(df, filename):
    # Write the merged dataframe to a CSV file for checking
    df.to_csv(filename, index=False)

def save_to_json(df, filename):
    # Convert the merged dataframe to JSON
    json_data = df.to_json(orient='records', force_ascii=False)

    with open(filename, 'w', encoding='utf-8') as json_file:
        json_file.write(json_data)

def load_json(filename):
    # Load the text from a local JSON file
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def create_embeddings(data):
    embeddings = []

    for entry in data:
        title = entry['title']
        text = entry['text']

        # Combine the title and the text
        combined_input = f"{title} ||| {text}"

        # Create an embedding using new client approach
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=combined_input
        )

        embedding = response.data[0].embedding

        # Save the embedding
        embeddings.append({'embedding': embedding})

    return embeddings

def save_vectors(embeddings, filename):
    # Extract the vectors and convert them to NumPy arrays
    vectors = [np.array(item["embedding"], dtype=np.float32) for item in embeddings]

    # Stack all vectors into one big NumPy array
    stacked_vectors = np.vstack(vectors)

    # Save the vectors to the local disk
    np.save(filename, stacked_vectors)

def remove_file(filename):
    # Check if the file exists and then remove it
    if os.path.exists(filename):
        os.remove(filename)