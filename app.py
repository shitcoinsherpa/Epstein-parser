import gradio as gr
import os
import json
from datetime import datetime
from email_parser import EmailParser
from email_threading import EmailThreader
from html_generator_v2 import MessagingHTMLGenerator
from gemini_analyzer import GeminiImageAnalyzer

# Global state
parser_state = {"emails": None, "threads": None, "stats": None}
analyzer_state = {"results": None, "stats": None}

def format_date(date_str):
    """Format date string to human-readable format"""
    if not date_str or date_str == "Unknown date":
        return date_str

    try:
        # Handle ISO format (2019-05-19T22:39:32)
        if 'T' in str(date_str):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y at %I:%M %p")

        # Handle other formats - just return as is
        return date_str
    except:
        return date_str

def parse_emails(progress=gr.Progress()):
    """Parse all email files"""
    try:
        progress(0, desc="Initializing email parser...")

        parser = EmailParser()

        text_folders = ["TEXT/001", "TEXT/002"]

        def progress_callback(current, total):
            progress(current / total, desc=f"Processing file {current}/{total}")

        progress(0.1, desc="Starting email extraction...")
        emails = parser.parse_all_files(text_folders, progress_callback)

        progress(0.8, desc="Creating email threads...")
        threader = EmailThreader(emails)
        threads = threader.create_threads()

        # Get deduplicated emails with duplicate_sources field
        deduplicated_emails = threader.deduplicate_emails(emails)

        # Update parser with deduplicated emails BEFORE calculating stats
        parser.emails = deduplicated_emails
        # Update emails_found to reflect deduplication
        parser.stats["emails_found"] = len(deduplicated_emails)

        progress(0.9, desc="Calculating statistics...")
        stats = parser.get_statistics()

        # Save to JSON with deduplicated emails
        progress(0.95, desc="Saving results...")
        parser.save_to_json("emails_parsed.json")

        # Store in state
        parser_state["emails"] = deduplicated_emails
        parser_state["threads"] = threads
        parser_state["stats"] = stats

        progress(1.0, desc="Complete!")

        summary = f"""✅ **Parsing Complete!**

📊 **Statistics:**
- Total files processed: {stats['total_files']}
- Emails found: {stats['emails_found']}
- Traditional format: {stats['traditional_format']}
- Message format: {stats['message_format']}
- Other documents: {stats['other_documents']}
- Parse errors: {stats['parse_errors']}

📧 **Email Breakdown:**
- Epstein sent: {stats['epstein_sent']}
- Epstein received: {stats['epstein_received']}
- Unique senders: {stats['unique_senders']}
- Unique recipients: {stats['unique_recipients']}

📅 **Date Range:**
- Earliest: {stats['date_range']['earliest'] if stats['date_range'] else 'N/A'}
- Latest: {stats['date_range']['latest'] if stats['date_range'] else 'N/A'}

🧵 **Threads:** {len(threads)} conversation threads created

💾 **Data saved to:** emails_parsed.json
"""

        return summary, stats['emails_found'], stats['epstein_sent'], stats['unique_senders']

    except Exception as e:
        return f"❌ Error: {str(e)}", 0, 0, 0


def export_html(progress=gr.Progress()):
    """Export emails to static HTML"""
    try:
        if not parser_state["emails"]:
            return "❌ Please parse emails first!"

        progress(0, desc="Generating HTML...")

        generator = MessagingHTMLGenerator(
            parser_state["emails"],
            parser_state["threads"],
            parser_state["stats"]
        )

        output_dir = "output"
        generator.generate(output_dir)

        progress(1.0, desc="Complete!")

        return f"""✅ **HTML Export Complete!**

📁 **Output directory:** {os.path.abspath(output_dir)}

📄 **Files generated:**
- index.html (main email viewer)
- assets/css/styles.css
- assets/js/data.js (embedded email data)
- assets/js/app.js (search/filter functionality)

🌐 **To deploy to soearly.space:**
1. Upload all files from the output/ directory
2. Access at: https://soearly.space/epstein/index.html

**Features included:**
- ✓ Search (keyword & exact match with quotes)
- ✓ Filter by sender
- ✓ Sort by date, sender
- ✓ Table and threaded conversation views
- ✓ Epstein-only filter (default)
- ✓ CSV export
- ✓ Sender statistics
- ✓ Full responsive design
"""

    except Exception as e:
        return f"❌ Error: {str(e)}"


