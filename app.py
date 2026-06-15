import streamlit as st
import cv2
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="HFG Wear Calibration Pro", page_icon="🦷", layout="centered")

st.title("🦷 HFG Calibrated Wear Engine")
st.write("Click directly on your image points below to secure highly accurate metric data.")

# Set up defaults for #100 Thin reference scaling
factory_nominal_length_mm = 12.5

# Step 1: Profile metadata
sku_selection = st.selectbox("Selected Geometry Profile", ["#100 Thin", "#10 Universal", "#1000 Triple Bend"])
uploaded_file = st.file_uploader("Upload Insert Photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Read Image files
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, 1)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w, _ = img_rgb.shape

    # Set up interactive mode steps
    st.subheader("2. Interactive Frame Calibration")
    mode = st.radio("Select point to define by clicking the image:", 
                    ["1. Set Grip-to-Metal Junction (Baseline)", "2. Set Absolute Tip Apex"])
    
    # Initialize point trackers in session states
    if "baseline_y" not in st.session_state: st.session_state.baseline_y = int(h * 0.7)
    if "apex_y" not in st.session_state: st.session_state.apex_y = int(h * 0.3)
    if "scale_pixels_per_mm" not in st.session_state: st.session_state.scale_pixels_per_mm = 25.0

    # Draw visual overlays dynamically onto the source canvas
    preview_img = img_rgb.copy()
    cv2.line(preview_img, (0, st.session_state.baseline_y), (w, st.session_state.baseline_y), (0, 0, 255), 4) # Blue/Red Baseline
    cv2.circle(preview_img, (int(w/2), st.session_state.apex_y), 10, (0, 255, 0), -1) # Green Tip Tracker

    st.caption("👇 Tap/Click the image below to move the active marker to the true boundary position.")
    
    # Capture the mouse click coordinates via plugin module
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
        min_value=5.0, max_value=100.0, value=st.session_state.scale_pixels_per_mm, step=0.1
    )

    # Step 3: Run Deterministic Math Equations
    pixel_distance = abs(st.session_state.baseline_y - st.session_state.apex_y)
    calculated_length_mm = pixel_distance / st.session_state.scale_pixels_per_mm
    wear_delta_mm = abs(factory_nominal_length_mm - calculated_length_mm)

    # Status classification evaluation loops
    if wear_delta_mm <= 0.5:
        status = "NOMINAL EFFICIENCY"
        color = "green"
    elif 0.5 < wear_delta_mm <= 1.5:
        status = "25% WEAR (REORDER STRATEGY ALERT)"
        color = "orange"
    else:
        status = "50% SEVERE DEGRADATION (SCRAP VALUE)"
        color = "red"

    # Step 4: Metric Display Terminal Layout
    st.subheader("3. Validated Calibration Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Measured Base-to-Tip", f"{calculated_length_mm:.2f} mm")
    col2.metric("Calculated Wear Delta", f"{wear_delta_mm:.2f} mm")
    col3.markdown(f"Status:<br>:{color}[**{status}**]", unsafe_allow_html=True)

    st.write(f"**Verification Check:** Line baseline is set at Y={st.session_state.baseline_y}px. Apex target point is locked at Y={st.session_state.apex_y}px.")
