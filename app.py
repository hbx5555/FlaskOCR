import os
import requests
import base64
import traceback
import sys
import json
from flask import Flask, request, Response, jsonify
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


# --- Configuration ---
# Feature toggle for OCR approach
# Set to 'reference_based' to use the original approach with reference image
# Set to 'direct' to use the new approach without reference image
# 
# To switch between approaches:
# 1. In development: Set the OCR_APPROACH environment variable locally
#    export OCR_APPROACH=direct  # For the new approach without reference image
#    export OCR_APPROACH=reference_based  # For the original approach (default)
# 
# 2. In Heroku: Use the Heroku CLI or dashboard to set config vars
#    heroku config:set OCR_APPROACH=direct
#    heroku config:set OCR_APPROACH=reference_based
OCR_APPROACH = os.environ.get('OCR_APPROACH', 'direct')

# --- Reference Image ---
# Using a publicly accessible URL for the reference document instead of embedding it as base64
# This avoids issues with base64 encoding in the deployed environment
REFERENCE_IMAGE_URL = "https://xpertlink.agency/wp-content/uploads/2025/08/רישוי_שנתי.jpg"

# --- Gemini Model ---
# Using a model that is good for multimodal tasks.
# Using flash model due to quota limitations with pro
model = genai.GenerativeModel('gemini-2.0-flash')

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
            <p><strong>Response:</strong> JSON object with extracted field values</p>
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

        # 3. Choose OCR approach based on feature toggle
    if OCR_APPROACH == 'reference_based':
        # Original approach with reference image
        try:
            print("Using reference-based OCR approach")
            print("Fetching reference image from URL...")
            reference_response = requests.get(REFERENCE_IMAGE_URL, timeout=10)
            reference_response.raise_for_status()
            reference_image = Image.open(BytesIO(reference_response.content))
            print("Reference image fetched successfully")
        except Exception as e:
            error_msg = f"Error fetching reference image: {str(e)}"
            print(error_msg)
            return Response(error_msg, status=500, mimetype='text/plain')

        # 4. Define the prompt with specific instructions for the AI with JSON output
        prompt = """
You are an expert document analysis assistant. Your task is to first learn the spatial location of fields from a reference document using the provided text and example values. Then, you must find the data at those *exact same spatial locations* in a new, second document.

Here are your instructions for learning from the reference document: From the reference image, learn the locations of the following fields: 'דגם' is 'GD9EL5R' and 'רמת גימור' is 'GX'.

Now, using the locations you have just learned, analyze the new document and extract the corresponding values.

Your output must be a valid JSON object with the following structure:
{
    "דגם": "[extracted model value]",
    "רמת גימור": "[extracted trim level value]"
}

Do not include any other text or formatting outside of this JSON structure.
"""

        try:
            # 5. Send the request to the Gemini API
            print("Sending request to Gemini API...")
            print(f"API Key configured: {'Yes' if os.environ.get('GOOGLE_API_KEY') else 'No'}")
            api_response = model.generate_content([prompt, reference_image, new_image])
            
            # Parse the response as JSON
            # The response might have code blocks or other formatting, so we need to extract just the JSON
            response_text = api_response.text.strip()
            # Remove any markdown code block markers if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '', 1)
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse the JSON
            json_data = json.loads(response_text)
            
            # Return the JSON response
            return jsonify(json_data)
        except json.JSONDecodeError as e:
            # Handle JSON parsing errors
            error_msg = f"Error parsing JSON response: {str(e)}\nResponse text: {api_response.text}"
            print(error_msg)
            return Response(error_msg, status=500, mimetype='text/plain; charset=utf-8')
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
            return Response(f"Error communicating with the AI model:\nError Type: {error_type}\nError Message: {error_msg}", status=500, mimetype='text/plain; charset=utf-8')
            
    else:  # OCR_APPROACH == 'direct'
        # New approach without reference image
        print("Using direct OCR approach without reference image")
        
        # Define a simpler prompt that directly asks for field extraction with JSON output
        prompt = """
You are an expert document analysis assistant for vehicle registration documents in Hebrew. 

Analyze the provided image of a vehicle registration document and extract the following fields:
1. 'דגם' (Model) - This field appears on the document and contains the vehicle model code.
2. 'רמת גימור' (Trim Level) - This field appears on the document and contains the trim level code.

Your output must be a valid JSON object with the following structure:
{
    "דגם": "[extracted model value]",
    "רמת גימור": "[extracted trim level value]"
}

Do not include any other text or formatting outside of this JSON structure.
"""

        try:
            # Send the request to the Gemini API with only the new image
            print("Sending request to Gemini API with direct approach...")
            print(f"API Key configured: {'Yes' if os.environ.get('GOOGLE_API_KEY') else 'No'}")
            api_response = model.generate_content([prompt, new_image])
            
            # Parse the response as JSON
            # The response might have code blocks or other formatting, so we need to extract just the JSON
            response_text = api_response.text.strip()
            # Remove any markdown code block markers if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '', 1)
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse the JSON
            json_data = json.loads(response_text)
            
            # Return the JSON response
            return jsonify(json_data)
        except json.JSONDecodeError as e:
            # Handle JSON parsing errors
            error_msg = f"Error parsing JSON response: {str(e)}\nResponse text: {api_response.text}"
            print(error_msg)
            return Response(error_msg, status=500, mimetype='text/plain; charset=utf-8')
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
            return Response(f"Error communicating with the AI model:\nError Type: {error_type}\nError Message: {error_msg}", status=500, mimetype='text/plain; charset=utf-8')
        


# --- Run the Application ---
if __name__ == '__main__':
    # Get port from environment variable (Heroku sets this automatically)
    port = int(os.environ.get("PORT", 5000))
    
    # In production, host should be '0.0.0.0' to accept connections from any IP
    # Debug mode should be turned off in production
    app.run(host='0.0.0.0', port=port, debug=False)