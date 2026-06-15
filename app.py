import streamlit as st
import numpy as np
from PIL import Image, ImageDraw

st.set_page_config(page_title="HFG Precision Wear Engine", page_icon="🦷", layout="centered")

st.title("🦷 HFG Precision Wear Engine")
st.write("Use the sliders below to manually align the measurement markers to your insert.")

# Factory baseline constant for #100 Thin
factory_nominal_length_mm = 12.5

sku_selection = st.selectbox("Selected Geometry Profile", ["#100 Thin", "#10 Universal", "#1000 Triple Bend"])
uploaded_file = st.file_uploader("Upload Insert Photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    try:
        # --- FIXED: Use PIL instead of OpenCV to safely open any smartphone image format ---
        img_raw = Image.open(uploaded_file)
        
        # Normalize orientation based on phone camera metadata
        img_raw = img_raw.convert("RGB")
        
        # Scale image down cleanly so it fits perfectly on your screen
        w_orig, h_orig = img_raw.size
        max_dimension = 600
        
        if h_orig > w_orig:
            scale_factor = max_dimension / h_orig
            target_height = max_dimension
            target_width = int(w_orig * scale_factor)
        else:
            scale_factor = max_dimension / w_orig
            target_width = max_dimension
            target_height = int(h_orig * scale_factor)
            
        img_resized = img_raw.resize((target_width, target_height), Image.Resampling.LANCZOS)
        w, h = img_resized.size

        st.subheader("2. Alignment Controls")
        st.markdown("Move these sliders until the visual lines on the photo match your insert perfectly.")
        
        # Set interactive sliders based on the safe resized image height
        apex_y = st.slider("Move Green Line to the very TIP APEX", min_value=0, max_value=h, value=int(h * 0.3))
        baseline_y = st.slider("Move Blue Line to the GRIP JUNCTION (Base)", min_value=0, max_value=h, value=int(h * 0.7))
        
        scale_pixels_per_mm = st.number_input(
            "Camera Zoom Scale (Pixels per Millimeter)", 
            min_value=1.0, max_value=100.0, value=15.0, step=0.1
        )

        # Draw the target lines directly onto a copy of the image using PIL
        preview_img = img_resized.copy()
        draw = ImageDraw.Draw(preview_img)
        
        # Green line for the tip apex
        draw.line([(0, apex_y), (w, apex_y)], fill=(0, 255, 0), width=3)
        draw.ellipse([(int(w/2)-6, apex_y-6), (int(w/2)+6, apex_y+6)], fill=(0, 255, 0))
        
        # Red line for the handle baseline
        draw.line([(0, baseline_y), (w, baseline_y)], fill=(255, 0, 0), width=3)
        draw.ellipse([(int(w/2)-6, baseline_y-6), (int(w/2)+6, baseline_y+6)], fill=(255, 0, 0))

        # Render the final composite image on the webpage safely
        st.image(preview_img, caption="Live Alignment Preview", use_column_width=True)

        # Step 3: Math Engine Calculations
        pixel_distance = abs(baseline_y - apex_y)
        calculated_length_mm = pixel_distance / scale_pixels_per_mm
        wear_delta_mm = abs(factory_nominal_length_mm - calculated_length_mm)

        # Threshold evaluation matching HFG constraints
        if wear_delta_mm <= 0.5:
            status = "NOMINAL EFFICIENCY"
            color = "green"
            msg = "Instrument is sharp and performing within factory limits."
        elif 0.5 < wear_delta_mm <= 1.5:
            status = "25% EFFICIENCY LOSS"
            color = "orange"
            msg = "Tip wear detected. Flag account for a replacement reorder."
        else:
            status = "50% CRITICAL WEAR"
            color = "red"
            msg = "Severe wear. Discard instrument immediately to prevent clinical inefficiencies."

        # Step 4: Display Results Dashboard
        st.subheader("3. Diagnostic Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Measured Tip Length", f"{calculated_length_mm:.2f} mm")
        col2.metric("Calculated Wear Delta", f"{wear_delta_mm:.2f} mm")
        col3.markdown(f"Status:<br>:{color}[**{status}**]", unsafe_allow_html=True)
        
        st.info(f"💡 **Clinical Advice:** {msg}")
        
    except Exception as e:
        st.error(f"Error compiling image processor data: {str(e)}")
