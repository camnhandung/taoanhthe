import streamlit as st
from rembg import remove
from PIL import Image, ImageOps
import io
import numpy as np
import cv2 # Cần cho chức năng căn giữa tự động
from streamlit_cropper import st_cropper # Thư viện cắt ảnh tương tác

# --- CẤU HÌNH ---
st.set_page_config(page_title="Pro Passport Photo Maker", layout="wide")

# Kích thước chuẩn (300 DPI)
SIZE_CHART = {
    "2x3 cm": (236, 354),
    "3x4 cm": (354, 472),
    "4x6 cm": (472, 709),
    "Hộ chiếu (3.5x4.5 cm)": (413, 531)
}

# Màu nền chuẩn
BG_COLORS = {
    "Nền Trắng": (255, 255, 255),
    "Nền Xanh Dương (Chuẩn)": (0, 51, 153), # Màu xanh chuẩn ảnh thẻ
    "Nền Xanh Dương (Sáng)": (0, 112, 192)
}

# --- HÀM HỖ TRỢ ---
def get_face_center(pil_image):
    """Sử dụng OpenCV để tìm tâm khuôn mặt"""
    # Chuyển PIL sang OpenCV (BGR)
    open_cv_image = np.array(pil_image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    
    # Tải bộ phân loại khuôn mặt mặc định
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) == 0:
        return None # Không tìm thấy khuôn mặt
    
    # Lấy khuôn mặt đầu tiên (lớn nhất)
    (x, y, w, h) = faces[0]
    # Trả về tâm khuôn mặt (x_center, y_center)
    return (x + w//2, y + h//2)

def autocenter_image(pil_image, target_ratio):
    """Cắt ảnh sao cho tâm khuôn mặt nằm giữa khung hình theo tỉ lệ chuẩn"""
    face_center = get_face_center(pil_image)
    
    if face_center is None:
        st.warning("⚠️ Không nhận diện được khuôn mặt để tự động căn giữa. Sử dụng vùng cắt thủ công.")
        return pil_image

    img_w, img_h = pil_image.size
    face_x, face_y = face_center
    target_w_ratio, target_h_ratio = target_ratio
    
    # Tính toán kích thước vùng cắt dựa trên tỉ lệ đích
    # Chúng ta muốn lấy vùng lớn nhất có thể xung quanh khuôn mặt
    curr_ratio = img_w / img_h
    target_ratio_val = target_w_ratio / target_h_ratio

    if curr_ratio > target_ratio_val:
        # Ảnh quá rộng, cắt theo chiều cao
        new_h = img_h
        new_w = int(new_h * target_ratio_val)
    else:
        # Ảnh quá cao, cắt theo chiều rộng
        new_w = img_w
        new_h = int(new_w / target_ratio_val)
        
    # Tính toán tọa độ cắt (left, top, right, bottom) sao cho face_center nằm giữa
    left = face_x - new_w // 2
    top = face_y - new_h // 2
    right = face_x + new_w // 2
    bottom = face_y + new_h // 2
    
    # Xử lý trường hợp vùng cắt vượt ra ngoài biên ảnh gốc
    if left < 0:
        right -= left
        left = 0
    if top < 0:
        bottom -= top
        top = 0
    if right > img_w:
        left -= (right - img_w)
        right = img_w
    if bottom > img_h:
        top -= (bottom - img_h)
        bottom = img_h
        
    return pil_image.crop((left, top, right, bottom))

# --- GIAO DIỆN CHÍNH ---
st.title("📸 Máy Tạo Ảnh Thẻ Chuyên Nghiệp Pro")
st.markdown("Cắt ảnh, tự động căn giữa, tách nền và chọn phông nền chuẩn.")

# 1. Sidebar - Cài đặt
st.sidebar.header("1. Cài đặt ảnh")
size_label = st.sidebar.selectbox("Kích thước ảnh thẻ:", list(SIZE_CHART.keys()))
bg_label = st.sidebar.selectbox("Màu nền ảnh thẻ:", list(BG_COLORS.keys()))
target_size = SIZE_CHART[size_label]
target_bg_color = BG_COLORS[bg_label]

st.sidebar.markdown("---")
st.sidebar.header("2. Tùy chọn nâng cao")
do_autocenter = st.sidebar.checkbox("Tự động căn giữa khuôn mặt", value=True, help="Nếu bật, AI sẽ cố gắng đưa khuôn mặt bạn vào giữa. Nếu tắt, sẽ dùng chính xác vùng bạn cắt thủ công.")

# 2. Vùng Upload và Cắt ảnh (Main Body)
uploaded_file = st.file_uploader("Tải ảnh chân dung của bạn lên...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    col1, col2 = st.columns(2)
    
    input_image = Image.open(uploaded_file)
    input_image = ImageOps.exif_transpose(input_image) # Sửa lỗi ảnh bị ngược trên điện thoại

    with col1:
        st.subheader("Bước 1: Cắt ảnh thủ công (để chọn vùng đẹp)")
        st.caption("Hãy kéo khung màu đỏ để chọn vùng ảnh bạn muốn lấy.")
        
        # Công cụ cắt ảnh tương tác
        # Khóa tỉ lệ theo kích thước ảnh thẻ đã chọn
        aspect_ratio = (target_size[0], target_size[1])
        cropped_img = st_cropper(input_image, realtime_update=True, box_color='#FF0000', aspect_ratio=aspect_ratio)
        
        # Hiển thị ảnh sau khi cắt thủ công
        st.image(cropped_img, caption="Vùng đã cắt thủ công", width=200)

    with col2:
        st.subheader("Bước 2: Xử lý và Kết quả")
        process_btn = st.button("Tạo ảnh thẻ ngay")

        if process_btn:
            with st.spinner("Đang xử lý (Tách nền + Căn chỉnh)..."):
                
                # --- Xử lý 1: Căn giữa (nếu chọn) ---
                image_to_process = cropped_img
                if do_autocenter:
                    # Gửi ảnh đã cắt thủ công vào để AI căn giữa tinh xảo hơn
                    image_to_process = autocenter_image(cropped_img, aspect_ratio)

                # --- Xử lý 2: Tách nền ---
                # Chuyển về RGB để tách nền sạch hơn nếu cần
                if image_to_process.mode == 'CMYK':
                    image_to_process = image_to_process.convert('RGB')
                    
                no_bg_img = remove(image_to_process)
                
                # --- Xử lý 3: Thay nền mới ---
                # Tạo phông nền màu chuẩn
                final_img = Image.new("RGB", no_bg_img.size, target_bg_color)
                # Dán ảnh đã tách nền lên
                final_img.paste(no_bg_img, (0, 0), no_bg_img)
                
                # --- Xử lý 4: Resize về kích thước chuẩn cuối cùng ---
                final_img = final_img.resize(target_size, Image.LANCZOS)

                # --- Hiển thị kết quả ---
                st.success("Đã hoàn thành!")
                st.image(final_img, caption=f"Ảnh thẻ {size_label}", width=target_size[0]//2) # Hiển thị nhỏ lại cho đẹp trên web

                # --- Nút tải về ---
                buf = io.BytesIO()
                final_img.save(buf, format="JPEG", quality=95)
                byte_im = buf.getvalue()
                st.download_button(
                    label=f"⬇️ Tải ảnh {size_label} về máy",
                    data=byte_im,
                    file_name=f"anh_the_{size_label.replace(' ', '_')}.jpg",
                    mime="image/jpeg"
                )
