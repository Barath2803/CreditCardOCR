import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json
import re

st.set_page_config(page_title='CreditCardOCR', 
                   page_icon = ":credit_card:", 
                   layout = 'wide', 
                   initial_sidebar_state = 'auto')


# Extract necessary info from ocr response
def extract_info(labels):
    account_number_pattern_1 = re.compile(r'\b(?:\d{1,4}\s*){1,2}\d{2,4}\s?\d{2,4}\s?\d{2,4}\s?\d{1,4}\b')
    account_number_pattern_2 = r'\b\d+\b'
    validity_date_pattern = re.compile(r'\b(?:THRU)?\d{2}\s*/\s*\d{2}\b')
    name_pattern_1 = re.compile(r'^[A-Z.]{1,23}\s[A-Z. ]{1,23}$')
    
    result = {
        'account_number': None,
        'account_holder_name': None,
        'validity_date': None
    }
    splitted_acc_number = ""
    for label in labels:
        if account_number_pattern_1.match(label):
            label = label.replace(" ", "")
            if len(label) > 16:
                label = label[:16]
            formatted_label = ' '.join([label[i:i+4] for i in range(0, len(label), 4)])
            result['account_number'] = formatted_label
        if result['account_number'] is None or len(result['account_number']) < 19:
            numbers = re.findall(account_number_pattern_2, label)
            splitted_acc_number += ' '.join(numbers)
            
        if validity_date_pattern.search(label):
            match = validity_date_pattern.search(label).group(0)
            result['validity_date'] = re.sub(r'[^/\d]', '', match)
            
        if name_pattern_1.match(label) and not account_number_pattern_1.match(label) and not validity_date_pattern.match(label):
            result['account_holder_name'] = label
            
    if result['account_number'] is None or len(result['account_number']) != 19:
        splitted_acc_number = splitted_acc_number.replace(" ", "")
        if len(splitted_acc_number) == 0:
            result['account_number'] = None
        if len(splitted_acc_number) > 16:
            splitted_acc_number = splitted_acc_number[:16]
        splitted_acc_number = ' '.join([splitted_acc_number[i:i+4] for i in range(0, len(splitted_acc_number), 4)])
        result['account_number'] = splitted_acc_number
    return result

def get_predictions(image):
    url = "http://127.0.0.1:8000/predict"
    response = requests.post(url, json={'image_paths': image})
    response_json = json.loads(response.content.decode('utf-8'))
    labels = response_json['<OCR_WITH_REGION>']['labels']
    return labels

def main():
    st.title('Credit Card OCR Extraction')
    st.divider()
    
    uploaded_file = st.file_uploader("**Choose an image...**", type=["jpg", "jpeg", "png"])
    image_uploaded = False  # Flag to track if an image is uploaded
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_path = "images/temp.jpg"
        image.save(image_path)
        image_uploaded = True  # Set flag to True when image is uploaded
    
    if image_uploaded:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Card")
            st.image(image.resize((280, 180)), 
                     # caption='Uploaded Image', 
                     use_column_width=True)
        
        with st.status('Extracting...', expanded=True) as status:
            predictions = get_predictions(image_path)
            status.update(label="Extraction complete!", state="complete", expanded=False)
        labels = extract_info(predictions)
        
        with col2:
            st.subheader("OCR Output")
            for key, value in labels.items():
                if key == "account_number":
                    st.code(f"Account Number: {value}")
                elif key == "account_holder_name":
                    st.code(f"Holder Name: {value}")
                else:
                    st.code(f"Valid Date: {value}")
    else:
        st.info("Upload an image to see OCR output.")

if __name__ == "__main__":
    main()
