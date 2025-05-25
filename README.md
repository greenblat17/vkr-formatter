# VKR Formatter 🎓

A powerful FastAPI-based service that automatically formats VKR (Graduate Qualification Work) documents according to GOST standards. The service features a modular architecture with intelligent content detection and comprehensive document formatting capabilities.

## ✨ Features

- 🤖 **AI-Powered Requirements Extraction**

  - Uses GPT-3.5 to intelligently parse formatting requirements
  - Handles complex and unstructured requirement documents
  - Extracts detailed formatting rules automatically

- 🧠 **Intelligent Content Detection**

  - Automatic detection of title pages, table of contents, and main content
  - Smart paragraph classification (H1, H2, lists, regular text)
  - Complex regex patterns for content recognition

- 📝 **Comprehensive GOST Formatting**

  - Font settings (Times New Roman, sizes, styles)
  - Paragraph formatting (alignment, indentation, spacing)
  - Document structure (margins, sections, page numbering)
  - Proper handling of academic document sections

- 🚀 **Easy Integration**

  - Simple REST API endpoint
  - FastAPI-powered with automatic OpenAPI documentation
  - Support for .docx files
  - Real-time processing with detailed statistics

- 📊 **Advanced Processing**
  - Skips service sections (title pages, task assignments)
  - Properly handles table of contents with page numbers
  - State-based document processing
  - Comprehensive error handling and logging

## 🛠️ Prerequisites

- Python 3.8 or higher
- Basic understanding of REST APIs
- .docx files for processing

## 📦 Installation

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/vrk-formatter.git
cd vrk-formatter
```

2. **Set up virtual environment:**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment:**

```bash
# Create .env file
touch .env  # On Windows: type nul > .env

# Add your OpenAI API key
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## 🚀 Usage

1. **Start the server:**

```bash
uvicorn api:app --reload --port 8000
```

2. **Access the API:**

   - API will be available at `http://localhost:8000`
   - Interactive documentation at `http://localhost:8000/docs`
   - Check service status: `http://localhost:8000/`
   - View default requirements: `http://localhost:8000/requirements`
   - Check processing statistics: `http://localhost:8000/stats`

3. **Format your document:**
   - Send a POST request to `/format` with:
     - `vkr`: Your VKR document (.docx)
   - The service uses built-in GOST requirements
   - Receive the formatted document in response

### 📝 Example Requests

**Using curl:**

```bash
curl -X POST "http://localhost:8000/format" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "vkr=@path/to/your/vkr.docx" \
  --output formatted_vkr.docx
```

**Using Python requests:**

```python
import requests

url = "http://localhost:8000/format"
files = {
    'vkr': ('vkr.docx', open('path/to/vkr.docx', 'rb'))
}

response = requests.post(url, files=files)
with open('formatted_vkr.docx', 'wb') as f:
    f.write(response.content)
```

**Check service status:**

```bash
curl http://localhost:8000/
curl http://localhost:8000/requirements
curl http://localhost:8000/stats
```

## 📁 Project Structure

```
vrk-formatter/
├── api.py                      # FastAPI application entry point
├── vkr_formatter.py           # Main formatter orchestrator
├── formatting_constants.py    # Formatting constants and mappings
├── document_state.py          # Document processing state management
├── content_detector.py        # Content type detection logic
├── paragraph_classifier.py    # Paragraph classification
├── paragraph_formatter.py     # Paragraph formatting implementation
├── statistics_tracker.py      # Processing statistics tracking
├── vkr_requirements_stub.py   # Default GOST requirements
├── logger_config.py           # Logging configuration
├── __init__.py                # Package initialization
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

### 🏗️ Modular Architecture

The project follows a clean modular architecture with separation of concerns:

- **`FormattingConstants`**: Centralized constants for alignment, spacing, and content markers
- **`DocumentState`**: Manages document processing state (title, contents, main content sections)
- **`ContentDetector`**: Intelligent detection of different content types using regex patterns
- **`ParagraphClassifier`**: Classifies paragraphs into types (skip, h1, h2, list, regular)
- **`ParagraphFormatter`**: Applies formatting rules to different paragraph types
- **`StatisticsTracker`**: Tracks processing metrics and statistics
- **`VKRFormatter`**: Main orchestrator that coordinates all components

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔄 Version History

- **v2.0.0**: Modular architecture refactoring
- **v1.x**: Initial monolithic implementation