def analyze_images(api_key, folder_selection, progress=gr.Progress()):
    """Analyze images using Gemini"""
    try:
        if not api_key:
            return "❌ Please enter your OpenRouter API key!", 0, 0, 0

        progress(0, desc="Initializing Gemini analyzer...")

        analyzer = GeminiImageAnalyzer(api_key)

        # Determine folders to process
        if folder_selection == "All Folders (001-012)":
            folders = [f"{i:03d}" for i in range(1, 13)]
        elif folder_selection == "Folder 012 Only":
            folders = ["012"]
        else:
            # Custom - just do 012 for now
            folders = ["012"]

        def progress_callback(current, total, folder):
            progress(current / total, desc=f"Analyzing images in folder {folder}: {current}/{total}")

        progress(0, desc="Starting image analysis...")
        results = analyzer.analyze_all_folders("IMAGES", folders, progress_callback)

        progress(0.9, desc="Saving results...")

        # Save JSON results
        analyzer.save_results("image_analysis_results.json")

        # Generate HTML report
        analyzer.generate_html_report("output/image-analysis.html")

        # Store in state
        analyzer_state["results"] = results
        analyzer_state["stats"] = analyzer.stats

        progress(1.0, desc="Complete!")

        summary = f"""✅ **Image Analysis Complete!**

📊 **Statistics:**
- Total images: {analyzer.stats['total_images']}
- Processed: {analyzer.stats['processed']}
- Errors: {analyzer.stats['errors']}

📷 **Categories:**
- 🔍 Unique Photos: {analyzer.stats['unique_photos']}
- 📧 Email Screenshots: {analyzer.stats['email_screenshots']}
- 📄 Legal Documents: {analyzer.stats['legal_docs']}
- 📚 Book Pages: {analyzer.stats['book_pages']}

💾 **Results saved to:**
- image_analysis_results.json
- output/image-analysis.html

🌐 **View report:** Open output/image-analysis.html in browser

**Using model:** google/gemini-2.0-flash-exp:free (FREE)
**Total cost:** $0.00
"""

        return summary, analyzer.stats['processed'], analyzer.stats['unique_photos'], analyzer.stats['book_pages']

    except Exception as e:
        return f"❌ Error: {str(e)}", 0, 0, 0


def get_top_senders():
    """Get top email senders and recipients for display"""
    if not parser_state["stats"]:
        return "Parse emails first to see statistics.", []

    sender_counts = parser_state["stats"].get("sender_counts", {})
    recipient_counts = parser_state["stats"].get("recipient_counts", {})

    top_senders = list(sender_counts.items())[:20]
    top_recipients = list(recipient_counts.items())[:20]

    output = "## 📤 Top 20 Email Senders:\n\n"
    for email, count in top_senders:
        # Escape @ to prevent mailto links
        display_email = email.replace('@', '\\@') if email else email
        output += f"- **`{display_email}`**: {count} emails sent\n"

    output += "\n---\n\n"
    output += "## 📥 Top 20 Email Recipients:\n\n"
    for email, count in top_recipients:
        # Escape @ to prevent mailto links
        display_email = email.replace('@', '\\@') if email else email
        output += f"- **`{display_email}`**: {count} emails received\n"

    # Return list of all senders and recipients for dropdown
    all_senders = list(sender_counts.keys())
    all_recipients = list(recipient_counts.keys())

    return output, all_senders


