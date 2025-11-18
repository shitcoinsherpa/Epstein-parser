import requests
import base64
import json
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set

class GeminiImageAnalyzer:
    """Analyze images using Gemini 2.0 Flash via OpenRouter"""

    def __init__(self, api_key: str, model: str = "google/gemini-2.0-flash-exp:free"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.results = []
        self.image_hashes = {}  # Track image hashes for duplicate detection
        self.stats = {
            "total_images": 0,
            "processed": 0,
            "unique_photos": 0,
            "email_screenshots": 0,
            "legal_docs": 0,
            "book_pages": 0,
            "errors": 0,
            "duplicates": 0
        }

    def load_checkpoint(self, checkpoint_file: str) -> set:
        """Load processed files from checkpoint"""
        if not os.path.exists(checkpoint_file):
            return set()

        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                self.results = checkpoint.get("results", [])
                self.stats = checkpoint.get("stats", self.stats)
                processed = set(r["full_path"] for r in self.results if "full_path" in r)
                print(f"Resuming from checkpoint: {len(processed)} images already processed")
                return processed
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return set()

    def save_checkpoint(self, checkpoint_file: str):
        """Save current progress to checkpoint"""
        checkpoint = {
            "results": self.results,
            "stats": self.stats,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)

    def analyze_all_folders(self, base_path: str, folders: List[str] = None, progress_callback=None, checkpoint_file: str = "image_analysis_checkpoint.json") -> List[Dict]:
        """Analyze all images in specified folders with progress persistence"""

        if folders is None:
            # Default to all 12 folders
            folders = [f"{i:03d}" for i in range(1, 13)]

        # Load checkpoint if exists
        processed_paths = self.load_checkpoint(checkpoint_file)

        all_images = []
        for folder in folders:
            folder_path = Path(base_path) / folder
            if folder_path.exists():
                images = list(folder_path.glob("*.jpg")) + list(folder_path.glob("*.png"))
                all_images.extend([(folder, img) for img in images])

        self.stats["total_images"] = len(all_images)

        for idx, (folder, image_path) in enumerate(all_images):
            # Skip if already processed
            if str(image_path) in processed_paths:
                if progress_callback:
                    progress_callback(idx + 1, len(all_images), folder)
                continue

            try:
                result = self.analyze_image(str(image_path), folder)
                self.results.append(result)
                self.stats["processed"] += 1

                # Update category counts
                category = result.get("category", "UNKNOWN")
                if category == "UNIQUE_PHOTO":
                    self.stats["unique_photos"] += 1
                elif category == "EMAIL_SCREENSHOT":
                    self.stats["email_screenshots"] += 1
                elif category == "LEGAL_DOC":
                    self.stats["legal_docs"] += 1
                elif category == "BOOK_PAGE":
                    self.stats["book_pages"] += 1

                # Save checkpoint every 50 images
                if self.stats["processed"] % 50 == 0:
                    self.save_checkpoint(checkpoint_file)
                    print(f"Checkpoint saved: {self.stats['processed']} images processed")

                if progress_callback:
                    progress_callback(idx + 1, len(all_images), folder)

                # Rate limiting - small delay between requests
                time.sleep(0.3)

            except Exception as e:
                self.stats["errors"] += 1
                self.results.append({
                    "file": str(image_path),
                    "full_path": str(image_path),
                    "folder": folder,
                    "error": str(e),
                    "category": "ERROR"
                })
                print(f"Error analyzing {image_path}: {e}")

        # Final checkpoint save
        self.save_checkpoint(checkpoint_file)
        print(f"Final checkpoint saved: {self.stats['processed']} images processed")

        return self.results

    def compute_image_hash(self, image_data: bytes) -> str:
        """Compute perceptual hash of image for duplicate detection"""
        # Use MD5 hash for exact duplicate detection
        # For perceptual hashing, would need PIL/imagehash library
        return hashlib.md5(image_data).hexdigest()

    def analyze_image(self, image_path: str, folder: str) -> Dict:
        """Analyze a single image using Gemini"""

        # Read and encode image
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
            img_b64 = base64.b64encode(img_data).decode('utf-8')

        # Check for exact duplicates
        img_hash = self.compute_image_hash(img_data)
        if img_hash in self.image_hashes:
            self.stats["duplicates"] += 1
            return {
                "file": os.path.basename(image_path),
                "full_path": image_path,
                "folder": folder,
                "category": "DUPLICATE",
                "description": f"Exact duplicate of {self.image_hashes[img_hash]}",
                "duplicate_of": self.image_hashes[img_hash],
                "hash": img_hash
            }

        # Store hash
        self.image_hashes[img_hash] = os.path.basename(image_path)

        # Determine image type
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"

        # Create enhanced prompt
        prompt = """Analyze this image from the Jeffrey Epstein case disclosures (House Oversight Committee).

CRITICAL INSTRUCTIONS:
- Be VERY selective about UNIQUE_PHOTO category
- Most images are likely book pages, legal docs, or email screenshots
- ONLY categorize as UNIQUE_PHOTO if it's clearly a photograph taken by someone (not a scan of published material)

Categorize as ONE of the following:
1. UNIQUE_PHOTO - An original photograph (NOT from books/magazines/newspapers)
   - Examples: Personal photos, party/event photos, candid shots
   - NOT: Scanned magazine covers, book illustrations, newspaper photos
2. EMAIL_SCREENSHOT - Email or digital message screenshot
3. LEGAL_DOC - Legal document, correspondence, letter, memo, or administrative record
4. BOOK_PAGE - Scanned page from a book, magazine, newspaper, or other published material
   - Include: Magazine articles, book chapters, newspaper clippings

For UNIQUE_PHOTO (be conservative - when in doubt, choose BOOK_PAGE):
- Detailed description of subjects, setting, location if identifiable
- List any recognizable individuals (if clearly identifiable)
- Note unusual or significant details
- Assess investigative relevance: HIGH (contains previously unknown individuals/locations), MEDIUM (known subjects but new context), LOW (mundane/duplicative)

For BOOK_PAGE:
- Identify source if visible (book title, magazine name, publication date)
- Brief content summary
- Is this about Epstein? (yes/no)

For EMAIL_SCREENSHOT or LEGAL_DOC:
- Sender/recipient if visible
- Date if visible
- Brief content summary

Respond ONLY in JSON format (no markdown, no code blocks):
{
  "category": "UNIQUE_PHOTO|EMAIL_SCREENSHOT|LEGAL_DOC|BOOK_PAGE",
  "description": "detailed description",
  "source": "publication source for BOOK_PAGE, empty string otherwise",
  "relevance": "HIGH|MEDIUM|LOW (only for UNIQUE_PHOTO)",
  "individuals": "comma-separated list of identifiable people (only for UNIQUE_PHOTO)",
  "confidence": 0.0-1.0,
  "about_epstein": true/false
}"""

        # Make API request
        try:
            response = requests.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://soearly.space",
                    "X-Title": "Epstein Case Analysis"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{img_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1000
                },
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract response
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]

                # Try to parse JSON from response
                try:
                    # Extract JSON from markdown code blocks if present
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()

                    analysis = json.loads(content)

                    return {
                        "file": os.path.basename(image_path),
                        "full_path": image_path,
                        "folder": folder,
                        "category": analysis.get("category", "UNKNOWN"),
                        "description": analysis.get("description", ""),
                        "source": analysis.get("source", ""),
                        "relevance": analysis.get("relevance", ""),
                        "individuals": analysis.get("individuals", ""),
                        "confidence": analysis.get("confidence", 0.0),
                        "about_epstein": analysis.get("about_epstein", False),
                        "hash": img_hash,
                        "raw_response": content
                    }

                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        "file": os.path.basename(image_path),
                        "full_path": image_path,
                        "folder": folder,
                        "category": "UNKNOWN",
                        "description": content,
                        "raw_response": content
                    }

            else:
                raise Exception("No response from API")

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")

    def save_results(self, output_path: str):
        """Save analysis results to JSON"""
        data = {
            "results": self.results,
            "statistics": self.stats,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved analysis of {len(self.results)} images to {output_path}")

    def generate_html_report(self, output_path: str):
        """Generate HTML report of analysis results"""

        # Separate results by category
        categorized = {
            "UNIQUE_PHOTO": [],
            "EMAIL_SCREENSHOT": [],
            "LEGAL_DOC": [],
            "BOOK_PAGE": [],
            "ERROR": []
        }

        for result in self.results:
            category = result.get("category", "UNKNOWN")
            if category in categorized:
                categorized[category].append(result)

        # Sort unique photos by relevance
        categorized["UNIQUE_PHOTO"].sort(
            key=lambda x: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(x.get("relevance", "LOW"), 0),
            reverse=True
        )

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Analysis Results - Epstein Case</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        header {{
            background: linear-gradient(135deg, #c62828 0%, #e53935 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        .stats-bar {{
            display: flex;
            gap: 2rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}
        .stat {{
            display: flex;
            flex-direction: column;
        }}
        .stat-label {{
            font-size: 0.85rem;
            opacity: 0.8;
            text-transform: uppercase;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            margin-top: 0.25rem;
        }}
        .category-section {{
            background: white;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .category-section h2 {{
            color: #c62828;
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
        }}
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 2rem;
        }}
        .image-card {{
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .image-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}
        .image-card.high-relevance {{
            border-color: #c62828;
            border-width: 3px;
        }}
        .image-card.medium-relevance {{
            border-color: #ff9800;
            border-width: 3px;
        }}
        .image-card img {{
            width: 100%;
            height: 250px;
            object-fit: cover;
            cursor: pointer;
        }}
        .image-info {{
            padding: 1rem;
        }}
        .image-filename {{
            font-weight: 600;
            color: #666;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }}
        .image-description {{
            color: #444;
            margin-bottom: 0.5rem;
        }}
        .image-meta {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.75rem;
        }}
        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-high {{
            background: #c62828;
            color: white;
        }}
        .badge-medium {{
            background: #ff9800;
            color: white;
        }}
        .badge-low {{
            background: #757575;
            color: white;
        }}
        .lightbox {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        .lightbox.active {{
            display: flex;
        }}
        .lightbox img {{
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
        }}
        .lightbox-close {{
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>Image Analysis Results</h1>
            <p>Epstein Case Disclosures - {self.stats['total_images']} Images Analyzed</p>
            <div class="stats-bar">
                <div class="stat">
                    <span class="stat-label">Total Processed</span>
                    <span class="stat-value">{self.stats['processed']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Unique Photos</span>
                    <span class="stat-value">{self.stats['unique_photos']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Email Screenshots</span>
                    <span class="stat-value">{self.stats['email_screenshots']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Legal Docs</span>
                    <span class="stat-value">{self.stats['legal_docs']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Book Pages</span>
                    <span class="stat-value">{self.stats['book_pages']}</span>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
'''

        # UNIQUE PHOTOS section (highest priority)
        if categorized["UNIQUE_PHOTO"]:
            html += '''
        <div class="category-section">
            <h2>🔍 Unique Photos (High Priority Review)</h2>
            <div class="image-grid">
'''
            for item in categorized["UNIQUE_PHOTO"]:
                relevance = item.get("relevance", "LOW")
                relevance_class = f"{relevance.lower()}-relevance" if relevance in ["HIGH", "MEDIUM"] else ""

                html += f'''
                <div class="image-card {relevance_class}">
                    <img src="../{item['full_path'].replace(os.sep, '/')}" alt="{item['file']}" onclick="openLightbox(this.src)">
                    <div class="image-info">
                        <div class="image-filename">{item['file']}</div>
                        <div class="image-description">{item.get('description', 'No description')}</div>
                        {f'<div><strong>Individuals:</strong> {item["individuals"]}</div>' if item.get('individuals') else ''}
                        <div class="image-meta">
                            {f'<span class="badge badge-{relevance.lower()}">{relevance}</span>' if relevance else ''}
                            <span class="badge" style="background: #2196F3; color: white;">Folder {item['folder']}</span>
                        </div>
                    </div>
                </div>
'''
            html += '''
            </div>
        </div>
'''

        # Other categories (collapsed by default)
        for category, title in [
            ("EMAIL_SCREENSHOT", "📧 Email Screenshots"),
            ("LEGAL_DOC", "📄 Legal Documents"),
            ("BOOK_PAGE", "📚 Book/Magazine Pages")
        ]:
            if categorized[category]:
                html += f'''
        <div class="category-section">
            <h2>{title} ({len(categorized[category])} items)</h2>
            <p><em>Click to expand and view details</em></p>
        </div>
'''

        html += '''
    </div>

    <div id="lightbox" class="lightbox" onclick="closeLightbox()">
        <span class="lightbox-close">&times;</span>
        <img id="lightbox-img" src="" alt="">
    </div>

    <script>
        function openLightbox(src) {
            document.getElementById('lightbox').classList.add('active');
            document.getElementById('lightbox-img').src = src;
        }

        function closeLightbox() {
            document.getElementById('lightbox').classList.remove('active');
        }
    </script>
</body>
</html>
'''

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"HTML report generated: {output_path}")
