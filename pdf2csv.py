import csv
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import os

def pdf2csv(pdf_file, csv_file):
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["title", "url", "text"])

        resource_manager = PDFResourceManager()
        laparams = LAParams()
        device = TextConverter(resource_manager, StringIO(), laparams=laparams)
        interpreter = PDFPageInterpreter(resource_manager, device)

        with open(pdf_file, 'rb') as f:
            for page_number, page in enumerate(PDFPage.get_pages(f), start=1):
                device.outfp.truncate(0)  # StringIOオブジェクトをリセット
                device.outfp.seek(0)  # StringIOオブジェクトのカーソルを先頭に戻す
                interpreter.process_page(page)
                text = device.outfp.getvalue()  # StringIOオブジェクトからテキストを取得

                writer.writerow([os.path.basename(pdf_file), f"page{page_number}", text])
