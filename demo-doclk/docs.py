from docling.document_converter import DocumentConverter 
source = "https://arxiv.org/pdf/2408.09869.pdf" 
converter = DocumentConverter() 
doc = converter.convert(source).document 
# Export to markdown 
print(doc.export_to_markdown())
 