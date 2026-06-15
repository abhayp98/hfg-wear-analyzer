import streamlit as st
import cv2
import numpy as np

st.set_page_config(page_title="HFG Precision Wear Engine", page_icon="🦷", layout="centered")

st.title("🦷 HFG Precision Wear Engine")
st.write("Use the sliders below to manually align the measurement markers to your insert.")

# Factory baseline constant for #100 Thin
factory_nominal_length_mm = 12.5

sku_selection = st.selectbox("Selected Geometry Profile", ["#100 Thin", "#10 Universal", "#1000 Triple Bend"])
uploaded_file = st.file_uploader("Upload Insert Photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Read and decode the image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, 1)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    # Scale image down cleanly so it fits perfectly on your screen
    h_orig, w_orig, _ = img_rgb.shape
    max_dimension = 600
    if h_orig > w_orig:
        scale_factor = max_dimension / h_orig
        target_height = max_dimension
        target_width = int(w_orig * scale_factor)
    else:
        scale_factor = max_dimension / w_orig
        target_width = max_dimension
        target_height = int(h_orig * scale_factor)
        
    img_resized = cv2.resize(img_rgb, (target_width, target_height), interpolation=cv2.INTER_AREA)
    h, w, _ = img_resized.shape

    # --- NO CLICKING REQUIRED: Use precision manual sliders ---
    st.subheader("2. Alignment Controls")
    st.markdown("Move these sliders until the visual lines on the photo match your insert perfectly.")
    
    # Sliders match the exact pixel height of your photo dynamically
    apex_y = st.slider("Move Green Line to the very TIP APEX", min_value=0, max_value=h, value=int(h * 0.3))
    baseline_y = st.slider("Move Blue Line to the GRIP JUNCTION (Base)", min_value=0, max_value=h, value=int(h * 0.7))
    
    # Adjustment for camera zoom factor
    scale_pixels_per_mm = st.number_input(
        "Camera Zoom Scale (Pixels per Millimeter)", 
        min_value=1.0, max_value=100.0, value=15.0, step=0.1
    )

    # Draw the lines onto your image in real-time
    preview_img = img_resized.copy()
    # Green line for the fine tip apex
    cv2.line(preview_img, (0, apex_y), (w, apex_y), (0, 255, 0), 2)
    cv2.circle(preview_img, (int(w/2), apex_y), 6, (0, 255, 0), -1)
    
    # Blue line for the base junction where metal meets handle
    cv2.line(preview_img, (0, baseline_y), (w, baseline_y), (0, 0, 255), 2)
    cv2.circle(preview_img, (int(w
