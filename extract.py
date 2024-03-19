import fitz  # imports the pymupdf library

doc = fitz.open("example.pdf")  # open a document

with open("example.txt", "w") as f:  # Open the file once for writing
    for page in doc:  # iterate the document pages
        text = page.get_text()  # get plain text encoded as UTF-8
        f.write(text)  # append the text to the file