def view_emails_by_sender(sender_email, max_emails=50):
    """View emails from a specific sender - now shows threaded conversations"""
    if not parser_state["emails"]:
        return "No emails parsed yet."

    if not sender_email:
        return "Select a sender to view their emails."

    emails = [e for e in parser_state["emails"] if e.get("from") == sender_email]

    if not emails:
        return f"No emails found from {sender_email}"

    # Group into conversation threads
    threads = group_emails_by_thread(emails)

    # Sort threads by most recent email (reverse chronological for threads)
    sorted_threads = sorted(threads.items(),
                           key=lambda x: max(e.get("timestamp", 0) for e in x[1]),
                           reverse=True)

    # Limit number of threads shown
    sorted_threads = sorted_threads[:max_emails]

    total_emails = sum(len(thread_emails) for _, thread_emails in sorted_threads)
    total_threads = len(sorted_threads)

    output = f"# 📧 Emails from `{sender_email}`\n\n"
    output += f"**Total: {total_emails} emails in {total_threads} conversations** (showing first {max_emails} conversations)\n\n"
    output += "---\n\n"

    for thread_idx, (source_file, thread_emails) in enumerate(sorted_threads, 1):
        # Check if this is a multi-message conversation
        is_conversation = len(thread_emails) > 1

        if is_conversation:
            # Display as threaded conversation
            output += f"## 💬 Conversation {thread_idx} ({len(thread_emails)} messages)\n\n"

            # Check for duplicate sources
            duplicate_sources = thread_emails[0].get('_duplicate_sources', [source_file])
            if len(duplicate_sources) > 1:
                output += f"**Source:** `{duplicate_sources[0]}`\n\n"
                other_sources = [s for s in duplicate_sources if s != duplicate_sources[0]]
                output += f"<div style='padding: 6px 10px; border-left: 3px solid #8b949e; margin-bottom: 12px; opacity: 0.7; font-size: 0.9em;'>\n"
                output += f"ℹ️ <em>Additional copies of this conversation found in: {', '.join(f'`{s}`' for s in other_sources)}</em>\n"
                output += f"</div>\n\n"
            else:
                output += f"**Source:** `{source_file}`\n\n"

            for msg_idx, email in enumerate(thread_emails, 1):
                date = email.get("date", "Unknown date")
                from_addr = email.get("from", "Unknown sender")
                to_addr = email.get("to", "Unknown recipient")
                subject = email.get("subject", "")
                body = email.get("body", "")
                is_embedded = email.get("is_embedded", False)

                # Color-coded message header
                msg_icon = '📨' if is_embedded else '📧'
                output += f"### {msg_icon} Message {msg_idx} — {format_date(date)}\n\n"

                # From/To with colored borders (dark mode friendly)
                output += f"<div style='padding: 8px 12px; border-left: 4px solid #4a90e2; margin-bottom: 12px;'>\n"
                output += f"<strong style='color: #4a90e2;'>FROM:</strong> <code>{from_addr}</code><br/>\n"
                output += f"<strong style='color: #2ea043;'>TO:</strong> <code>{to_addr}</code>\n"
                output += f"</div>\n\n"

                # Subject (if present)
                if subject and subject.strip():
                    output += f"<div style='padding: 8px 12px; border-left: 4px solid #fb8500; margin-bottom: 12px;'>\n"
                    output += f"<strong style='color: #fb8500;'>SUBJECT:</strong> {subject}\n"
                    output += f"</div>\n\n"

                # Body content
                disclaimer = email.get('disclaimer')
                if body:
                    body_preview = body[:400] + "..." if len(body) > 400 else body
                    output += f"<div style='padding: 8px 12px; border-left: 4px solid #8b949e; margin-bottom: 16px;'>\n"
                    output += f"<strong style='color: #8b949e;'>BODY:</strong>\n\n"
                    output += f"{body_preview}\n"
                    output += f"</div>\n\n"
                elif not disclaimer:
                    # Only show "(No content)" if there's also no disclaimer
                    output += f"<div style='padding: 8px 12px; border-left: 4px solid #6e7681; margin-bottom: 16px; font-style: italic; opacity: 0.7;'>\n"
                    output += f"(No content)\n"
                    output += f"</div>\n\n"
                # else: If no body but has disclaimer, don't show anything - just the disclaimer below

                # Disclaimer (if present) - styled smaller and italicized
                if disclaimer:
                    disc_preview = disclaimer[:200] + "..." if len(disclaimer) > 200 else disclaimer
                    output += f"<div style='padding: 6px 10px; border-left: 2px solid #6e7681; margin-bottom: 12px; font-size: 0.85em; font-style: italic; opacity: 0.6;'>\n"
                    if not body:
                        output += f"<strong style='color: #8b949e;'>BODY:</strong> <em style='opacity: 0.8;'>[Message contained only legal disclaimer]</em>\n\n"
                    output += f"<em>{disc_preview}</em>\n"
                    output += f"</div>\n\n"

            output += "---\n\n"
        else:
            # Single email - display with same color-coding
            email = thread_emails[0]
            date = email.get("date", "Unknown date")
            to = email.get("to", "Unknown recipient")
            subject = email.get("subject", "")
            body = email.get("body", "")

            output += f"### 📧 Email {thread_idx} — {format_date(date)}\n\n"

            # Check for duplicate sources
            duplicate_sources = email.get('_duplicate_sources', [source_file])
            if len(duplicate_sources) > 1:
                output += f"**Source:** `{duplicate_sources[0]}`\n\n"
                other_sources = [s for s in duplicate_sources if s != duplicate_sources[0]]
                output += f"<div style='padding: 6px 10px; border-left: 3px solid #8b949e; margin-bottom: 12px; opacity: 0.7; font-size: 0.9em;'>\n"
                output += f"ℹ️ <em>Additional copies found in: {', '.join(f'`{s}`' for s in other_sources)}</em>\n"
                output += f"</div>\n\n"
            else:
                output += f"**Source:** `{source_file}`\n\n"

            # From/To
            output += f"<div style='background: #f0f7ff; padding: 10px; border-left: 4px solid #4a90e2; margin-bottom: 10px;'>\n"
            output += f"<strong style='color: #1a5490;'>FROM:</strong> <code>{sender_email}</code><br/>\n"
            output += f"<strong style='color: #2d8659;'>TO:</strong> <code>{to}</code>\n"
            output += f"</div>\n\n"

            # Subject
            if subject and subject.strip():
                output += f"<div style='background: #fff8e6; padding: 8px; border-left: 3px solid #ff9800; margin-bottom: 10px;'>\n"
                output += f"<strong style='color: #e65100;'>SUBJECT:</strong> {subject}\n"
                output += f"</div>\n\n"

            # Body
            if body:
                output += f"<div style='background: #f8f8f8; padding: 10px; border-left: 3px solid #999; margin-bottom: 15px;'>\n"
                output += f"<strong style='color: #555;'>BODY:</strong><br/>\n"
                output += f"<pre style='white-space: pre-wrap; font-family: inherit; margin: 5px 0 0 0;'>{body}</pre>\n"
                output += f"</div>\n\n"
            else:
                output += f"<div style='background: #f8f8f8; padding: 10px; border-left: 3px solid #ccc; margin-bottom: 15px; font-style: italic; color: #999;'>\n"
                output += f"(No content)\n"
                output += f"</div>\n\n"

            output += "---\n\n"

    return output


