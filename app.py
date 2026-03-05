import streamlit as st
import os
import json
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener
from src.processor import PhotoProcessor

# Register HEIF opener for Pillow
register_heif_opener()

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Life Photos", page_icon="📸", layout="wide")

# Custom CSS for Animations and Layout
st.markdown("""
<style>
    @keyframes slideInUp {
        0% { transform: translateY(20px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }
    
    .status-text {
        animation: slideInUp 0.5s ease-out forwards;
        font-size: 1.2rem;
        font-weight: 500;
        color: #4A4A4A;
        padding: 10px;
        border-left: 4px solid #FF4B4B;
        background-color: #F0F2F6;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    
    /* Dark mode adjustment for status text */
    @media (prefers-color-scheme: dark) {
        .status-text {
            color: #FAFAFA;
            background-color: #262730;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("📸 Life Photos")
st.markdown("### Bring your photos to life with Cinematic AI")

# API Key Check
if "GOOGLE_API_KEY" not in os.environ:
    st.error("Please set the GOOGLE_API_KEY environment variable in your .env file.")
    st.stop()

# Initialize Processor
processor = PhotoProcessor()

# Main Layout: 50/50 Split
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Select Photo")
    uploaded_file = st.file_uploader("Upload a photo...", type=["jpg", "jpeg", "png", "webp", "heic"])

    # Initialize start_process to False
    start_process = False

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        width, height = image.size
        st.image(image, use_container_width=True, caption=f"Original ({width}x{height})")
        
        # Action Button inside Left Column
        start_process = st.button("Bring to Life ✨", type="primary", use_container_width=True)
    else:
        st.info("Upload a photo to get started.")
        st.markdown("""
        **How it works:**
        1. **Smart Analysis:** Detects subject, mood, and lighting.
        2. **Fidelity Correction:** Upscales (x2) only if needed.
        3. **Cinematic Animation:** Generates a high-quality video matching the photo's vibe.
        
        **Privacy Focus:** Strict identity preservation enabled.
        """)

with col_right:
    st.subheader("2. Cinematic Creation")
    
    # Placeholders for dynamic content
    status_placeholder = st.empty()
    video_placeholder = st.empty()
    debug_expander = st.empty()

    if uploaded_file is not None:
        # Check if button was clicked
        if 'start_process' in locals() and start_process:
            # Temp file management
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Handle HEIC conversion for compatibility
            if uploaded_file.name.lower().endswith(".heic"):
                try:
                    # Reset pointer and open
                    uploaded_file.seek(0)
                    image_heic = Image.open(uploaded_file)
                    image_rgb = image_heic.convert("RGB")
                    
                    # Save as JPG
                    new_filename = os.path.splitext(uploaded_file.name)[0] + ".jpg"
                    temp_path = os.path.join(temp_dir, new_filename)
                    image_rgb.save(temp_path, format="JPEG", quality=95)
                except Exception as heic_err:
                    st.error(f"Error converting HEIC file: {heic_err}")
                    st.stop()
            else:
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                # Reset pointer for safety, though getbuffer usually works
                uploaded_file.seek(0) 
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            try:
                # Define callback for updates
                def update_ui(msg):
                    if isinstance(msg, str):
                        # Animated Status Update
                        status_placeholder.markdown(f'<div class="status-text">{msg}</div>', unsafe_allow_html=True)
                    else:
                        # It's an Operation object or generic data from Veo
                        # We can display the raw metadata in the expander
                        try:
                            # Try to extract meaningful metadata or raw json
                            meta = getattr(msg, 'metadata', str(msg))
                            with debug_expander.container():
                                with st.expander("🔌 AI Provider Response (Veo 3.1)", expanded=True):
                                    st.write("Live Operation State:")
                                    st.write(meta)
                        except Exception:
                            pass
                
                # Run Pipeline
                result = processor.process_workflow(temp_path, status_callback=update_ui)
                
                if result.success:
                    status_placeholder.markdown('<div class="status-text" style="border-color: #00CC00;">✨ Transformation Complete!</div>', unsafe_allow_html=True)
                    
                    # Display Video
                    if result.video_path:
                        with video_placeholder.container():
                            st.video(result.video_path, autoplay=True, loop=True)
                            with open(result.video_path, "rb") as v:
                                st.download_button(
                                    "Download Video 🎬", 
                                    v, 
                                    file_name=f"life_photo_{uploaded_file.name}.mp4",
                                    mime="video/mp4",
                                    use_container_width=True
                                )
                else:
                    status_placeholder.markdown(f'<div class="status-text" style="border-color: #FF0000;">❌ Processing Failed: {result.error}</div>', unsafe_allow_html=True)
                    st.error(f"Error Details: {result.error}")

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
