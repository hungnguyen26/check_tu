# app.py
import streamlit as st
import fitz  # PyMuPDF
from io import BytesIO
from google import genai  # Gemini AI SDK

# ==========================
# CẤU HÌNH GEMINI
# ==========================
API_KEY = "AIzaSyDfTc99o-Uid51Ce8pFBKB0gPXrPX9fTkA"  # Thay bằng API key Gemini thật
client = genai.Client(api_key=API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"  # Hoặc gemini-2.0 tùy quyền truy cập

# ==========================
# HÀM KIỂM TRA LỖI
# ==========================
def check_with_gemini(text: str) -> list:
    """
    Gửi văn bản tiếng Việt tới Gemini AI để check lỗi:
    - Dính chữ, xuống dòng sai, lặp từ, số & chữ, …
    Trả về danh sách lỗi (mỗi lỗi trên 1 dòng)
    """
    prompt = f"""
Bạn là chuyên gia kiểm tra văn bản tiếng Việt.
Văn bản:
{text}

Hãy liệt kê tất cả các lỗi sau:
1. Các từ dính nhau không cách.
2. Xuống dòng sai, ngắt câu sai.
3. Lặp từ.
4. Số dưới 10 ghi số thay vì chữ, số >= 10 ghi chữ thay vì số.

Trả về danh sách các từ/cụm từ vi phạm, mỗi lỗi trên 1 dòng, không giải thích thêm.
"""
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        result_text = response.text
        errors = [line.strip("-• \n") for line in result_text.split("\n") if line.strip()]
        return errors
    except Exception as e:
        st.error(f"Lỗi khi gọi Gemini AI: {e}")
        return []

# ==========================
# HÀM HIGHLIGHT PDF
# ==========================
# ==========================
# HÀM HIGHLIGHT PDF (MÀU ĐỎ NHẠT)
# ==========================
def highlight_pdf_with_errors(pdf_bytes: bytes, errors: list) -> bytes:
    """
    Bôi đỏ nhạt tất cả các lỗi đã được AI phát hiện trên PDF
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # Màu đỏ nhạt (RGB: 1.0, 0.6, 0.6)
    highlight_color = (1, 0.6, 0.6)
    
    for page in doc:
        for err in errors:
            # Tìm tất cả vị trí xuất hiện từ/cụm từ
            for inst in page.search_for(err):
                # Thêm highlight annotation
                annot = page.add_highlight_annot(inst)
                # Đặt màu đỏ nhạt
                annot.set_colors(stroke=highlight_color)  # stroke = màu viền highlight
                annot.update()
    
    out = BytesIO()
    doc.save(out)
    return out.getvalue()


# ==========================
# STREAMLIT WEB
# ==========================
st.set_page_config(page_title="PDF Checker tiếng Việt + Gemini AI")
st.title("PDF Checker nâng cao - Gemini AI")

st.markdown("""
Tool này kiểm tra lỗi tiếng Việt trong PDF (dính chữ, xuống dòng sai, lặp từ, số & chữ, v.v.) và highlight các lỗi.  
Gemini AI sẽ tự động phân tích toàn bộ văn bản tiếng Việt trong PDF.
""")

uploaded_file = st.file_uploader("Chọn file PDF", type=["pdf"])
if uploaded_file:
    st.info("Đang xử lý, vui lòng chờ…")
    pdf_bytes = uploaded_file.read()

    # Lấy toàn bộ văn bản PDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"

    # Kiểm tra lỗi bằng Gemini AI
    errors = check_with_gemini(full_text)

    if errors:
        highlighted_pdf = highlight_pdf_with_errors(pdf_bytes, errors)
        st.success("Hoàn tất kiểm tra lỗi!")
        st.download_button(
            label="Tải file PDF đã bôi đỏ",
            data=highlighted_pdf,
            file_name="checked_" + uploaded_file.name,
            mime="application/pdf"
        )

        st.markdown("### Danh sách lỗi phát hiện:")
        for e in errors:
            st.write(f"- {e}")
    else:
        st.success("Không tìm thấy lỗi nào trong PDF.")
