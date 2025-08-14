# Flask OCR - Document Field Extraction API

A Flask-based REST API that extracts specific fields from document images using Google's Gemini Multimodal AI. The application compares a new document against a reference document to extract fields from the same spatial locations.

## 📋 Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Local Development](#local-development)
  - [Heroku Deployment](#heroku-deployment)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- **REST API Endpoint**: Simple GET endpoint that accepts an image URL
- **Document Field Extraction**: Extracts specific fields from documents based on spatial location
- **Multimodal AI Processing**: Uses Google's Gemini 1.5 Flash model for image analysis
- **Reference-Based Extraction**: Compares new documents against a reference document
- **Heroku-Ready**: Configured for easy deployment to Heroku

## 🔍 How It Works

1. The application stores a reference document image (encoded as base64)
2. When a new image URL is provided via the API, the app:
   - Downloads the image
   - Sends both the reference and new images to the Gemini API
   - Instructs the AI to extract specific fields from the same spatial locations
   - Returns the extracted text

## 📋 Prerequisites

- Python 3.8+
- Google API key with access to Gemini models
- Internet connection (for accessing the Gemini API)

## 🚀 Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/hbx5555/FlaskOCR.git
   cd FlaskOCR
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.template .env
   ```
   Edit the `.env` file and add your Google API key:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

5. **Run the application**
   ```bash
   python app.py
   ```
   The app will be available at http://localhost:5000

### Heroku Deployment

1. **Login to Heroku CLI**
   ```bash
   heroku login
   ```

2. **Create a new Heroku app**
   ```bash
   heroku create flask-ocr-app  # You can choose any available name
   ```

3. **Set up your Google API key**
   ```bash
   heroku config:set GOOGLE_API_KEY=your_actual_google_api_key_here
   ```

4. **Deploy to Heroku**
   ```bash
   git push heroku master
   ```

5. **Open your app**
   ```bash
   heroku open
   ```

## 📝 Usage

To extract fields from a document image:

```
GET /extract?image_url=https://example.com/path/to/image.jpg
```

Example using curl:
```bash
curl "http://localhost:5000/extract?image_url=https://example.com/path/to/image.jpg"
```

Example response:
```
דגם:
GD9EL5R
רמת גימור:
GX
```

## 📚 API Reference

### GET /extract

Extracts fields from a document image based on a reference document.

**Query Parameters:**
- `image_url` (required): URL of the image to analyze

**Response:**
- Content-Type: text/plain; charset=utf-8
- Body: Extracted field values in plain text format

**Status Codes:**
- 200: Success
- 400: Bad request (missing image_url or invalid URL)
- 500: Server error (processing error or API error)

## 📁 Project Structure

```
FlaskOCR/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── Procfile           # Heroku deployment configuration
├── .env.template      # Template for environment variables
└── .gitignore        # Git ignore configuration
```

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GOOGLE_API_KEY | API key for Google Gemini | Yes |
| PORT | Port for the web server (default: 5000) | No |
| DEBUG | Enable debug mode (default: False) | No |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Built with ❤️ using Flask and Google Gemini AI
