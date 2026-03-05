import streamlit as st
from rembg import remove
from PIL import Image, ImageOps
import io
import numpy as np
import cv2
import zipfile

# --- CẤU HÌNH ---
st.set_page_config(page_title="Auto Passport Photo Maker", layout="wide")

SIZE_CHART = {
    "2x3 cm": (236, 354),
    "3x4 cm": (354, 472),
    "4x6 cm": (472, 709),
    "Hộ chiếu (3.5x4.5 cm)": (413, 531)
}

BG_COLORS = {
    "Nền Trắng": (255, 255, 255),
    "Nền Xanh Dương (Chuẩn)": (0, 51, 153),
    "Nền Xanh Dương (Sáng)": (0, 112, 192)
}

# --- THUẬT TOÁN TỰ ĐỘNG CẮT CHUẨN ẢNH THẺ ---
def auto_crop_id_photo(pil_image, target_size):
    """
    Tự động nhận diện khuôn mặt và cắt theo tỉ lệ chuẩn ảnh thẻ
    """
    # Chuyển đổi sang định dạng OpenCV
    open_cv_image = np.array(pil_image)
    if len(open_cv_image.shape) == 3 and open_cv_image.shape[2] == 3: # RGB
        open_cv_image = open_cv_image[:, :, ::-1].copy() # Sang BGR
    elif len(open_cv_image.shape) == 3 and open_cv_image.shape[2] == 4: # RGBA
        open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGR)
        
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    
    # Nhận diện khuôn mặt
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
    
    if len(faces) == 0:
        return pil_image # Trả về ảnh gốc nếu không thấy mặt
        
    # Lấy khuôn mặt lớn nhất (đề phòng có người phía sau)
    faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
    x, y, w, h = faces[0]
    
    # Tính toán kích thước cắt theo tỉ lệ vàng
    target_w, target_h = target_size
    aspect_ratio = target_w / target_h
    
    # Chiều cao khuôn mặt chiếm khoảng 60% chiều cao ảnh chuẩn
    new_h = int(h / 0.6)
    new_w = int(new_h * aspect_ratio)
    
    # Tọa độ tâm khuôn mặt
    cx = x + w // 2
    
    # Tọa độ khung cắt
    left = cx - new_w // 2
    right = left + new_w
    # Chừa một khoảng trống trên đầu (khoảng 10% chiều cao ảnh)
    top = int(y - h * 0.1 - new_h * 0.1)
    bottom = top + new_h
    
    # Xử lý trường hợp khung cắt vượt ra ngoài ảnh (Thêm viền bù đắp - padding)
    img_h, img_w = open_cv_image.shape[:2]
    pad_left = max(0, -left)
    pad_top = max(0, -top)
    pad_right = max(0, right - img_w)
    pad_bottom = max(0, bottom - img_h)
    
    # Tạo ảnh có viền nội suy để bù vào phần thiếu hụt
    padded_img = cv2.copyMakeBorder(open_cv_image, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_REPLICATE)
    
    # Cập nhật lại tọa độ cắt trên ảnh đã bù viền
    new_left = left + pad_left
    new_top = top + pad_top
    new_right = right + pad_left
    new_bottom = bottom + pad_top
    
    cropped_cv = padded_img[new_top:new_bottom, new_left:new_right]
    
    # Chuyển ngược về PIL
    cropped_rgb = cv2.cvtColor(cropped_cv, cv2.COLOR_BGR2RGB)
    return Image.fromarray(cropped_rgb)

# --- GIAO DIỆN CHÍNH ---
st.title("📸 Máy Tạo Ảnh Thẻ AI Tự Động Hàng Loạt")
st.markdown("Tải lên nhiều ảnh cùng lúc. AI sẽ tự động tìm khuôn mặt, cắt theo tỉ lệ vàng, thay nền và nén thành file ZIP cho bạn.")

# Cài đặt Sidebar
st.sidebar.header("Cài đặt chung")
size_label = st.sidebar.selectbox("Kích thước:", list(SIZE_CHART.keys()))
bg_label = st.sidebar.selectbox("Phông nền:", list(BG_COLORS.keys()))
target_size = SIZE_CHART[size_label]
target_bg_color = BG_COLORS[bg_label]

# Upload nhiều ảnh
uploaded_files = st.file_uploader("Tải lên một hoặc nhiều ảnh...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 Bắt đầu xử lý tất cả"):
        # Tạo file ZIP trong bộ nhớ ảo
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            
            # Tạo lưới hiển thị ảnh (3 ảnh 1 hàng)
            cols = st.columns(3)
            
            progress_bar = st.progress(0)
            st.write(f"Đang xử lý {len(uploaded_files)} ảnh...")
            
            for index, file in enumerate(uploaded_files):
                col = cols[index % 3] # Phân bổ vào các cột
                
                with col:
                    st.caption(f"Ảnh: {file.name}")
                    try:
                        # 1. Đọc và chỉnh hướng ảnh
                        img = Image.open(file).convert("RGB")
                        img = ImageOps.exif_transpose(img)
                        
                        # 2. Tự động cắt chuẩn ảnh thẻ
                        cropped_img = auto_crop_id_photo(img, target_size)
                        
                        # 3. Tách nền bằng Rembg
                        no_bg_img = remove(cropped_img)
                        
                        # 4. Tạo phông nền và dán ảnh
                        final_img = Image.new("RGB", no_bg_img.size, target_bg_color)
                        final_img.paste(no_bg_img, (0, 0), no_bg_img)
                        
                        # 5. Resize về đúng Pixel
                        final_img = final_img.resize(target_size, Image.LANCZOS)
                        
                        # Hiển thị
                        st.image(final_img, use_container_width=True)
                        
                        # Lưu vào file ZIP ảo
                        img_byte_arr = io.BytesIO()
                        final_img.save(img_byte_arr, format='JPEG', quality=95)
                        zip_file.writestr(f"anhthe_{size_label}_{file.name}", img_byte_arr.getvalue())
                        
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
                
                # Cập nhật thanh tiến trình
                progress_bar.progress((index + 1) / len(uploaded_files))
                
        st.success("🎉 Đã xử lý xong toàn bộ ảnh!")
        
        # Nút tải xuống file ZIP
        st.download_button(
            label="⬇️ TẢI XUỐNG TẤT CẢ (File ZIP)",
            data=zip_buffer.getvalue(),
            file_name="anh_the_hang_loat.zip",
            mime="application/zip"
        )
