import streamlit as st
import os
from dotenv import load_dotenv
from PIL import Image
import tempfile
from src.ai_service import enhance_image, animate_image

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Life Photos", page_icon="📸", layout="wide")

st.title("📸 Life Photos")
st.markdown("### Bring your old photos to life using Google's Veo 3.1 & Nano Banana")

if "GOOGLE_API_KEY" not in os.environ:
    st.error("Please set the GOOGLE_API_KEY environment variable in your .env file.")
    st.stop()

# Sidebar controls
st.sidebar.header("Settings")
action = st.sidebar.radio("Choose Action", ["Enhance Quality (Nano Banana)", "Animate (Veo 3.1)"])

uploaded_file = st.file_uploader("Upload an old photo...", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    # Display original image
    image = Image.open(uploaded_file)
    st.image(image, caption="Original Photo", use_container_width=True)

    if st.button("Process Photo"):
        with st.spinner(f"Processing with {action}..."):
            try:
                # Save uploaded file to temp for processing if needed
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    image.save(tmp_file.name)
                    tmp_path = tmp_file.name
                
                if action == "Enhance Quality (Nano Banana)":
                    # Call enhancement service
                    result_path = enhance_image(tmp_path)
                    if result_path:
                        st.success("Enhancement Complete!")
                        st.image(result_path, caption="Enhanced Photo", use_container_width=True)
                    else:
                        st.error("Enhancement failed.")

                elif action == "Animate (Veo 3.1)":
                    # Call animation service
                    video_path = animate_image(tmp_path)
                    if video_path:
                        st.success("Animation Complete!")
                        st.video(video_path)
                    else:
                        st.error("Animation failed.")
                
                # Cleanup temp file
                os.remove(tmp_path)

            except Exception as e:
                st.error(f"An error occurred: {e}")
