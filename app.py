import streamlit as st
import cv2
import numpy as np

# Set up clean page config
st.set_page_config(page_title="HFG Wear Analyzer", page_icon="🦷", layout="centered")

st.title("🦷 HFG Insert Wear Analyzer")
st.write("Upload a flat, top-down photo of your ultrasonic insert to analyze tip degradation.")

# 1. Customer Information Data Input
st.subheader("1. Customer & SKU Profiling")
clinic_name = st.text_input("Clinic / Customer Name")
sku_selection = st.selectbox("Select Insert Geometry SKU", ["#100 Thin", "#10 Universal", "#1000 Triple Bend"])

# 2. Camera Instructions Guidance Matrix
st.info("""
📸 **How to take a perfect analysis photo:**
1. Place the instrument completely flat on a dark, non-reflective surface.
2. Hold your smartphone directly above the instrument (do not tilt the lens).
3. Ensure bright, even lighting with no harsh shadows blocking the metal tip.
""")

# 3. Image Capture Interface
uploaded_file = st.file_uploader("Capture or Upload Photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Convert file stream to openCV image matrix
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    
    # Run Image Preprocessing (Grayscale + Adaptive Thresholding)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Trace Contours to find the extreme tip coordinate
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        # Identify the apex boundary (highest point in pixel space)
        ext_top = tuple(largest_contour[largest_contour[:, :, 1].argmin()][0])
        
        # UI Sliders to allow user to manually calibrate baseline errors 
        st.subheader("2. Precise Scale Calibration")
        st.caption("Adjust the parameters below if the raw photo zoom varies.")
        scale_ratio = st.slider("Pixel-to-Millimeter Ratio Scale", 10.0, 50.0, 24.5)
        baseline_pixel = st.slider("Handle Grip Starting Y-Baseline", 100, 800, 450)
        
        # Calculate Delta 
        measured_length_pixels = abs(baseline_pixel - ext_top[1])
        calculated_length_mm = measured_length_pixels / scale_ratio
        
        # Reference constraints for #100 Thin (Example factory baseline: 12.5mm)
        factory_nominal_mm = 12.5
        wear_delta_mm = abs(factory_nominal_mm - calculated_length_mm)
        
        # Logic Classification Loop
        if wear_delta_mm <= 0.6:
            status = "OPTIMAL CONDITION"
            color = "green"
            msg = "Instrument performing within nominal spec margins."
        elif 0.6 < wear_delta_mm <= 1.5:
            status = "25% EFFICIENCY LOSS (REORDER RECOMMENDED)"
            color = "orange"
            msg = "Tip is approaching lifecycle threshold limits. Order replacement units."
        else:
            status = "50% CRITICAL WEAR (DISCARD IMMEDIATELY)"
            color = "red"
            msg = "Severe clinical scaling inefficiency. Scrap and replace instrument."
            
        # 4. Render Interactive Dashboard Output
        st.subheader("3. Automated Diagnostic Audit Report")
        st.metric(label="Calculated Tip Wear Delta", value=f"{wear_delta_mm:.2f} mm")
        
        st.markdown(f"**Diagnostic Status:** :{color}[{status}]")
        st.write(f"**Action Recommended:** {msg}")
        
        # Draw target diagnostic overlays on the final rendered preview
        cv2.circle(img, ext_top, 12, (0, 0, 255), -1) # Red tracking point at tip apex
        cv2.line(img, (0, baseline_pixel), (img.shape[1], baseline_pixel), (255, 0, 0), 3) # Blue baseline
        
        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Processed Target Edge Detection Overlays", use_column_width=True)
    else:
        st.error("Unable to securely segment metal components. Check contrast.")
