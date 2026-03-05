import streamlit as st
from rembg import remove
from PIL import Image
import io

# Cấu hình các kích thước chuẩn (Đơn vị: mm -> px với 300 DPI)
# Công thức: px = (mm * 300) / 25.4
SIZE_CHART = {
    "2x3 cm": (236, 354),
    "3x4 cm": (354, 472),
    "4x6 cm": (472, 709),
    "Passport (3.5x4.5 cm)": (413, 531)
}

st.set_page_config(page_title="AI Passport Photo Maker", layout="centered")

st.title("📸 Máy Tạo Ảnh Thẻ AI")
st.write("Tách nền và tạo ảnh thẻ chuyên nghiệp trong vài giây.")

# 1. Upload file
uploaded_file = st.file_uploader("Tải ảnh chân dung của bạn lên...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # Hiển thị ảnh gốc
    input_image = Image.open(uploaded_file)
    st.image(input_image, caption="Ảnh gốc", use_container_width=True)

    # 2. Cài đặt thông số
    st.sidebar.header("Cài đặt ảnh thẻ")
    bg_color = st.sidebar.color_picker("Chọn màu nền", "#003399") # Mặc định xanh dương
    size_label = st.sidebar.selectbox("Chọn kích thước ảnh", list(SIZE_CHART.keys()))
    
    if st.button("Bắt đầu xử lý"):
        with st.spinner("Đang tách nền và căn chỉnh..."):
            # Bước 1: Tách nền
            no_bg_img = remove(input_image)
            
            # Bước 2: Tạo nền mới
            target_size = SIZE_CHART[size_label]
            # Tạo một phông nền màu thuần túy
            final_img = Image.new("RGB", no_bg_img.size, bg_color)
            # Dán ảnh đã tách nền lên phông màu
            final_img.paste(no_bg_img, (0, 0), no_bg_img)
            
            # Bước 3: Resize theo chuẩn
            final_img = final_img.resize(target_size, Image.LANCZOS)

            # Hiển thị kết quả
            st.success("Hoàn thành!")
            st.image(final_img, caption=f"Ảnh thẻ {size_label} của bạn", width=250)

            # Nút tải về
            buf = io.BytesIO()
            final_img.save(buf, format="JPEG")
            byte_im = buf.getvalue()
            st.download_button(
                label="Tải ảnh về máy",
                data=byte_im,
                file_name=f"anh_the_{size_label.replace(' ', '_')}.jpg",
                mime="image/jpeg"
            )