def group_emails_by_thread(emails):
    """Group emails by source file (conversation thread) and sort chronologically
    Also detects duplicate conversations and groups them together"""
    from collections import defaultdict

    threads = defaultdict(list)
    for email in emails:
        source_file = email.get("source_file", "Unknown")
        threads[source_file].append(email)

    # Sort emails within each thread by timestamp (chronological order)
    for source_file in threads:
        threads[source_file].sort(key=lambda x: x.get("timestamp", 0))

    # Deduplicate: find threads with identical content
    deduplicated = {}
    signature_map = {}  # Maps signature to list of source files

    for source_file, thread_emails in threads.items():
        # Create signature from first message (from+to+timestamp+body_snippet)
        if thread_emails:
            first = thread_emails[0]
            sig = f"{first.get('from')}|{first.get('to')}|{first.get('timestamp')}|{first.get('body', '')[:50]}"

            if sig in signature_map:
                # This is a duplicate - add source file to existing list
                signature_map[sig].append(source_file)
            else:
                # First occurrence - store it
                signature_map[sig] = [source_file]
                deduplicated[source_file] = thread_emails

    # Add duplicate source file info to each thread
    for source_file, thread_emails in deduplicated.items():
        first = thread_emails[0]
        sig = f"{first.get('from')}|{first.get('to')}|{first.get('timestamp')}|{first.get('body', '')[:50]}"

        # Store list of all source files containing this conversation
        for email in thread_emails:
            email['_duplicate_sources'] = signature_map[sig]

    return deduplicated


