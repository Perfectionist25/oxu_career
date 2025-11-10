from weasyprint import HTML

html = HTML(string="<h1>Привет, OXU!</h1>")
pdf = html.write_pdf()
with open("test.pdf", "wb") as f:
    f.write(pdf)
