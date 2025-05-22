# VKR Formatter 🎓

A powerful FastAPI-based service that automatically formats VKR (Graduate Qualification Work) documents according to university requirements. The service uses GPT-3.5 to intelligently extract formatting rules from requirements documents and applies them to your VKR document with precision.

## ✨ Features

- 🤖 **AI-Powered Requirements Extraction**

  - Uses GPT-3.5 to intelligently parse formatting requirements
  - Handles complex and unstructured requirement documents
  - Extracts detailed formatting rules automatically

- 📝 **Comprehensive Formatting**

  - Font settings (name, size, style)
  - Paragraph formatting (alignment, indentation, spacing)
  - Document structure (margins, sections, page numbering)
  - Table and figure formatting
  - Citation and reference formatting

- 🚀 **Easy Integration**
  - Simple REST API endpoint
  - FastAPI-powered with automatic OpenAPI documentation
  - Support for .docx files
  - Real-time processing

## 🛠️ Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Basic understanding of REST APIs

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
uvicorn main:app --reload
```

2. **Access the API:**

   - API will be available at `http://localhost:8000`
   - Interactive documentation at `http://localhost:8000/docs`

3. **Format your document:**
   - Send a POST request to `/process` with:
     - `vkr`: Your VKR document (.docx)
     - `requirements`: Requirements document (.docx)
   - Receive the formatted document in response

### 📝 Example Requests

**Using curl:**

```bash
curl -X POST "http://localhost:8000/process" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "vkr=@path/to/your/vkr.docx" \
  -F "requirements=@path/to/your/requirements.docx" \
  --output formatted_vkr.docx
```

**Using Python requests:**

```python
import requests

url = "http://localhost:8000/process"
files = {
    'vkr': ('vkr.docx', open('path/to/vkr.docx', 'rb')),
    'requirements': ('requirements.docx', open('path/to/requirements.docx', 'rb'))
}

response = requests.post(url, files=files)
with open('formatted_vkr.docx', 'wb') as f:
    f.write(response.content)
```

## 📁 Project Structure

```
vrk-formatter/
├── main.py                 # FastAPI application entry point
├── utils/
│   ├── extract_requirements.py  # GPT-based requirements extraction
│   └── apply_formatting.py      # Document formatting logic
├── requirements.txt        # Project dependencies
├── .env                   # Environment variables (not in git)
└── README.md              # Project documentation
```

## 🔧 Development

### Setting up development environment:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the requirements.txt if you add new dependencies
3. Ensure all tests pass
4. The PR will be merged once you have the sign-off of at least one other developer

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com) for providing the GPT API
- [python-docx](https://python-docx.readthedocs.io/) for document manipulation
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

## 📞 Support

If you encounter any issues or have questions:

- Open an issue in the GitHub repository
- Contact the maintainers
- Check the [FAQ](docs/FAQ.md) for common questions

## 🔄 Updates

Stay updated with the latest changes by:

- Watching the repository
- Following the [changelog](CHANGELOG.md)
- Checking the [releases page](https://github.com/yourusername/vrk-formatter/releases)