def view_emails_to_recipient(recipient_email, max_emails=50):
    """View emails to a specific recipient - now shows threaded conversations"""
    if not parser_state["emails"]:
        return "No emails parsed yet."

    if not recipient_email:
        return "Select a recipient to view their emails."

    # Check both primary 'to' field and 'to_list'
    emails = [e for e in parser_state["emails"]
              if e.get("to") == recipient_email or
              (e.get("to_list") and recipient_email in e.get("to_list", []))]

    if not emails:
        return f"No emails found to {recipient_email}"

    # Group into conversation threads
    threads = group_emails_by_thread(emails)

    # Sort threads by most recent email (reverse chronological for threads)
    sorted_threads = sorted(threads.items(),
                           key=lambda x: max(e.get("timestamp", 0) for e in x[1]),
                           reverse=True)

    # Limit number of threads shown
    sorted_threads = sorted_threads[:max_emails]

    total_emails = sum(len(thread_emails) for _, thread_emails in sorted_threads)
    total_threads = len(sorted_threads)

    output = f"# 📧 Emails to `{recipient_email}`\n\n"
    output += f"**Total: {total_emails} emails in {total_threads} conversations** (showing first {max_emails} conversations)\n\n"
    output += "---\n\n"

    for thread_idx, (source_file, thread_emails) in enumerate(sorted_threads, 1):
        # Check if this is a multi-message conversation
        is_conversation = len(thread_emails) > 1

        if is_conversation:
            # Display as threaded conversation
            output += f"## 💬 Conversation {thread_idx} ({len(thread_emails)} messages)\n\n"

            # Check for duplicate sources
            duplicate_sources = thread_emails[0].get('_duplicate_sources', [source_file])
            if len(duplicate_sources) > 1:
                output += f"**Source:** `{duplicate_sources[0]}`\n\n"
                other_sources = [s for s in duplicate_sources if s != duplicate_sources[0]]
                output += f"<div style='padding: 6px 10px; border-left: 3px solid #8b949e; margin-bottom: 12px; opacity: 0.7; font-size: 0.9em;'>\n"
                output += f"ℹ️ <em>Additional copies of this conversation found in: {', '.join(f'`{s}`' for s in other_sources)}</em>\n"
                output += f"</div>\n\n"
            else:
                output += f"**Source:** `{source_file}`\n\n"

            for msg_idx, email in enumerate(thread_emails, 1):
                date = email.get("date", "Unknown date")
                from_addr = email.get("from", "Unknown sender")
                to_addr = email.get("to", recipient_email)
                subject = email.get("subject", "")
                body = email.get("body", "")
                is_embedded = email.get("is_embedded", False)

                # Color-coded message header
                msg_icon = '📨' if is_embedded else '📧'
                output += f"### {msg_icon} Message {msg_idx} — {format_date(date)}\n\n"

                # From/To with colored borders (dark mode friendly)
                output += f"<div style='padding: 8px 12px; border-left: 4px solid #4a90e2; margin-bottom: 12px;'>\n"
                output += f"<strong style='color: #4a90e2;'>FROM:</strong> <code>{from_addr}</code><br/>\n"
                output += f"<strong style='color: #2ea043;'>TO:</strong> <code>{to_addr}</code>\n"
                output += f"</div>\n\n"

                # Subject (if present)
                if subject and subject.strip():
                    output += f"<div style='padding: 8px 12px; border-left: 4px solid #fb8500; margin-bottom: 12px;'>\n"
                    output += f"<strong style='color: #fb8500;'>SUBJECT:</strong> {subject}\n"
                    output += f"</div>\n\n"

                # Body content
                disclaimer = email.get('disclaimer')
                if body:
                    body_preview = body[:400] + "..." if len(body) > 400 else body
                    output += f"<div style='padding: 8px 12px; border-left: 4px solid #8b949e; margin-bottom: 16px;'>\n"
                    output += f"<strong style='color: #8b949e;'>BODY:</strong>\n\n"
                    output += f"{body_preview}\n"
                    output += f"</div>\n\n"
                elif not disclaimer:
                    # Only show "(No content)" if there's also no disclaimer
                    output += f"<div style='padding: 8px 12px; border-left: 4px solid #6e7681; margin-bottom: 16px; font-style: italic; opacity: 0.7;'>\n"
                    output += f"(No content)\n"
                    output += f"</div>\n\n"
                # else: If no body but has disclaimer, don't show anything - just the disclaimer below

                # Disclaimer (if present) - styled smaller and italicized
                if disclaimer:
                    disc_preview = disclaimer[:200] + "..." if len(disclaimer) > 200 else disclaimer
                    output += f"<div style='padding: 6px 10px; border-left: 2px solid #6e7681; margin-bottom: 12px; font-size: 0.85em; font-style: italic; opacity: 0.6;'>\n"
                    if not body:
                        output += f"<strong style='color: #8b949e;'>BODY:</strong> <em style='opacity: 0.8;'>[Message contained only legal disclaimer]</em>\n\n"
                    output += f"<em>{disc_preview}</em>\n"
                    output += f"</div>\n\n"

            output += "---\n\n"
        else:
            # Single email - display with same color-coding
            email = thread_emails[0]
            date = email.get("date", "Unknown date")
            from_addr = email.get("from", "Unknown sender")
            subject = email.get("subject", "")
            body = email.get("body", "")
            to_list = email.get("to_list", [recipient_email])
            to_display = ', '.join(to_list) if len(to_list) > 1 else recipient_email

            output += f"### 📧 Email {thread_idx} — {format_date(date)}\n\n"
            output += f"**Source:** `{source_file}`\n\n"

            # From/To (dark mode friendly)
            output += f"<div style='padding: 8px 12px; border-left: 4px solid #4a90e2; margin-bottom: 12px;'>\n"
            output += f"<strong style='color: #4a90e2;'>FROM:</strong> <code>{from_addr}</code><br/>\n"
            output += f"<strong style='color: #2ea043;'>TO:</strong> <code>{to_display}</code>\n"
            output += f"</div>\n\n"

            # Subject
            if subject and subject.strip():
                output += f"<div style='padding: 8px 12px; border-left: 4px solid #fb8500; margin-bottom: 12px;'>\n"
                output += f"<strong style='color: #fb8500;'>SUBJECT:</strong> {subject}\n"
                output += f"</div>\n\n"

            # Body
            if body:
                output += f"<div style='padding: 8px 12px; border-left: 4px solid #8b949e; margin-bottom: 16px;'>\n"
                output += f"<strong style='color: #8b949e;'>BODY:</strong>\n\n"
                output += f"{body}\n"
                output += f"</div>\n\n"
            else:
                output += f"<div style='padding: 8px 12px; border-left: 4px solid #6e7681; margin-bottom: 16px; font-style: italic; opacity: 0.7;'>\n"
                output += f"(No content)\n"
                output += f"</div>\n\n"

            output += "---\n\n"

    return output


