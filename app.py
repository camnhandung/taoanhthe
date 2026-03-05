import streamlit as st
from PIL import Image
import rembg
import io

st.title("Công cụ tạo ảnh thẻ tự động")

# Upload ảnh
uploaded_file = st.file_uploader("Tải ảnh chân dung lên", type=["jpg", "jpeg", "png"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Ảnh gốc", use_column_width=True)

    # Tách nền
    input_bytes = uploaded_file.read()
    output_bytes = rembg.remove(input_bytes)
    output_image = Image.open(io.BytesIO(output_bytes))

    st.image(output_image, caption="Ảnh đã tách nền", use_column_width=True)

    # Chọn màu nền
    bg_color = st.color_picker("Chọn màu nền", "#FFFFFF")
    bg = Image.new("RGB", output_image.size, bg_color)
    bg.paste(output_image, (0,0), output_image)
    st.image(bg, caption="Ảnh thẻ với nền mới", use_column_width=True)

    # Chọn kích thước
    size_option = st.selectbox("Chọn kích thước ảnh thẻ", ["2x3 cm", "3x4 cm", "4x6 cm"])
    dpi = 300  # chuẩn in
    cm_to_px = lambda cm: int(cm/2.54 * dpi)
    if size_option == "2x3 cm":
        size = (cm_to_px(2), cm_to_px(3))
    elif size_option == "3x4 cm":
        size = (cm_to_px(3), cm_to_px(4))
    else:
        size = (cm_to_px(4), cm_to_px(6))

    final_img = bg.resize(size)
    st.image(final_img, caption=f"Ảnh thẻ {size_option}", use_column_width=False)

    # Tải xuống
    buf = io.BytesIO()
    final_img.save(buf, format="JPEG")
    st.download_button("Tải ảnh thẻ", buf.getvalue(), file_name="anh_the.jpg", mime="image/jpeg")
