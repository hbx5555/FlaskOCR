import os
import requests
import base64
import traceback
import sys
from flask import Flask, request, Response
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# --- Application Setup ---
app = Flask(__name__)

# --- API Key Configuration ---
# IMPORTANT: It's best practice to set your API key as an environment variable
# rather than writing it directly in the code.
# On your terminal, you can set it like this:
# export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
# The code will then automatically pick it up.
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
except ValueError as e:
    print(f"Error: {e}")
    print("Please set your GOOGLE_API_KEY environment variable.")
    # You can also hardcode it here for quick testing, but this is NOT recommended for production:
    # api_key = "YOUR_API_KEY_GOES_HERE" 
    # genai.configure(api_key=api_key)


# --- Reference Image ---
# Using a publicly accessible URL for the reference document instead of embedding it as base64
# This avoids issues with base64 encoding in the deployed environment
REFERENCE_IMAGE_URL = "https://xpertlink.agency/wp-content/uploads/2025/08/רישוי_שנתי.jpg"

# --- Gemini Model ---
# Using a model that is good for multimodal tasks.
model = genai.GenerativeModel('gemini-1.5-Pro')

# --- Flask Routes ---
@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint that provides basic information about the API.
    """
    welcome_message = """
    <html>
    <head>
        <title>Flask OCR API</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            h2 { color: #555; }
            pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
            code { font-family: monospace; }
            .endpoint { background: #e9f7ef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>Flask OCR Document Field Extraction API</h1>
        <p>This API extracts specific fields from document images using Google's Gemini Multimodal AI.</p>
        
        <h2>Available Endpoints:</h2>
        <div class="endpoint">
            <h3>Extract Document Fields</h3>
            <p><strong>Endpoint:</strong> <code>/extract</code></p>
            <p><strong>Method:</strong> GET</p>
            <p><strong>Parameters:</strong></p>
            <ul>
                <li><code>image_url</code> - URL of the image to analyze (required)</li>
            </ul>
            <p><strong>Example:</strong></p>
            <pre>GET /extract?image_url=https://example.com/path/to/image.jpg</pre>
            <p><strong>Response:</strong> Plain text with extracted field values</p>
        </div>
        
        <p>For more information, visit the <a href="https://github.com/hbx5555/FlaskOCR">GitHub repository</a>.</p>
    </body>
    </html>
    """
    return Response(welcome_message, mimetype='text/html')

@app.route('/extract', methods=['GET'])
def extract_document_fields():
    """
    This endpoint receives a URL to an image, fetches it, and uses Gemini
    to extract fields based on a reference image.
    """
    # 1. Get the image URL from the request arguments
    image_url = request.args.get('image_url')
    if not image_url:
        return Response("Error: Please provide an 'image_url' parameter.", status=400, mimetype='text/plain')

    try:
        # 2. Fetch the new image from the provided URL
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        new_image_bytes = response.content
        new_image = Image.open(BytesIO(new_image_bytes))

    except requests.exceptions.RequestException as e:
        return Response(f"Error fetching image from URL: {e}", status=400, mimetype='text/plain')
    except Exception as e:
        return Response(f"Error processing image: {e}", status=500, mimetype='text/plain')

    # 3. Prepare images for the Gemini API - fetch reference image from URL
    try:
        print("Fetching reference image from URL...")
        reference_response = requests.get(REFERENCE_IMAGE_URL, timeout=10)
        reference_response.raise_for_status()
        reference_image = Image.open(BytesIO(reference_response.content))
        print("Reference image fetched successfully")
    except Exception as e:
        error_msg = f"Error fetching reference image: {str(e)}"
        print(error_msg)
        return Response(error_msg, status=500, mimetype='text/plain')

    # 4. Define the prompt with specific instructions for the AI
    prompt = """
You are an expert document analysis assistant. Your task is to first learn the spatial location of fields from a reference document using the provided text and example values. Then, you must find the data at those *exact same spatial locations* in a new, second document.

Here are your instructions for learning from the reference document: From the reference image, learn the locations of the following fields: 'דגם' is 'GD9EL5R' and 'רמת גימור' is 'GX'.

Now, using the locations you have just learned, analyze the new document and extract the corresponding values. Your output must be formatted on exactly four lines as follows:
1. The literal text "דגם:"
2. The extracted value for the 'דגם' field.
3. The literal text "רמת גימור:"
4. The extracted value for the 'רמת גימור' field.
Do not include any other text or formatting.
"""

    try:
        # 5. Send the request to the Gemini API
        print("Sending request to Gemini API...")
        print(f"API Key configured: {'Yes' if os.environ.get('GOOGLE_API_KEY') else 'No'}")
        api_response = model.generate_content([prompt, reference_image, new_image])
        
        # 6. Return the extracted text as a plain text response
        return Response(api_response.text, mimetype='text/plain; charset=utf-8')

    except Exception as e:
        # Get detailed error information
        error_type = type(e).__name__
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        
        # Log the error details
        print(f"Error Type: {error_type}")
        print(f"Error Message: {error_msg}")
        print(f"Stack Trace: {stack_trace}")
        
        # Return a more informative error response
        error_details = f"Error Type: {error_type}\nError Message: {error_msg}"
        return Response(f"Error communicating with the AI model:\n{error_details}", 
                       status=500, mimetype='text/plain')


# --- Run the Application ---
if __name__ == '__main__':
    # Get port from environment variable (Heroku sets this automatically)
    port = int(os.environ.get("PORT", 5000))
    
    # In production, host should be '0.0.0.0' to accept connections from any IP
    # Debug mode should be turned off in production
    app.run(host='0.0.0.0', port=port, debug=False)