# Create Gradio interface
with gr.Blocks(title="Epstein Case Email & Image Analyzer", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 📧 Epstein Case Email & Image Analyzer
    ## House Oversight Committee Disclosures Analysis Tool

    This tool parses email disclosures and analyzes images from the Epstein case files.
    """)

    with gr.Tabs():
        # Tab 1: Email Parser & Reader
        with gr.Tab("📧 Email Parser & Reader"):
            gr.Markdown("""
            ### Parse Email Documents
            Extract and organize all emails, then click any sender/recipient to view their emails.
            """)

            with gr.Row():
                parse_btn = gr.Button("🚀 Parse All Documents (2,895 files)", variant="primary", scale=2)
                export_btn = gr.Button("📤 Export to HTML", variant="secondary", scale=1)

            parse_output = gr.Markdown(label="Status")

            with gr.Row():
                total_emails_num = gr.Number(label="Total Emails Found", value=0)
                epstein_emails_num = gr.Number(label="Epstein Emails", value=0)
                unique_senders_num = gr.Number(label="Unique Senders", value=0)

            gr.Markdown("---")
            gr.Markdown("### 📖 Email Reader")
            gr.Markdown("After parsing, click any sender or recipient below to view their emails.")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 📤 Top Senders")
                    sender_radio = gr.Radio(
                        choices=[],
                        label="Click to view emails FROM:",
                        interactive=True
                    )

                with gr.Column(scale=1):
                    gr.Markdown("#### 📥 Top Recipients")
                    recipient_radio = gr.Radio(
                        choices=[],
                        label="Click to view emails TO:",
                        interactive=True
                    )

                with gr.Column(scale=2):
                    email_display = gr.Markdown(
                        value="**Parse emails above, then click any sender/recipient to view their emails.**"
                    )

            def parse_and_load():
                # Parse emails
                result = parse_emails()
                parse_result, total, epstein, senders = result

                # Auto-load lists
                if parser_state["stats"]:
                    sender_counts = parser_state["stats"].get("sender_counts", {})
                    recipient_counts = parser_state["stats"].get("recipient_counts", {})

                    sender_items = list(sender_counts.items())[:50]
                    recipient_items = list(recipient_counts.items())[:50]

                    sender_choices = [f"{email} ({count})" for email, count in sender_items]
                    recipient_choices = [f"{email} ({count})" for email, count in recipient_items]

                    return (
                        parse_result, total, epstein, senders,
                        gr.Radio(choices=sender_choices),
                        gr.Radio(choices=recipient_choices),
                        "**Click any sender or recipient above to view their emails.**"
                    )

                return parse_result, total, epstein, senders, gr.Radio(choices=[]), gr.Radio(choices=[]), ""

            parse_btn.click(
                fn=parse_and_load,
                outputs=[parse_output, total_emails_num, epstein_emails_num, unique_senders_num,
                        sender_radio, recipient_radio, email_display]
            )

            export_btn.click(
                fn=export_html,
                outputs=[parse_output]
            )

            def view_sender_from_radio(selection):
                if not selection:
                    return "Click a sender to view their emails."
                email = selection.rsplit(" (", 1)[0]
                return view_emails_by_sender(email)

            def view_recipient_from_radio(selection):
                if not selection:
                    return "Click a recipient to view their emails."
                email = selection.rsplit(" (", 1)[0]
                return view_emails_to_recipient(email)

            sender_radio.change(
                fn=view_sender_from_radio,
                inputs=[sender_radio],
                outputs=[email_display]
            )

            recipient_radio.change(
                fn=view_recipient_from_radio,
                inputs=[recipient_radio],
                outputs=[email_display]
            )

        # Tab 2: Image Analyzer
        with gr.Tab("🖼️ Image Analyzer"):
            gr.Markdown("""
            ### Analyze Images with Gemini
            Uses Gemini 2.0 Flash (free) to analyze all images and identify potentially unique photos
            vs. known public sources (books, magazines).

            **Total images across 12 folders:** 22,903 images
            """)

            api_key_input = gr.Textbox(
                label="OpenRouter API Key",
                type="password",
                placeholder="sk-or-v1-...",
                info="Get your free API key from https://openrouter.ai/"
            )

            folder_select = gr.Radio(
                choices=["All Folders (001-012)", "Folder 012 Only"],
                value="Folder 012 Only",
                label="Select Folders to Process",
                info="Start with folder 012 to test, then run all folders"
            )

            analyze_btn = gr.Button("🔍 Start Image Analysis", variant="primary")

            analyze_output = gr.Markdown(label="Status")

            with gr.Row():
                total_processed_num = gr.Number(label="Images Processed", value=0)
                unique_photos_num = gr.Number(label="Unique Photos Found", value=0)
                book_pages_num = gr.Number(label="Book Pages", value=0)

            gr.Markdown("""
            ⚠️ **Note:** Image analysis will take time. For all 22,903 images at ~0.3s per image,
            expect ~2 hours total. Results are saved incrementally.
            """)

            analyze_btn.click(
                fn=analyze_images,
                inputs=[api_key_input, folder_select],
                outputs=[analyze_output, total_processed_num, unique_photos_num, book_pages_num]
            )

        # Tab 3: Instructions
        with gr.Tab("ℹ️ Instructions"):
            gr.Markdown("""
            ## How to Use This Tool

            ### Step 1: Parse Emails
            1. Go to the **Email Parser** tab
            2. Click **"Parse All Documents"**
            3. Wait for processing (2,895 files, takes 2-5 minutes)
            4. Review statistics
            5. Click **"Export to HTML"** to generate static website

            ### Step 2: Analyze Images (Optional - Expensive Operation)
            1. Get a free API key from [OpenRouter](https://openrouter.ai/)
            2. Go to the **Image Analyzer** tab
            3. Enter your API key
            4. Select folder(s) to process
            5. Click **"Start Image Analysis"**
            6. Wait for completion (folder 012: ~5 minutes, all folders: ~2 hours)

            ### Step 3: Deploy to soearly.space
            1. Upload contents of `output/` folder via admin panel
            2. Set paths:
               - `index.html` → `/epstein/index.html`
               - `assets/*` → `/epstein/assets/*`
               - `image-analysis.html` → `/epstein/images.html`
            3. Access at `https://soearly.space/epstein/`

            ### Features in HTML Viewer
            - ✅ Search by keyword (case-insensitive)
            - ✅ Exact phrase search with quotes: `"roger stone"`
            - ✅ Filter by sender
            - ✅ Sort by date, sender
            - ✅ Table view or threaded conversation view
            - ✅ Epstein-only filter (default)
            - ✅ Top senders statistics
            - ✅ Export filtered results to CSV
            - ✅ Fully responsive (mobile-friendly)

            ### File Structure
            ```
            TEXT/001/          - 2,049 text files
            TEXT/002/          - 846 text files
            IMAGES/001-012/    - 22,903 images total
            ```

            ### Known Epstein Email Addresses
            - jeeitunes@gmail.com
            - jeevacation@gmail.com

            ### Notes
            - Email parser handles two formats: traditional (From:/To:) and Message: (GUID)
            - Some files contain multiple emails (Message: format)
            - Default view shows only emails involving Epstein addresses
            - Image analysis identifies unique photos vs. book pages/known sources
            - All processing is done locally, data stays on your machine
            - HTML output is 100% static (no backend required)
            """)

    gr.Markdown("""
    ---
    **Data Source:** House Oversight Committee - Epstein Case Disclosures

    **Contact/Issues:** Report issues or questions via your preferred channel
    """)

# Launch app
if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
