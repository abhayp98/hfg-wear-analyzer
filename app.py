import streamlit as st
import cv2
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="HFG Wear Calibration Pro", page_icon="🦷", layout="centered")

st.title("🦷 HFG Precision Wear Engine")
st.write("Click directly on the resized image below to secure highly accurate metric data.")

# Factory baseline constants for HuFriedyGroup #100 Thin
factory_nominal_length_mm = 12.5

sku_selection = st.selectbox("Selected Geometry Profile", ["#100 Thin", "#10 Universal", "#1000 Triple Bend"])
uploaded_file = st.file_uploader("Upload Insert Photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Read Image files
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, 1)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    # --- FIXED: Resize image so it fits perfectly on a mobile/desktop browser screen ---
    target_width = 600
    h_orig, w_orig, _ = img_rgb.shape
    aspect_ratio = h_orig / w_orig
    target_height = int(target_width * aspect_ratio)
    
    # Perform standard interpolation resize
    img_resized = cv2.resize(img_rgb, (target_width, target_height), interpolation=cv2.INTER_AREA)
    h, w, _ = img_resized.shape

    st.subheader("2. Interactive Frame Calibration")
    mode = st.radio("Select point to define by clicking the image:", 
                    ["1. Set Grip-to-Metal Junction (Baseline)", "2. Set Absolute Tip Apex"])
    
    # Initialize trackers using the resized boundaries
    if "baseline_y" not in st.session_state: st.session_state.baseline_y = int(h * 0.7)
    if "apex_y" not in st.session_state: st.session_state.apex_y = int(h * 0.3)
    # Calibrated pixels per mm for a 600px wide image window
    if "scale_pixels_per_mm" not in st.session_state: st.session_state.scale_pixels_per_mm = 15.0

    # Draw visual overlays dynamically onto the resized viewport canvas
    preview_img = img_resized.copy()
    cv2.line(preview_img, (0, st.session_state.baseline_y), (w, st.session_state.baseline_y), (255, 0, 0), 3) # Blue Baseline
    cv2.circle(preview_img, (int(w/2), st.session_state.apex_y), 8, (0, 255, 0), -1) # Green Tip Tracker

    st.caption("👇 Tap/Click the image below to move the active marker to the true boundary position.")
    
    # Capture the mouse click coordinates relative to the resized frame
    value = streamlit_image_coordinates(preview_img, key="coords")

    if value is not None:
        clicked_x = value["x"]
        clicked_y = value["y"]
        
        if "1. Set" in mode:
            st.session_state.baseline_y = clicked_y
            st.rerun()
        elif "2. Set" in mode:
            st.session_state.apex_y = clicked_y
            st.rerun()

    # Manual adjustments for scaling factor precision
    st.session_state.scale_pixels_per_mm = st.number_input(
        "Calibrated Camera Scale (Pixels per Millimeter)", 
        min_value=1.0, max_value=100.0, value=st.session_state.scale_pixels_per_mm, step=0.1
    )

    # Step 3: Run Math Equations
    pixel_distance =
