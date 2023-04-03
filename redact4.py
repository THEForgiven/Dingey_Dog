from flask import Flask, request, send_file
import re
import io

from docx import Document
from docx.enum.text import WD_BREAK

import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


app = Flask(__name__)

def process_pdf(file, keywords):
    pdf_reader = PyPDF2.PdfReader(file)
    output = io.BytesIO()

    for page_number in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_number]
        content = page.extract_text()

        for keyword in keywords:
            content = re.sub(r'\b' + re.escape(keyword.strip()) + r'\b', '_' * len(keyword), content)

        c = canvas.Canvas(output, pagesize=letter)
        textobject = c.beginText(40, 750)
        for line in content.split('\n'):
            textobject.textLine(line)
        c.drawText(textobject)
        c.showPage()

    c.save()
    output.seek(0)
    return output


# Move the process_docx function definition here
def process_docx(file, keywords):
    file_bytes = io.BytesIO(file.read())  # Convert SpooledTemporaryFile to BytesIO
    doc = Document(file_bytes)
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            for keyword in keywords:
                run.text = re.sub(r'\b' + re.escape(keyword.strip()) + r'\b', '_' * len(keyword), run.text)
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keywords = request.form['keywords'].split(',')
        file = request.files['document']
        file_extension = file.filename.split('.')[-1]

        if file_extension == 'txt':
            content = file.read().decode('utf-8')
            for keyword in keywords:
                content = re.sub(r'\b' + re.escape(keyword.strip()) + r'\b', '_' * len(keyword), content)
            output = io.BytesIO(content.encode('utf-8'))
            output.seek(0)
            return send_file(output, as_attachment=True, download_name='redacted_document.txt')
        elif file_extension == 'docx':
            output = process_docx(file.stream, keywords)  # Corrected line
            return send_file(output, as_attachment=True, download_name='redacted_document.docx')
        elif file_extension == 'pdf':
            output = process_pdf(file.stream, keywords)
            return send_file(output, as_attachment=True, download_name='redacted_document.pdf')
        else:
            return "Unsupported file format", 400

    # rest of the code remains the same

    return '''
    <!doctype html>
    <html>
    <body>
        <form method="POST" enctype="multipart/form-data">
            <label for="keywords">Enter keywords (comma-separated):</label>
            <input type="text" id="keywords" name="keywords" required><br><br>
            <label for="document">Upload a document:</label>
            <input type="file" id="document" name="document" required><br><br>
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
