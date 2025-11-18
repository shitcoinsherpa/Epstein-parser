# Epstein Case Email & Image Analyzer

A tool to parse, analyze, and visualize emails and images from the House Oversight Committee's Epstein case disclosures.

## Features

- **Email Parser**: Extract and organize 5,711 emails from 2,895 text files
- **Email Threading**: Automatically group related emails into conversations
- **Deduplication**: Identify and consolidate duplicate emails across sources
- **HTML Viewer**: Interactive messaging-style interface with search and filtering
- **Image Analyzer**: AI-powered analysis to identify unique photos vs. known sources
- **Export Options**: CSV export and conversation threading

## Quick Start

### 1. Download Archive Data

The archive files (TEXT/ and IMAGES/ folders) are too large for GitHub. Download them from Google Drive:

**[Google Drive Link - INSERT LINK HERE]**

Extract the downloaded archive to this directory. You should have:
```
epstein-email-analyzer/
├── TEXT/
│   ├── 001/  (2,049 files)
│   └── 002/  (846 files)
├── IMAGES/
│   └── 001-012/ (22,903 images)
└── [other project files]
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

The Gradio interface will open at `http://localhost:7860`

## Usage

### Email Parser

1. Click **"Parse All Documents"** to extract emails from TEXT/ folders
2. View statistics and top senders/recipients
3. Click any sender/recipient to view their emails
4. Click **"Export to HTML"** to generate static HTML viewer

### HTML Viewer

After exporting, open `output/index.html` in your browser for:
- Messaging-style conversation view
- Full-text search (keyword or exact phrase with quotes)
- Filter by sender (from/to Epstein)
- Export conversations to CSV
- Responsive mobile-friendly design

### Image Analyzer (Optional)

1. Get a free API key from [OpenRouter](https://openrouter.ai/)
2. Go to the **Image Analyzer** tab
3. Enter your API key
4. Select folder(s) to process
5. View analysis results in `output/image-analysis.html`

## Project Structure

```
├── app.py                  # Main Gradio application
├── email_parser.py         # Email extraction and parsing logic
├── email_threading.py      # Conversation threading and deduplication
├── html_generator_v2.py    # Static HTML viewer generator
├── gemini_analyzer.py      # Image analysis with Gemini AI
├── regenerate_html.py      # Quick HTML regeneration utility
├── requirements.txt        # Python dependencies
└── output/                 # Generated HTML files (auto-created)
```

## Email Statistics

- **Total Emails**: 5,711 (after deduplication)
- **From Epstein**: 3,536
- **Unique Senders**: 438
- **Date Range**: Various dates in 2010-2017

## Known Epstein Email Addresses

- jeeitunes@gmail.com
- jeevacation@gmail.com

## Technical Details

### Email Formats Supported

1. **Traditional Format**:
   ```
   From: sender@example.com
   Sent: Date
   To: recipient@example.com
   Subject: Subject line

   Body content...
   ```

2. **Message Format** (GUID-based):
   ```
   Message: GUID
   Sender: sender@example.com
   Time: timestamp

   Body content...
   ```

### OCR Error Correction

The parser includes robust OCR error correction for:
- Broken URLs (spaces in date paths, file extensions)
- Malformed email addresses
- Date/time parsing errors
- Sender/recipient name cleanup

### Deduplication

Emails are deduplicated based on:
- From + To + Timestamp + Body snippet
- Duplicate sources are tracked in `_duplicate_sources` field

## Output Files

- `emails_parsed.json` - All parsed emails with metadata
- `output/index.html` - Interactive HTML viewer
- `output/assets/` - CSS, JavaScript, and data files
- `image_analysis_results.json` - Image analysis results (if run)

## Contributing

This tool was created for transparency and public analysis of the Epstein case disclosures. Contributions welcome via pull requests.

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool analyzes publicly available documents from the House Oversight Committee's Epstein case disclosures. All data is from official government sources.

## Data Source

House Oversight Committee - Epstein Case Disclosures
Total Files: 2,895 text documents + 22,903 images

## Support

For issues or questions, please open a GitHub issue.
