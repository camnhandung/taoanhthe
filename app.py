import streamlit as st
import pandas as pd
import json

# Thiết lập cấu hình trang
st.set_page_config(page_title="Excel to JSON Converter", layout="centered")

st.title("Military Data Converter")
st.subheader("Chuyển đổi file Excel sang định dạng JSON")

# Bảng ánh xạ tiêu đề (Mapping)
key_mapping = {
    "Họ tên khai sinh": "fullname_birth",
    "Họ tên thường dùng": "fullname_used",
    "Số hiệu quân nhân": "service_id",
    "Số thẻ QN/CMND": "id_card_num",
    "Số thẻ BHYT": "health_ins_num",
    "Số CCCD": "citizen_id",
    "Ngày tháng năm sinh": "dob",
    "Cấp bậc": "rank",
    "Ngày nhận cấp bậc": "rank_date",
    "Ngày cấp thẻ QN": "id_card_date",
    "Chức vụ": "position",
    "Ngày nhận chức vụ": "position_date",
    "CNQS": "cnqs",
    "Bậc kỹ thuật": "tech_level",
    "Ngày nhập ngũ": "enlist_date",
    "Ngày xuất ngũ": "discharge_date",
    "Ngày tái ngũ": "reenlist_date",
    "Ngày chuyển QNCN": "to_qncn_date",
    "Ngày chuyển CNV": "to_cnv_date",
    "Lương nhóm": "salary_group",
    "Ngạch bậc": "salary_grade",
    "Ngày vào Đoàn": "youth_union_date",
    "Ngày vào Đảng": "party_date",
    "Ngày chính thức": "party_official_date",
    "TP gia đình": "family_background",
    "TP bản thân": "personal_background",
    "Dân tộc": "ethnicity",
    "Tôn giáo": "religion",
    "Văn hoá (12/12)": "education",
    "Ngoại ngữ": "language",
    "Sức khoẻ": "health",
    "Hạng thương tật": "disability",
    "Khen thưởng": "reward",
    "Kỷ luật": "discipline",
    "Tên trường": "school_name",
    "Cấp học": "school_level",
    "Ngành học": "school_major",
    "Thời gian học": "school_time",
    "Nguyên quán": "native_place",
    "Sinh quán": "birth_place",
    "Trú quán": "residence",
    "Báo tin cho ai, ở đâu?": "emergency_contact",
    "Họ tên cha": "father_name",
    "Họ tên mẹ": "mother_name",
    "Họ tên vợ/chồng": "spouse_name",
    "Tổng số con": "children_count"
}

# 1. Widget tải file
uploaded_file = st.file_uploader("Chọn file Excel (.xlsx hoặc .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Đọc dữ liệu từ Excel
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        df = df.fillna("") # Thay thế ô trống bằng chuỗi rỗng

        st.success("Tải file thành công! Đang xử lý dữ liệu...")

        json_list = []
        
        # Xử lý chuyển đổi
        for index, row in df.iterrows():
            entry = {}
            entry["id"] = index + 1
            
            for vn_col, en_key in key_mapping.items():
                if vn_col in df.columns:
                    val = row[vn_col]
                    
                    # Định dạng lại nếu là ngày tháng (tránh lỗi số nguyên Excel)
                    if "date" in en_key or en_key == "dob":
                        if hasattr(val, 'strftime'):
                            val = val.strftime('%d/%m/%Y')
                    
                    # Xử lý số lượng con
                    if en_key == "children_count":
                        try:
                            entry[en_key] = int(val) if val != "" else None
                        except:
                            entry[en_key] = None
                    else:
                        entry[en_key] = str(val).strip()
                else:
                    entry[en_key] = ""
            
            json_list.append(entry)

        # 2. Hiển thị xem trước dữ liệu JSON
        st.write("Xem trước kết quả (5 bản ghi đầu tiên):")
        st.json(json_list[:5])

        # 3. Chuyển đổi sang chuỗi JSON để tải về
        final_json = json.dumps(json_list, ensure_ascii=False, indent=4)

        # Nút tải file về
        st.download_button(
            label="Tải file JSON về máy",
            data=final_json,
            file_name="data_converted.json",
            mime="application/json"
        )

    except Exception as e:
        st.error(f"Đã có lỗi xảy ra: {e}")

else:
    st.info("Vui lòng tải lên file Excel để bắt đầu.")
