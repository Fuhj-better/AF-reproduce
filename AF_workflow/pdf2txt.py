from pypdf import PdfReader

def pdf_to_txt_pypdf(pdf_path, txt_path):
    """
    使用 pypdf 库将 PDF 文本内容提取到 TXT 文件。
    """
    try:
        reader = PdfReader(pdf_path)
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text() + "\n" # 提取每页文本并用换行符分隔

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        print(f"'{pdf_path}' 已成功转换为 '{txt_path}' (使用 pypdf)。")
    except Exception as e:
        print(f"转换 '{pdf_path}' 时发生错误 (pypdf): {e}")

# 示例用法
# 创建一个测试用的PDF文件（如果手头没有的话）
# 实际项目中你需要将 'input.pdf' 替换为你自己的PDF文件路径
# from reportlab.pdfgen import canvas
# c = canvas.Canvas("input.pdf")
# c.drawString(100, 750, "Hello, this is page 1.")
# c.drawString(100, 700, "This is some more text.")
# c.showPage()
# c.drawString(100, 750, "This is page 2.")
# c.save()

input_pdf = "../pdf/apb.pdf"  # 你的PDF文件路径
output_txt = "../input/apb.txt" # 输出的TXT文件路径

pdf_to_txt_pypdf(input_pdf, output_txt)