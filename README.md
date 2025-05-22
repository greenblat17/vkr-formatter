# VKR Formatter

A FastAPI-based service that automatically formats VKR (Graduate Qualification Work) documents according to university requirements. The service extracts formatting rules from a requirements document and applies them to the VKR document.

## Features

- Extract formatting requirements from a requirements document using GPT-3.5
- Apply formatting rules to VKR documents including:
  - Font settings (name, size)
  - Paragraph alignment
  - Indentation
  - Line spacing
  - Margins
  - And more
- FastAPI endpoint for easy integration
- Support for .docx files

## Prerequisites

- Python 3.8+
- OpenAI API key

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/vrk-formatter.git
cd vrk-formatter
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:

```bash
touch .env  # On Windows use: type nul > .env
```

5. Add your OpenAI API key to the `.env` file:

```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

Note: Make sure to add `.env` to your `.gitignore` file to keep your API key secure.

## Usage

1. Start the FastAPI server:

```bash
uvicorn main:app --reload
```

2. The API will be available at `http://localhost:8000`

3. Use the `/process` endpoint to format your VKR document:
   - Send a POST request with two files:
     - `vkr`: Your VKR document (.docx)
     - `requirements`: The requirements document (.docx)
   - The endpoint will return the formatted document

### Example using curl:

```bash
curl -X POST "http://localhost:8000/process" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "vkr=@path/to/your/vkr.docx" \
  -F "requirements=@path/to/your/requirements.docx" \
  --output formatted_vkr.docx
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`

## Project Structure

```
vrk-formatter/
├── main.py                 # FastAPI application
├── utils/
│   ├── extract_requirements.py  # GPT-based requirements extraction
│   └── apply_formatting.py      # Document formatting logic
├── requirements.txt        # Project dependencies
├── .env                   # Environment variables (not in git)
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the GPT API
- python-docx for document manipulation
- FastAPI for the web framework
