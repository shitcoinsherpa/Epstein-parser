import re
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

class EmailParser:
    """Parser for Epstein case disclosure emails - handles multiple formats"""

    EPSTEIN_EMAILS = [
        "jeeitunes@gmail.com",
        "jeevacation@gmail.com",
        "jeeproject@yahoo.com",         # Additional Epstein email
        "deevacation@gmail.com",        # OCR typo: j→d
        "j.epstein@lsnyc.net",          # Official email
        "jepstein@lsnyc.net",           # Without dot variant
        "e:jeeitunes@gmail.com",
        "e:jeevacation@gmail.com",
        "e:jeeproject@yahoo.com"
    ]

    EPSTEIN_NAME_PATTERNS = [
        "jeffrey epstein",
        "jeffrey e.",
        "jeffrey e",
        "jeff epstein",
        "epstein, jeffrey",
        "jeevacation",
        "jeeitunes",
        "jeeproject",
        "jee"                           # Short form used in some emails
    ]

    # Key associates/employees for tracking associate correspondence
    ASSOCIATE_NAMES = [
        "ghislaine maxwell",
        "lesley groff",
        "leslie groff",
        "darren indyke",
        "richard kahn",
        "rich kahn",
        "jean luc brunel",
        "jean-luc brunel",
        "sarah kellen",
        "sarah kensington",
        "nadia marcinkova",
        "nadia",
        "adriana ross",
        "adriana mucinska",
        "halidah sedgwick",
        "alan dershowitz",
        "alan m. dershowitz",
    ]

    # OCR typo corrections for known email addresses
    EMAIL_CORRECTIONS = {
        # jeevacation typos
        "jeeyacation@gmail.com": "jeevacation@gmail.com",  # y instead of v
        "jeevacation@qmail.com": "jeevacation@gmail.com",  # q instead of g
        "jeevacation@dmail.com": "jeevacation@gmail.com",  # d instead of g
        "jeevacation@omail.com": "jeevacation@gmail.com",  # o instead of g
        "jeevacation@gmail.corn": "jeevacation@gmail.com",  # corn instead of com
        "jeevacation@gmai1.com": "jeevacation@gmail.com",  # 1 instead of l
        "jeevacation@grnail.com": "jeevacation@gmail.com",  # rn instead of m
        "jeevacation@gmail.com": "jeevacation@gmail.com",  # canonical
        "jeevacationagmail.com": "jeevacation@gmail.com",  # missing @
        "ieevacation@gmail.com": "jeevacation@gmail.com",  # i instead of j
        "leevacation@gmail.com": "jeevacation@gmail.com",  # l instead of j
        "jeevacation@email.com": "jeevacation@gmail.com",  # wrong domain
        "eevacation@gmail.com": "jeevacation@gmail.com",  # missing j
        "jeevacation@cimail.com": "jeevacation@gmail.com",  # ci instead of g
        "jeevacation@gmail. corn": "jeevacation@gmail.com",  # space before corn
        "jeevacation@gmail. com": "jeevacation@gmail.com",  # space before com
        "jeevacation@gma il.com": "jeevacation@gmail.com",  # space in gmail
        "jeevacation@grnail.corn": "jeevacation@gmail.com",  # rn and corn
        "jeevacation©gmail.com": "jeevacation@gmail.com",  # © instead of @
        "jeevacation(4mail.com": "jeevacation@gmail.com",  # (4 instead of @g
        "jeeyacationornail.com": "jeevacation@gmail.com",  # multiple OCR errors
        # jeeitunes typos
        "jeetunes@gmail.com": "jeeitunes@gmail.com",  # missing i
        "jeeltunes@gmail.com": "jeeitunes@gmail.com",  # l instead of i
        "jeeitunes@qmail.com": "jeeitunes@gmail.com",  # q instead of g
        "jeeitunes@gmail.com": "jeeitunes@gmail.com",  # canonical
        # e: prefix variations
        "e:jeeyacation@gmail.com": "jeevacation@gmail.com",
        "e:jeevacation@qmail.com": "jeevacation@gmail.com",
    }

    # Name corrections for OCR errors (case-insensitive)
    NAME_CORRECTIONS = {
        # Al Seckel variations
        "l seckel": "Al Seckel",
        "al seckel": "Al Seckel",
        "al seckel 4111111111111.1111111111111111": "Al Seckel",

        # Alan Dershowitz variations
        "alan m. dershowil": "Alan Dershowitz",
        "alan dershowitz": "Alan Dershowitz",

        # Anas Alrasheed variations
        "anasalrasheed": "Anas Alrasheed",
        "anasalrasheec": "Anas Alrasheed",
        "anas alrasheed": "Anas Alrasheed",

        # Darren Indyke variations (I vs l confusion)
        "darren lndyke": "Darren Indyke",
        "darren indyke": "Darren Indyke",

        # Lesley Groff variations
        "lesley groffl": "Lesley Groff",
        "lesley groff i": "Lesley Groff",
        "tesley groff": "Lesley Groff",
        "lesley groff": "Lesley Groff",

        # Lisa New variations
        "lisa ne": "Lisa New",
        "lisa new": "Lisa New",

        # Tom Barrack variations
        "tom barrack private": "Tom Barrack",
        "tom barrack privat": "Tom Barrack",
        "tom barrack": "Tom Barrack",

        # Barry J. Cohen variations
        "barry j. cohen .111": "Barry J. Cohen",
        "barry j. cohen": "Barry J. Cohen",

        # Kathy Ruemmler variations
        "kathy ruemmler f": "Kathy Ruemmler",
        "kathy ruemmler i": "Kathy Ruemmler",
        "kathy ruemmlerl": "Kathy Ruemmler",
        "kathy ruemmler": "Kathy Ruemmler",

        # LHS variations
        "lhs i i": "Lhs",
        "lhs": "Lhs",

        # Larry Summer variations
        "larry summer": "Larry Summers",
        "larry summers": "Larry Summers",

        # Landon Thomas Jr variations
        "landon'": "Landon Thomas Jr.",
        "landon": "Landon Thomas Jr.",
        "landon thomas": "Landon Thomas Jr.",
        "landon thomas jr": "Landon Thomas Jr.",
        "landon thomas jr.": "Landon Thomas Jr.",
        "thomas jr., landon": "Landon Thomas Jr.",
        "thomas jr": "Landon Thomas Jr.",

        # Steve/Stephen Bannon variations
        "steve bannon i": "Steve Bannon",
        "steve bannon'il": "Steve Bannon",
        "steve bannon`": "Steve Bannon",
        "steve bannon": "Steve Bannon",
        "stephen bannon": "Steve Bannon",

        # Joi Ito variations
        "joichi ito": "Joi Ito",
        "joi ito": "Joi Ito",

        # Peggy Siegal variations
        "peggy siega": "Peggy Siegal",
        "peggy siegal": "Peggy Siegal",
        "peggy siegal f": "Peggy Siegal",

        # Nicholas Ribis variations
        "nicholas ribi": "Nicholas Ribis",
        "nicholas ribis": "Nicholas Ribis",
        "nicholas.ribis": "Nicholas Ribis",

        # Boris Nikolic variations
        "boris nikolic": "Boris Nikolic",

        # Ehud Barak variations
        "ehbarak": "Ehud Barak",
        "ehud barak": "Ehud Barak",

        # Thorbjorn Jagland variations
        "thorbjon jagian": "Thorbjorn Jagland",
        "thorbjon jagland": "Thorbjorn Jagland",
        "thorbjorn jagland": "Thorbjorn Jagland",

        # Faith Kates variations
        "faith kate": "Faith Kates",
        "faith kates": "Faith Kates",

        # Jack Lang variations
        "lang": "Jack Lang",
        "jack lang": "Jack Lang",

        # Jean Luc Brune variations
        "jean luc brune": "Jean Luc Brune",

        # Joscha Bach variations
        "joscha bachl": "Joscha Bach",
        "joscha bach": "Joscha Bach",

        # Joshua Cooper Ramo variations
        "joshua cooper ramo": "Joshua Cooper Ramo",

        # Ken Starr variations
        "starr": "Ken Starr",
        "ken starr": "Ken Starr",

        # Lajcak Miroslav variations
        "lajcak miroslav/minister/mzv": "Lajcak Miroslav",
        "lajcak miroslay/minister/mzv": "Lajcak Miroslav",

        # Lawrence Krauss variations
        "lawrence krauss": "Lawrence Krauss",

        # Leon Black variations
        "leon blac": "Leon Black",
        "leon black": "Leon Black",

        # Linda Stone variations
        "linda stone": "Linda Stone",

        # Melanie Spinella variations
        "melanie spineila": "Melanie Spinella",
        "melanie spinella": "Melanie Spinella",

        # Michael Wolff variations
        "michael woli": "Michael Wolff",
        "michael wolff": "Michael Wolff",

        # Mortimer Zuckerman variations
        "mortimer zuckerman": "Mortimer Zuckerman",

        # Moshe Hoffman variations
        "moshe hoffman": "Moshe Hoffman",

        # Nadia variations
        "nadja2102@yahoo.com": "Nadia",
        "nadia": "Nadia",

        # Neal Kassell variations
        "neal kassell": "Neal Kassell",

        # Nil Priell Barak variations
        "nil priell barak": "Nil Priell Barak",

        # Noam Chomsky variations
        "noam chomsky": "Noam Chomsky",

        # Paul Barrett variations
        "paul barrett .": "Paul Barrett",
        "paul barrett": "Paul Barrett",

        # Paul Krassner variations
        "paul krassner": "Paul Krassner",

        # Paul Prosperi variations
        "paul prosperi": "Paul Prosperi",

        # Peter Mandelson variations
        "peter mandelsor": "Peter Mandelson",
        "peter mandelson bt": "Peter Mandelson",
        "peter mandelson.": "Peter Mandelson",
        "peter mandelson": "Peter Mandelson",

        # Peter Thiel variations
        "peter thiel": "Peter Thiel",

        # Pritzker variations
        "pritzker": "Tom Pritzker",
        "tom pritzker": "Tom Pritzker",

        # Reid Hoffman variations
        "reid hoffman": "Reid Hoffman",

        # Richard Kahn variations
        "rich kahn": "Richard Kahn",
        "richard kahn": "Richard Kahn",

        # Richard Merkin variations
        "richard merkin": "Richard Merkin",

        # Robert Gold variations
        "robert gold": "Robert Gold",

        # Robert Kuhn variations
        "robert kuhn": "Robert Kuhn",
        "robert lawrence kuhn": "Robert Kuhn",

        # Robert Trivers variations
        "robert trivers": "Robert Trivers",

        # Soon Yi Previn variations
        "soon yi previ": "Soon Yi Previn",
        "soon yi previn": "Soon Yi Previn",

        # Stanley Rosenberg variations
        "stanley rosenberg": "Stanley Rosenberg",

        # Stephen Hanson variations
        "stephen hanson": "Stephen Hanson",
        "steve hanson": "Stephen Hanson",

        # Steven Pfeiffer variations
        "steven pfeiffer a=11": "Steven Pfeiffer",
        "steven pfeiffer": "Steven Pfeiffer",

        # Sultan Bin Sulayem variations
        "sultan bin sulayerr": "Sultan Bin Sulayem",
        "sultan bin sulayem": "Sultan Bin Sulayem",

        # Valeria Chomsky variations
        "valeria chomsky": "Valeria Chomsky",

        # Brad Karp variations
        "brad s karp": "Brad Karp",
        "brad karp": "Brad Karp",
        "karp": "Brad Karp",

        # David Blaine variations
        "david blaine": "David Blaine",

        # David Grosof variations
        "david grosof": "David Grosof",

        # David Schoen variations
        "david schoen": "David Schoen",

        # David Stern variations
        "david stern": "David Stern",

        # Deepak Chopra variations
        "deepak chopra": "Deepak Chopra",

        # Ed Boyden variations
        "ed boyden": "Ed Boyden",

        # Eric Roth variations
        "eric roth": "Eric Roth",

        # Erika Kellerhals variations
        "erika kellerhals": "Erika Kellerhals",

        # G Maxwell / Gmax variations
        "g maxwell": "Ghislaine Maxwell",
        "gmax": "Ghislaine Maxwell",
        "ghislaine maxwell": "Ghislaine Maxwell",

        # Gerald Barton variations
        "gerald barton": "Gerald Barton",

        # Gianni Serazzi variations
        "gianni serazzi": "Gianni Serazzi",

        # Gwendolyn Beck variations
        "gwendolyn beck": "Gwendolyn Beck",

        # Harry Fisch variations
        "harry fisch": "Harry Fisch",

        # Jack Goldberger variations
        "jack goldberger": "Jack Goldberger",

        # Jonathan Farkas variations
        "jonathan farkas": "Jonathan Farkas",

        # Katherine Keating variations
        "katherine keating": "Katherine Keating",

        # Kathy variations (generic)
        "kathy": "Kathy Ruemmler",

        # Kensington variations
        "kensington2": "Kensington",

        # Martin Weinberg variations
        "martin weinberg": "Martin Weinberg",

        # Masha Drokova variations
        "masha drokova": "Masha Drokova",

        # Melanie Walker variations
        "melanie walker": "Melanie Walker",

        # Miller variations
        "miller": "Miller",

        # Mohamed Waheed Hassan variations
        "mohamed waheed hassan": "Mohamed Waheed Hassan",

        # Paula variations
        "paula": "Paula",

        # Ramsey Elkholy variations
        "ramsey elkholy": "Ramsey Elkholy",

        # R. Couri Hay variations
        "r. couri hay": "R. Couri Hay",

        # Tim Zagat variations
        "tim zagat": "Tim Zagat",

        # Weingarten variations
        "weingarten": "Weingarten",

        # Zubair Khan variations
        "zubair khan": "Zubair Khan",

        # Alan Dershowitz variations
        "alan dershowitz": "Alan Dershowitz",
        "alan m. dershowitz": "Alan Dershowitz",
        "alan m dershowitz": "Alan Dershowitz",

        # Alireza Ittihadieh variations
        "alireza ittihadieh": "Alireza Ittihadieh",

        # Anil Ambani variations
        "anil.ambani": "Anil Ambani",
        "anil ambani": "Anil Ambani",

        # Anthony variations
        "anthony": "Anthony",

        # Barbro C Ehnbom variations
        "barbro c ehnbom": "Barbro C Ehnbom",

        # Bill Siegel variations
        "bill siegel": "Bill Siegel",

        # Ed variations
        "ed": "Ed Boyden",
    }

    # Canonical sender mapping - map name variations to email addresses
    CANONICAL_SENDERS = {
        # Jeffrey Epstein variations (name-only forms without email addresses)
        "jeffrey e.": "jeevacation@gmail.com",
        "jeffrey e": "jeevacation@gmail.com",
        "jeffrey": "jeevacation@gmail.com",
        "jeffrey epstein": "jeevacation@gmail.com",
        "j": "jeevacation@gmail.com",
        "jep": "jeevacation@gmail.com",
        "j jep": "jeevacation@gmail.com",
        "jeevacation": "jeevacation@gmail.com",
        # Add more as we discover patterns
    }

    def __init__(self):
        self.emails = []
        self.stats = {
            "total_files": 0,
            "emails_found": 0,
            "traditional_format": 0,
            "message_format": 0,
            "other_documents": 0,
            "parse_errors": 0
        }
        self.sender_aliases = {}  # Track discovered aliases during parsing

    def parse_all_files(self, text_folders: List[str], progress_callback=None) -> List[Dict]:
        """Parse all text files in the given folders"""
        all_files = []
        for folder in text_folders:
            if os.path.exists(folder):
                all_files.extend(list(Path(folder).glob("*.txt")))

        self.stats["total_files"] = len(all_files)

        for idx, file_path in enumerate(all_files):
            try:
                emails_from_file = self.parse_file(str(file_path))
                if emails_from_file:
                    self.emails.extend(emails_from_file)
                    self.stats["emails_found"] += len(emails_from_file)
                else:
                    self.stats["other_documents"] += 1

                if progress_callback:
                    progress_callback(idx + 1, len(all_files))

            except Exception as e:
                self.stats["parse_errors"] += 1
                print(f"Error parsing {file_path}: {e}")

        # Post-process: deduplicate senders
        print("Deduplicating senders...")
        self.deduplicate_senders()

        return self.emails

    def parse_file(self, file_path: str) -> List[Dict]:
        """Parse a single file and return list of email dicts (may contain multiple emails)"""
        try:
            with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                content = f.read()

            # Check for traditional format - must have From: and Sent: OR Date: at start of lines
            has_traditional = (re.search(r'^From:\s*', content, re.MULTILINE) and
                             (re.search(r'^Sent:\s*', content, re.MULTILINE) or
                              re.search(r'^Date:\s*', content, re.MULTILINE)))

            # Check for Message format - must have GUID: and Message: at start of lines
            has_message = (re.search(r'^GUID:\s*', content, re.MULTILINE) and
                          re.search(r'^Message:\s*', content, re.MULTILINE) and
                          re.search(r'^Sender:\s*', content, re.MULTILINE))

            # Try traditional format first
            if has_traditional:
                # Check if it's a group chat
                if re.search(r'From:.*multiple senders', content, re.IGNORECASE):
                    return self.parse_group_chat(content, file_path)

                result = self.parse_traditional_format(content, file_path)
                # Handle both single email dict and list of emails (with embedded)
                if isinstance(result, list):
                    return result
                elif result:
                    return [result]
                else:
                    return []

            # Try Message: format (may return multiple emails)
            elif has_message:
                result = self.parse_message_format(content, file_path)
                if isinstance(result, list):
                    return result
                elif result:
                    return [result]

            return []

        except Exception as e:
            raise Exception(f"Failed to read file: {e}")

    def extract_embedded_emails(self, body: str, source_file: str) -> List[Dict]:
        """Extract embedded/quoted emails from message body (forwards/replies)"""
        embedded_emails = []

        # Pattern 1: Formal email headers - From: ... \n Sent: or Date: ... \n To: ...
        # Subject must be on the same line, not continuing to next line
        # Use [ \t]* instead of \s* after Subject: to avoid matching newlines
        formal_pattern = r'(?:^|\n)From:\s*(.+?)\s*\n(?:Sent|Date):\s*(.+?)\s*\nTo:\s*(.+?)(?:\s*\nSubject:[ \t]*([^\n]*?))?(?=\n|$)'
        formal_matches = list(re.finditer(formal_pattern, body, re.MULTILINE))

        for match in formal_matches:
            from_addr = match.group(1).strip()
            date_str = match.group(2).strip()
            to_addr = match.group(3).strip()
            subject = match.group(4).strip() if match.group(4) else None

            # Extract body until next From: or Gmail quote
            start_pos = match.end()
            next_delimiter = len(body)

            # Find next From: header
            next_from = body.find('\nFrom:', start_pos)
            if next_from > 0:
                next_delimiter = min(next_delimiter, next_from)

            # Find next Gmail quote
            next_gmail = body.find('\nOn ', start_pos)
            if next_gmail > 0 and ' wrote:' in body[next_gmail:next_gmail+200]:
                next_delimiter = min(next_delimiter, next_gmail)

            embedded_body = body[start_pos:next_delimiter].strip()

            # NOTE: Don't truncate embedded body - we now properly extract disclaimers
            # and handle long content, so let the full body through

            # Clean up the addresses
            from_email = self.canonicalize_sender(from_addr)
            to_email = self.canonicalize_sender(to_addr)

            # Extract recipient list (handles semicolon-separated, quotes, etc.)
            to_list = self.extract_recipients(to_addr) if to_addr else []

            # Skip if invalid
            if not from_email or len(from_email) < 2:
                continue

            # Parse date
            parsed_date = self.parse_datetime(date_str)

            # Process body
            processed_body = self.fix_ocr_urls(embedded_body)
            processed_body, disclaimer = self.extract_disclaimer(processed_body)
            processed_body = self.strip_quoted_content(processed_body)

            embedded_emails.append({
                "from": from_email,
                "to": to_email,
                "to_list": to_list,
                "date": parsed_date["iso"] if parsed_date else date_str,
                "timestamp": parsed_date["timestamp"] if parsed_date else 0,
                "subject": subject,
                "body": processed_body,
                "disclaimer": disclaimer,
                "source_file": source_file,
                "is_embedded": True,
                "raw_date": date_str
            })

        # Pattern 2: Gmail-style quotes - "On [date] at [time], [name] <[email]> wrote:"
        # Examples:
        # - On Mon, Jun 3, 2019 at 9:12 AM Weingarten, Reid < > wrote:
        # - On Mon, Jun 3, 2019 at 9:12 AM, Weingarten, Reid <email@example.com> wrote:
        # - On Sat, Jul 6, 2019 at 1:55 PM Weingarten, Reid < It is Todd kozel... (missing "wrote:")
        # Format: On [Day, Month DD, YYYY] at [H:MM AM/PM] [sender info] [optional "wrote:"] [body]
        # Made more lenient to handle incomplete quotes and missing "wrote:"
        gmail_pattern = r'(?:^|\n)On\s+([A-Z][a-z]{2},\s+[A-Z][a-z]{2,}\s+\d{1,2},\s+\d{4})\s+at\s+([\d:]+\s+[AP]M)\s*,?\s*(.+?)(?:\s+wrote:)?\s*[:\n]\s*(.+?)(?=\n(?:From:|On\s+[A-Z][a-z]{2},|$))'
        gmail_matches = list(re.finditer(gmail_pattern, body, re.MULTILINE | re.DOTALL))

        for match in gmail_matches:
            date_part = match.group(1).strip()
            time_part = match.group(2).strip()
            sender_part = match.group(3).strip()  # "Weingarten, Reid < >" or "Weingarten, Reid <email@example.com>"
            quoted_body = match.group(4).strip()

            # Combine date and time
            date_str = f"{date_part} at {time_part}"

            # Extract name and email from sender_part
            # Format can be: "Name < >" or "Name <email@example.com>" or just "Name"
            email_match = re.search(r'<([^>]+)>', sender_part)
            if email_match:
                from_email_raw = email_match.group(1).strip()
                from_name = sender_part[:email_match.start()].strip()
            else:
                from_email_raw = None
                from_name = sender_part

            # Use email if valid, otherwise use name
            if from_email_raw and '@' in from_email_raw:
                from_email = self.canonicalize_sender(from_email_raw)
            else:
                from_email = self.canonicalize_sender(from_name)

            # Skip if invalid
            if not from_email or len(from_email) < 2:
                continue

            # Limit quoted body
            if len(quoted_body) > 500:
                quoted_body = quoted_body[:500]

            # Parse date (Gmail format: "Mon, Jun 3, 2019 at 9:12 AM")
            parsed_date = self.parse_datetime(date_str)

            embedded_emails.append({
                "from": from_email,
                "to": None,  # Gmail quotes don't show recipient
                "to_list": [],
                "date": parsed_date["iso"] if parsed_date else date_str,
                "timestamp": parsed_date["timestamp"] if parsed_date else 0,
                "subject": None,  # Gmail quotes usually don't show subject
                "body": quoted_body,
                "source_file": source_file,
                "is_embedded": True,
                "raw_date": date_str
            })

        return embedded_emails

    def parse_traditional_format(self, content: str, file_path: str) -> Optional[Dict]:
        """Parse traditional email format (From:, Sent:, To:, Subject:) - returns list including embedded emails"""
        try:
            # Remove UTF-8 BOM if present
            if content.startswith('\ufeff'):
                content = content[1:]

            # Decode common HTML entities early
            content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            content = content.replace('©', '@').replace('&#64;', '@')  # Email symbol variations

            lines = content.split('\n')

            # Extract fields - only from lines that start with these keywords
            from_match = None
            to_match = None
            cc_match = None
            sent_match = None
            subject_match = None
            importance_match = None
            last_header_idx = 0

            for idx, line in enumerate(lines):
                # Don't strip - check actual line start
                # Only capture the FIRST occurrence of each header (don't overwrite)
                if line.startswith("From:") and not from_match:
                    from_match = line[5:].strip()
                    last_header_idx = idx
                elif line.startswith("To:") and not to_match:
                    to_match = line[3:].strip()
                    last_header_idx = idx
                elif (line.startswith("CC:") or line.startswith("Cc:")) and not cc_match:
                    cc_match = line[3:].strip()
                    last_header_idx = idx
                elif line.startswith("Sent:") and not sent_match:
                    sent_match = line[5:].strip()
                    last_header_idx = idx
                elif line.startswith("Date:") and not sent_match:
                    # Use Date: field if Sent: is not present
                    sent_match = line[5:].strip()
                    last_header_idx = idx
                elif line.startswith("Subject:") and not subject_match:
                    subject_match = line[8:].strip()
                    last_header_idx = idx
                elif line.startswith("Importance:") and not importance_match:
                    importance_match = line[11:].strip()
                    last_header_idx = idx

            # Must have at least Sent or Date field
            if not sent_match:
                return None

            # From field is required but can be just a name (redacted emails)
            if not from_match:
                return None

            # Start body after last header
            body_start_idx = last_header_idx + 1 if last_header_idx > 0 else 0

            # Extract email body
            body_lines = []
            if body_start_idx > 0:
                for line in lines[body_start_idx:]:
                    # Stop at HOUSE_OVERSIGHT marker ONLY if it's a standalone marker line
                    # (not embedded in disclaimer text or other content)
                    stripped = line.strip()
                    if stripped and (stripped.startswith("HOUSE_OVERSIGHT") or stripped.startswith("HOUSE OVERSIGHT")) and len(stripped) < 50:
                        break
                    # Skip empty lines at start
                    if not body_lines and not line.strip():
                        continue
                    body_lines.append(line)

            body = '\n'.join(body_lines).strip()

            # Extract embedded emails BEFORE cleaning (they contain From:, To: patterns)
            embedded_emails = self.extract_embedded_emails(body, os.path.basename(file_path))

            # Remove common footer/signature patterns
            body = self.clean_email_body(body)

            # Skip group chat/multiple sender emails - return None to signal special handling
            if from_match and "multiple senders" in from_match.lower():
                # Set a flag to handle this in parse_file
                return None

            # Parse email addresses - handle names without emails
            from_email, from_name = self.extract_email_and_name(from_match)

            # Handle multiple recipients (To and CC)
            to_list = self.extract_recipients(to_match) if to_match else ["Unknown Recipient"]
            cc_list = self.extract_recipients(cc_match) if cc_match else []

            # Combine To and CC recipients, but keep them separate for display
            all_recipients = to_list.copy()
            if cc_list:
                all_recipients.extend(cc_list)

            to_email = to_list[0] if to_list else "Unknown Recipient"  # Use first recipient for primary
            to_name = None  # Name extraction handled in extract_recipients

            # If recipient is unknown, try to extract from email body
            if to_email == "Unknown Recipient" and body:
                extracted_recipient = self.extract_recipient_from_body(body)
                if extracted_recipient != "Unknown Recipient":
                    to_email = extracted_recipient
                    to_list = [extracted_recipient]
                    all_recipients = [extracted_recipient]

            # If no email found, treat the whole field as a name/identifier (already normalized)
            if not from_email:
                normalized = self.normalize_sender_field(from_match) if from_match else None
                from_email = normalized if normalized else None
                from_name = None

            # Parse datetime
            parsed_date = self.parse_datetime(sent_match)

            # Parse subject metadata
            subject_meta = self.parse_subject_metadata(subject_match)

            # Generate unique ID with source file and position
            email_id = self.generate_id(from_email, to_email, sent_match, subject_match or "",
                                       os.path.basename(file_path), 0)

            self.stats["traditional_format"] += 1

            # Process body: fix OCR URLs, extract disclaimer, strip quoted content
            processed_body = self.fix_ocr_urls(body)
            processed_body, disclaimer = self.extract_disclaimer(processed_body)
            processed_body = self.strip_quoted_content(processed_body)

            # Main email
            main_email = {
                "id": email_id,
                "format": "traditional",
                "from": from_email,
                "from_name": from_name,
                "to": to_email,
                "to_name": to_name,
                "to_list": to_list,  # Store To recipients
                "cc_list": cc_list,  # Store CC recipients
                "subject": subject_match,
                "subject_clean": subject_meta["clean_subject"],
                "reply_depth": subject_meta["reply_depth"],
                "is_forward": subject_meta["is_forward"],
                "date": parsed_date["iso"] if parsed_date else sent_match,
                "timestamp": parsed_date["timestamp"] if parsed_date else 0,
                "body": processed_body,
                "disclaimer": disclaimer,
                "importance": importance_match,
                "source_file": os.path.basename(file_path),
                "is_epstein_sender": self.is_epstein_email(from_email) or self.is_epstein_name(from_name),
                "is_epstein_recipient": (
                    self.is_epstein_email(to_email) or
                    self.is_epstein_name(to_name) or
                    any(self.is_epstein_email(r) or self.is_epstein_name(r) for r in all_recipients) or
                    any(self.is_epstein_email(cc) or self.is_epstein_name(cc) for cc in cc_list) or
                    # Parse the raw to field directly (handles semicolon-separated lists with quotes)
                    any(self.is_epstein_email(r) or self.is_epstein_name(r) for r in self.parse_recipients(to_match or ""))
                ),
                "is_associate_sender": self.is_associate_name(from_email) or self.is_associate_name(from_name),
                "is_associate_recipient": (
                    self.is_associate_name(to_email) or
                    self.is_associate_name(to_name) or
                    any(self.is_associate_name(r) for r in all_recipients) or
                    any(self.is_associate_name(cc) for cc in cc_list)
                ),
                "associate_names": list(set(
                    self.get_associates_in_name(from_email) +
                    self.get_associates_in_name(from_name) +
                    self.get_associates_in_name(to_email) +
                    self.get_associates_in_name(to_name) +
                    [assoc for r in all_recipients for assoc in self.get_associates_in_name(r)] +
                    [assoc for cc in cc_list for assoc in self.get_associates_in_name(cc)]
                )),
                "raw_date": sent_match,
                "is_embedded": False
            }

            # Mark email as irrelevant if it matches spam/fragment patterns
            main_email["is_irrelevant"] = self.is_irrelevant_email(main_email)

            # Return list: [main_email] + embedded_emails
            # If there are embedded emails, return all of them
            if embedded_emails:
                # Update embedded emails with proper metadata
                for idx, emb in enumerate(embedded_emails, start=1):
                    emb["id"] = self.generate_id(emb["from"], emb["to"], emb.get("raw_date", ""), emb.get("subject", ""),
                                                 os.path.basename(file_path), idx)
                    emb["format"] = "traditional"
                    emb["from_name"] = None
                    emb["to_name"] = None
                    emb["cc_list"] = []
                    emb["subject_clean"] = emb.get("subject", "")
                    emb["reply_depth"] = 0
                    emb["is_forward"] = False
                    emb["importance"] = None
                    emb["is_epstein_sender"] = self.is_epstein_email(emb["from"]) or self.is_epstein_name(emb.get("from_name", ""))
                    emb["is_epstein_recipient"] = (
                        self.is_epstein_email(emb.get("to")) or
                        self.is_epstein_name(emb.get("to_name", "")) or
                        any(self.is_epstein_email(cc) or self.is_epstein_name(cc) for cc in emb.get("cc_list", [])) or
                        # Parse the raw to field directly for embedded emails too
                        any(self.is_epstein_email(r) or self.is_epstein_name(r) for r in self.parse_recipients(emb.get("to", "")))
                    )
                    emb["is_associate_sender"] = self.is_associate_name(emb["from"]) or self.is_associate_name(emb.get("from_name", ""))
                    emb["is_associate_recipient"] = (
                        self.is_associate_name(emb.get("to")) or
                        self.is_associate_name(emb.get("to_name", "")) or
                        any(self.is_associate_name(r) for r in emb.get("to_list", [])) or
                        any(self.is_associate_name(cc) for cc in emb.get("cc_list", []))
                    )
                    emb["associate_names"] = list(set(
                        self.get_associates_in_name(emb["from"]) +
                        self.get_associates_in_name(emb.get("from_name", "")) +
                        self.get_associates_in_name(emb.get("to", "")) +
                        self.get_associates_in_name(emb.get("to_name", "")) +
                        [assoc for r in emb.get("to_list", []) for assoc in self.get_associates_in_name(r)] +
                        [assoc for cc in emb.get("cc_list", []) for assoc in self.get_associates_in_name(cc)]
                    ))
                    # Mark embedded email as irrelevant if it matches spam/fragment patterns
                    emb["is_irrelevant"] = self.is_irrelevant_email(emb)

                return [main_email] + embedded_emails
            else:
                return main_email  # Return single email as before for compatibility

        except Exception as e:
            print(f"Error parsing traditional format: {e}")
            return None

    def parse_group_chat(self, content: str, file_path: str) -> List[Dict]:
        """Parse group chat format (Multi-line conversation extracted from body)"""
        emails = []

        # Extract the body content
        body_match = re.search(r'Subject:.*?\n(.*)', content, re.DOTALL)
        if not body_match:
            return []

        body = body_match.group(1)
        lines = [line.strip() for line in body.split('\n')]

        # Remove empty lines and document markers upfront
        lines = [line for line in lines if line and 'HOUSE_OVERSIGHT' not in line and 'HOUSE OVERSIGHT' not in line]

        if not lines:
            return []

        # Find all timestamp indices - these are the anchors for parsing
        timestamp_indices = []
        for i, line in enumerate(lines):
            if re.match(r'^\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M$', line):
                timestamp_indices.append(i)

        if not timestamp_indices:
            return []

        # Parse each message block
        for idx, ts_idx in enumerate(timestamp_indices):
            # The sender should be the line immediately before the timestamp
            if ts_idx == 0:
                continue  # No sender line available

            sender_idx = ts_idx - 1
            sender = lines[sender_idx]
            timestamp = lines[ts_idx]

            # Validate sender looks like a real name (not a phone number, artifact, etc.)
            if not self.is_valid_sender_name(sender):
                continue

            # Collect message lines (everything between this timestamp and the next sender/timestamp)
            message_lines = []
            next_sender_idx = timestamp_indices[idx + 1] - 1 if idx + 1 < len(timestamp_indices) else len(lines)

            for i in range(ts_idx + 1, next_sender_idx):
                message_lines.append(lines[i])

            message = ' '.join(message_lines).strip()

            # Skip messages with no content
            if not message:
                continue

            # Parse datetime
            parsed_date = self.parse_datetime(timestamp)

            # Normalize sender (could be email or username)
            sender_email, sender_name = self.extract_email_and_name(sender)
            if not sender_email:
                # Use normalized name as identifier for usernames
                sender_email = self.normalize_sender_field(sender)

            # Try to extract recipient from message body
            recipient = self.extract_recipient_from_body(message)

            # Process body
            processed_msg = self.fix_ocr_urls(message)
            processed_msg, disclaimer = self.extract_disclaimer(processed_msg)
            processed_msg = self.strip_quoted_content(processed_msg)

            emails.append({
                "id": self.generate_id(sender_email, recipient, timestamp, message[:50],
                                      os.path.basename(file_path), idx),
                "format": "chat",
                "from": sender_email,
                "from_name": sender_name,
                "to": recipient,
                "to_name": None,
                "to_list": [recipient],
                "subject": None,
                "subject_clean": "",
                "reply_depth": 0,
                "is_forward": False,
                "date": parsed_date["iso"] if parsed_date else timestamp,
                "timestamp": parsed_date["timestamp"] if parsed_date else 0,
                "body": processed_msg,
                "disclaimer": disclaimer,
                "importance": None,
                "source_file": os.path.basename(file_path),
                "is_epstein_sender": self.is_epstein_email(sender_email),
                "is_epstein_recipient": False,
                "raw_date": timestamp
            })

        return emails

    def is_valid_sender_name(self, name: str) -> bool:
        """Validate that a string looks like a sender name (not a phone number, timestamp, etc.)"""
        if not name:
            return False

        # Skip phone numbers (e.g., +13109906526)
        if re.match(r'^\+?\d{10,}$', name):
            return False

        # Skip lines that start with "Time:" (parsing artifacts)
        if name.startswith("Time:"):
            return False

        # Skip document markers
        if "HOUSE" in name.upper() or "OVERSIGHT" in name.upper():
            return False

        # Skip lines that look like timestamps themselves
        if re.match(r'^\d{2}/\d{2}/\d{4}', name):
            return False

        # Skip very short names (likely artifacts)
        if len(name) < 2:
            return False

        # Must contain at least some alphanumeric characters
        if not re.search(r'[a-zA-Z0-9]', name):
            return False

        # Skip lines that are mostly numbers (like "(581951477)")
        if re.match(r'^[\d\(\)\s\-]+$', name):
            return False

        return True

    def parse_message_format(self, content: str, file_path: str) -> Optional[Dict]:
        """Parse Message: format (GUID, Message:, Sender:, Time:) - returns list of emails"""
        try:
            # Split content into individual email blocks using GUID as delimiter
            email_blocks = re.split(r'(?=GUID:\s*[A-F0-9-]+)', content)
            email_blocks = [block.strip() for block in email_blocks if 'GUID:' in block]

            if not email_blocks:
                return None

            # Parse each email block and collect all emails
            all_emails = []

            for block_idx, block in enumerate(email_blocks):
                # Extract fields from this block
                guid_match = re.search(r'GUID:\s*([A-F0-9-]+)', block)
                message_match = re.search(r'Message:\s*(.+?)(?=\nSender:|$)', block, re.DOTALL)
                sender_match = re.search(r'Sender:\s*(.+?)(?=\n|$)', block)
                time_match = re.search(r'Time:\s*(.+?)(?=\n|$)', block)
                flags_match = re.search(r'Flags:\s*(.+?)(?=\n|$)', block)

                if not (guid_match and message_match and sender_match and time_match):
                    continue

                guid = guid_match.group(1).strip()
                message = message_match.group(1).strip()
                sender = sender_match.group(1).strip()
                time_str = time_match.group(1).strip()
                flag_str = flags_match.group(1).strip() if flags_match else ""

                # Validate sender - skip if it looks like a timestamp or invalid pattern
                if (sender.startswith('Time:') or
                    re.match(r'^\d{2}/\d{2}/\d{2}', sender) or  # Matches dates
                    re.match(r'^[\d\s\+\-\(\)]+$', sender) or   # Matches phone numbers/digit only
                    len(sender) < 2):
                    continue

                # Parse email from sender
                sender_email, sender_name = self.extract_email_and_name(sender)

                # If no valid email, use normalized sender name
                if not sender_email:
                    sender_email = self.normalize_sender_field(sender)

                # Skip if sender is still invalid after normalization
                if not sender_email or sender_email.startswith('Time:'):
                    continue

                # Clean message body
                message = self.clean_email_body(message)

                # Try to extract recipient from body
                recipient = self.extract_recipient_from_body(message)

                # Parse datetime
                parsed_date = self.parse_datetime(time_str)

                # Parse subject metadata (even though no subject in message format)
                subject_meta = self.parse_subject_metadata(None)

                # Generate unique ID with source file and block position
                email_id = self.generate_id(sender_email, recipient, time_str, message[:50],
                                           os.path.basename(file_path), block_idx)

                # Process body
                processed_msg = self.fix_ocr_urls(message)
                processed_msg, disclaimer = self.extract_disclaimer(processed_msg)
                processed_msg = self.strip_quoted_content(processed_msg)

                all_emails.append({
                    "id": email_id,
                    "guid": guid,
                    "format": "message",
                    "from": sender_email,
                    "from_name": sender_name,
                    "to": recipient,
                    "to_name": None,
                    "to_list": [recipient],
                    "subject": None,
                    "subject_clean": "",
                    "reply_depth": 0,
                    "is_forward": False,
                    "date": parsed_date["iso"] if parsed_date else time_str,
                    "timestamp": parsed_date["timestamp"] if parsed_date else 0,
                    "body": processed_msg,
                    "disclaimer": disclaimer,
                    "flags": flag_str,
                    "source_file": os.path.basename(file_path),
                    "is_epstein_sender": self.is_epstein_email(sender_email),
                    "is_epstein_recipient": False,
                    "raw_date": time_str
                })

            if all_emails:
                self.stats["message_format"] += len(all_emails)
                # Return the first email, but we'll need to handle multiple emails per file
                # Actually, let's modify parse_file to handle this
                return all_emails

            return None

        except Exception as e:
            print(f"Error parsing message format: {e}")
            return None

    def clean_ocr_artifacts(self, name: str) -> str:
        """Remove common OCR artifacts from names

        Targets specific patterns found in analysis:
        - [mailto and [mailto: patterns
        - Malformed email addresses in brackets
        - Trailing [ ii, [ il, etc. OCR garbage
        - Spaces in email addresses (e.g., "gma il.com")
        """
        if not name:
            return ""

        # Remove [mailto: and [mailto patterns
        name = re.sub(r'\s*\[mailto:?[^\]]*$', '', name)
        name = re.sub(r'\s*\[mailto:?[^\]]*\]', '', name)

        # Remove malformed email addresses in brackets (with spaces)
        # e.g., "[jeevacation@gma il.com"
        name = re.sub(r'\[[\w\-\.]+@[\w\s\-\.]+\]?', '', name)

        # Remove trailing OCR garbage like "[ ii", "[ il", "[ I", etc.
        name = re.sub(r'\s*\[\s*[il1I]+\s*$', '', name)

        # Remove standalone brackets
        name = re.sub(r'\s*\[\s*$', '', name)
        name = re.sub(r'^\s*\]', '', name)

        return name.strip()

    def normalize_sender_field(self, field: str) -> str:
        """Clean sender field of all OCR artifacts and formatting issues"""
        if not field:
            return ""

        # Remove leading/trailing quotes (both single and double)
        field = field.strip()
        if (field.startswith('"') and field.endswith('"')) or \
           (field.startswith("'") and field.endswith("'")):
            field = field[1:-1].strip()

        # Apply dedicated OCR artifact cleaning
        field = self.clean_ocr_artifacts(field)

        # Remove [mailto: patterns (kept for legacy compatibility)
        field = re.sub(r'\s*\[mailto:[^\]]*\]', '', field)

        # Remove everything after < or ‹ or other bracket chars (email artifacts)
        # This handles "Name <email@..." or "Name ‹email..." or "Name •(.111>"
        field = re.sub(r'\s*[<‹〈\(].*$', '', field)

        # Remove trailing/leading underscores and dashes (OCR artifacts)
        field = re.sub(r'[_\-]+$', '', field)
        field = re.sub(r'^[_\-]+', '', field)

        # Remove trailing dots and special chars (OCR garbage like ".111.>")
        field = re.sub(r'[\.\s]*[›〉>\]]+.*$', '', field)

        # Remove HTML tags like "< br>"
        field = re.sub(r'<\s*/?\s*[a-z]+\s*>', '', field, flags=re.IGNORECASE)

        # Remove incomplete brackets
        field = re.sub(r'[<\[‹〈]\s*$', '', field)
        field = re.sub(r'^\s*[>\]›〉]', '', field)

        # Remove HTML entities
        field = field.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

        # Remove common OCR artifacts: bullet points, special chars, etc.
        field = re.sub(r'[•●○◦▪▫]', '', field)

        # Remove "Subject:" artifacts that sometimes appear
        field = re.sub(r'Subject:\s*.*$', '', field, flags=re.IGNORECASE)

        # Remove parenthetical suffixes like "(bgC3)" or "(bgC3) <-"
        field = re.sub(r'\s*\([^)]*\)\s*[<\-]*\s*$', '', field)

        # Collapse multiple spaces
        field = re.sub(r'\s+', ' ', field).strip()

        # Remove pure whitespace/symbols
        if re.match(r'^[\s\-_<>\[\]()]+$', field):
            return ""

        return field

    def extract_recipients(self, field: str) -> List[str]:
        """Extract multiple recipients from a field (handles ; and , delimiters)"""
        if not field:
            return ["Unknown Recipient"]

        # IMPORTANT: We need to handle "LastName, FirstName" patterns WITHOUT splitting them
        # Strategy: Temporarily replace these patterns with placeholders, then split, then restore

        # Find all "LastName, FirstName" patterns (e.g., "Weingarten, Reid", "Smith, John")
        # Pattern: word(s) + comma + space + 1-2 words (first name, possibly middle initial)
        # Must not be followed by additional words (which would indicate multiple recipients)
        lastname_firstname_pattern = r'\b([A-Za-z][a-z]*(?:\s+[A-Za-z][a-z]*)*),\s+([A-Za-z][a-z]*(?:\s+[A-Za-z]\.?)?)\b(?!\s+[A-Za-z])'

        # Store the matches and replace with placeholders
        protected = []
        def protect_name(match):
            full_name = match.group(0)
            protected.append(full_name)
            return f"__PROTECTED_{len(protected)-1}__"

        field_protected = re.sub(lastname_firstname_pattern, protect_name, field.strip())

        # Now split by semicolons, commas, or multiple whitespace
        recipients = re.split(r'[;,]\s*|\s{2,}', field_protected)

        result = []
        for recipient in recipients:
            recipient = recipient.strip()

            # Restore protected "LastName, FirstName" patterns
            for i, protected_name in enumerate(protected):
                recipient = recipient.replace(f"__PROTECTED_{i}__", protected_name)

            if not recipient:
                continue

            # Skip invalid recipients that are just punctuation or single characters
            if recipient in ['.', '-', '_', ':', ';', ','] or len(recipient) == 1:
                continue

            # Skip recipients that are just whitespace or symbols
            if re.match(r'^[\s\.\-_<>\[\]()]+$', recipient):
                continue

            email, name = self.extract_email_and_name(recipient)
            if email:
                result.append(email)
            elif name:
                # Use the cleaned name returned by extract_email_and_name
                # (OCR artifacts have been stripped)

                # Additional cleanup: strip trailing/leading punctuation and numbers
                name = re.sub(r'[\s_\-\.;:,]+$', '', name)  # Trailing punctuation
                name = re.sub(r'^[\s_\-\.;:,]+', '', name)  # Leading punctuation
                name = re.sub(r'\s+\d{5,}[\.\-=]*$', '', name)  # Trailing OCR number sequences (5+ digits, possibly with punctuation)
                name = re.sub(r'\s+[\d=\-\.\|]+$', '', name)  # Remove patterns like "111=11"

                # Remove trailing single characters (OCR artifacts like " I", " l", etc.)
                name = re.sub(r'\s+[IilL1]$', '', name)

                # Remove trailing special character combinations (OCR artifacts like "'IL", "`", "BT", etc.)
                name = re.sub(r"['`]+[IiLl]*$", '', name)
                name = re.sub(r'\s+(BT|Bt|bt)$', '', name, flags=re.IGNORECASE)

                name = re.sub(r'[\.,]$', '', name)  # Remove trailing period or comma
                name = name.strip()

                # Skip if name becomes empty or invalid after cleanup
                if not name or len(name) < 2:
                    continue

                name_lower = name.lower()
                if name_lower in self.NAME_CORRECTIONS:
                    result.append(self.NAME_CORRECTIONS[name_lower])
                else:
                    result.append(name)
            elif recipient and recipient.lower() not in ['[redacted]', 'redacted', '-']:
                # Fallback to original recipient if no name was extracted
                recipient_lower = recipient.lower()
                if recipient_lower in self.NAME_CORRECTIONS:
                    result.append(self.NAME_CORRECTIONS[recipient_lower])
                else:
                    result.append(recipient)

        return result if result else ["Unknown Recipient"]

    def extract_recipient_from_body(self, body: str) -> str:
        """Extract recipient from quoted email in body when recipient is unknown"""
        if not body:
            return "Unknown Recipient"

        # SPECIAL CASE: If this is a forwarded message, look for who it was forwarded TO
        # Forwarded messages have the forward recipient at the TOP before the forwarded content
        forward_markers = [
            r'[-\s]*Forwarded [Mm]essage[-\s]*',
            r'Begin forwarded message:',
            r'Fwd:',
            r'FW:'
        ]

        is_forward = any(re.search(marker, body[:500], re.IGNORECASE) for marker in forward_markers)

        if is_forward:
            # In a forward, the FIRST occurrence of recipient info is who it was forwarded TO
            # Look for "To: Name" or similar BEFORE the forward marker
            forward_to_patterns = [
                # Look for the first To: line (before forwarded content)
                (r'^To:\s*([^<‹\n]+?)\s*[<‹〈]([^>›〉@]+@[^>›〉]+)[>›〉]', True),
                (r'^To:\s*([A-Za-z][A-Za-z\s\.]+?)(?:\n|$)', False),
            ]

            for pattern, has_email in forward_to_patterns:
                match = re.search(pattern, body[:1000], re.MULTILINE | re.IGNORECASE)
                if match:
                    if has_email and len(match.groups()) >= 2:
                        email = match.group(2).strip()
                        if self.is_valid_email(email):
                            return self.normalize_email(email)
                    else:
                        name = match.group(1).strip()
                        name = self.normalize_sender_field(name)
                        if name and not self.is_greeting(name) and len(name) > 2:
                            return name

        # Look for common quoted email patterns (in order of specificity)
        # Note: Using [<‹〈] to match various unicode brackets
        patterns = [
            # Pattern: "On [date], Name <email@domain.com> wrote:" - most reliable
            (r'On\s+[^,]+,\s+([^<‹\n]+?)\s*[<‹〈]([^>›〉@]+@[^>›〉]+)[>›〉]\s+wrote:', True),
            # Pattern: "> From: Name <email@domain.com>" or "From: Name ‹email›" in quoted section
            (r'[>\s]*From:\s*([^<‹\n]+?)\s*[<‹〈]([^>›〉@]+@[^>›〉]+)[>›〉]', True),
            # Pattern: "-----Original Message-----\n> From: Name <email>"
            (r'Original Message[^\n]*\n[>\s]*From:\s*([^<‹\n]+?)\s*[<‹〈]([^>›〉@]+@[^>›〉]+)[>›〉]', True),
            # Pattern: "> From: Name" (name only, no brackets/email)
            (r'[>\s]+From:\s*([A-Z][A-Za-z\s\.]+?)\s*(?:\n|$)', False),
            # Pattern: "On [date], Name wrote:" (no email)
            (r'On\s+[A-Z][a-z]+,\s+[A-Z][a-z]+\s+\d+,\s+\d{4}[^,]+,\s+([A-Za-z][A-Za-z\s\.]+?)\s+wrote:', False),
            # Pattern: "From: Name" at start of quoted section (no >)
            (r'^From:\s*([A-Z][A-Za-z\s\.]+?)\s*(?:\n|[<‹])', False),
        ]

        for pattern, has_email in patterns:
            match = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
            if match:
                if has_email and len(match.groups()) >= 2:
                    # Has both name and email
                    name = match.group(1).strip()
                    email = match.group(2).strip()

                    # Validate the email
                    if self.is_valid_email(email):
                        return self.normalize_email(email)
                else:
                    # Just has name
                    name = match.group(1).strip()

                # Clean up and validate the extracted name
                name = re.sub(r'[>\s]+$', '', name)  # Remove trailing > and spaces
                name = re.sub(r'^[>\s]+', '', name)  # Remove leading > and spaces
                name = self.normalize_sender_field(name)

                # Validate it's not a greeting or salutation
                if name and not self.is_greeting(name):
                    # Further validate it looks like a name
                    if name.lower() not in ['[redacted]', 'redacted', '-', ''] and len(name) > 2:
                        # Check if it has email format
                        email, display_name = self.extract_email_and_name(name)
                        return email if email else name

        return "Unknown Recipient"

    def is_greeting(self, text: str) -> bool:
        """Check if text is a common email greeting or salutation"""
        if not text:
            return False

        text_lower = text.lower().strip()

        # Common greetings
        greetings = [
            'dear', 'hi', 'hello', 'hey', 'greetings',
            'good morning', 'good afternoon', 'good evening',
            'to whom it may concern', 'ladies and gentlemen'
        ]

        # Check if text starts with a greeting
        for greeting in greetings:
            if text_lower.startswith(greeting):
                return True

        # Check if it's just "Dear [Name]" pattern
        if re.match(r'^dear\s+[a-z\s]+[—\-:]?\s*$', text_lower):
            return True

        return False

    def extract_email_and_name(self, field: str) -> Tuple[str, str]:
        """Extract email address and name from field like 'Name [email@domain.com]'"""
        if not field:
            return None, None

        # Basic cleanup but preserve brackets for email extraction
        field = field.strip()

        # Check for redacted/empty fields
        if not field or field.lower() in ['[redacted]', 'redacted', '-']:
            return None, None

        # Pattern: Name [email@domain.com] or Name [OCR garbage]
        # Check this BEFORE normalize_sender_field which removes trailing ]
        bracket_match = re.search(r'\[([^\]]+)\]', field)
        if bracket_match:
            bracket_content = bracket_match.group(1).strip()
            # Validate it's actually an email
            if self.is_valid_email(bracket_content):
                # Normalize email
                email = self.normalize_email(bracket_content)
                name = field[:bracket_match.start()].strip()
                # Normalize the name
                name = self.normalize_sender_field(name) if name else None
                return email, name
            else:
                # Bracket contains OCR garbage, not a valid email - strip it
                field = field[:bracket_match.start()].strip()
                # Now normalize the cleaned field
                field = self.normalize_sender_field(field)
                # Continue to other pattern checks below

        # Now normalize the field for other pattern checks
        if not bracket_match:
            field = self.normalize_sender_field(field)

        # Check again for empty after normalization
        if not field:
            return None, None

        # Pattern: email@domain.com or Name <email@domain.com>
        email_match = re.search(r'[\w\.\-+:]+@[\w\.\-]+\.[a-zA-Z]{2,}', field)
        if email_match:
            email = email_match.group(0)
            # Validate it's actually an email
            if self.is_valid_email(email):
                # Normalize email
                email = self.normalize_email(email)
                # Check if there's a name before the email
                name = field[:email_match.start()].strip()
                # Clean up name (remove < > if present)
                name = re.sub(r'[<>]', '', name).strip()
                return email, name if name else None

        # No valid email found - return cleaned field as name
        # field may have been cleaned of OCR artifacts above
        return None, field if field else None

    def normalize_email(self, email: str) -> str:
        """Normalize email address - fix OCR typos and case"""
        if not email:
            return email

        # Remove e: prefix if present
        if email.lower().startswith("e:"):
            email = email[2:]

        # Convert to lowercase for comparison
        email_lower = email.lower().strip()

        # Apply known corrections
        if email_lower in self.EMAIL_CORRECTIONS:
            return self.EMAIL_CORRECTIONS[email_lower]

        # Return lowercase version
        return email_lower

    def is_valid_email(self, email: str) -> bool:
        """Validate that a string is actually an email address"""
        if not email or '@' not in email:
            return False

        # Remove e: prefix if present for validation
        test_email = email
        if email.lower().startswith("e:"):
            test_email = email[2:]

        # Must have @ and a TLD
        pattern = r'^[\w\.\-+]+@[\w\.\-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, test_email):
            return False

        # Split and validate parts
        parts = test_email.split('@')
        if len(parts) != 2:
            return False

        local, domain = parts

        # Local part shouldn't be empty or too long
        if not local or len(local) > 64:
            return False

        # Domain should have at least one dot and valid TLD
        if '.' not in domain:
            return False

        domain_parts = domain.split('.')
        tld = domain_parts[-1]

        # TLD should be at least 2 chars and not obvious OCR errors
        if len(tld) < 2 or tld in ['corn', 'cam', 'cpm']:
            return False

        return True

    def parse_datetime(self, date_str: str) -> Optional[Dict]:
        """Parse various datetime formats"""
        if not date_str:
            return None

        # Common formats in the data
        formats = [
            "%m/%d/%Y %I:%M:%S %p",  # 6/15/2018 1:47:13 PM
            "%m/%d/%Y %I:%M:%S%p",   # 6/15/2018 1:47:13PM
            "%m/%d/%Y %I:%M %p",     # 1/25/2019 1:11 PM
            "%m/%d/%y %I:%M:%S %p (%f)",  # 07/25/18 02:29:14 PM (554246954)
            "%m/%d/%y %I:%M:%S %p",  # 07/25/18 02:29:14 PM
            # Embedded email formats (formal headers)
            "%A, %B %d, %Y %I:%M %p",     # Monday, June 3, 2019 8:31 AM
            "%A, %B %d, %Y %I:%M:%S %p",  # Tuesday, December 20, 2016 12:05 PM
            "%A, %B %d, %Y %I:%M%p",      # Monday, June 3, 2019 8:31AM (no space)
            # Gmail-style quote formats
            "%a, %b %d, %Y at %I:%M %p",  # Mon, Jun 3, 2019 at 9:12 AM
            "%a, %b %d, %Y at %I:%M:%S %p",  # Mon, Jun 3, 2019 at 9:12:00 AM
            # European date formats (DD/MM/YYYY)
            "%d/%m/%Y %I:%M %p",     # 15/10/2014 4:46 PM
            "%d/%m/%Y %I:%M:%S %p",  # 15/10/2014 4:46:30 PM
            # European with 24-hour time
            "%d/%m/%Y %H:%M",        # 16/01/2015 05:16
            "%d/%m/%Y %H:%M:%S",     # 16/01/2015 05:16:00
            # Weekday with "at" patterns
            "%A, %B %d, %Y at %I:%M %p",     # Monday, November 16, 2009 at 7:48 PM
            "%A, %B %d, %Y at %I:%M:%S %p",  # Monday, November 16, 2009 at 7:48:30 PM
            # Month name with "at" and optional timezone
            "%B %d, %Y at %I:%M:%S %p",      # December 15, 2016 at 10:59:39 AM (timezone stripped below)
            "%B %d, %Y at %I:%M %p",         # December 15, 2016 at 10:59 AM
            # RFC-style dates with numeric timezone offset
            "%a, %d %b %Y %H:%M:%S %z",      # Sun, 22 Jul 2018 22:01:54 +0200
            "%a, %d %b %Y %H:%M:%S",         # Fri, 4 Mar 2011 11:14:35 (no offset)
            "%a, %b %d, %Y %I:%M %p",        # Mon, Aug 20, 2012 2:32 pm
            # Weekday, Month day YEAR (NO comma before year - common pattern!)
            "%A, %B %d %Y %I:%M %p",         # Monday, August 26 2013 02:46 PM
            "%A, %B %d %Y %I:%M:%S %p",      # Wednesday, April 17 2019 11:43:15 AM
            # Short month formats
            "%b %d, %Y %I:%M %p",            # Jan 30, 2015 12:25 PM
            "%b %d, %Y, %I:%M:%S %p",        # May 22, 2013, 8:54:07 PM
            # Dates with timezone at end (before stripping)
            "%m/%d/%Y %I:%M %p",             # 03/07/2011 02:04 PM (EST stripped by regex)
            # Day Month Year formats
            "%d %B %Y at %H: %M",            # 2 January 2015 at 20: 38 (note space in time)
            # Weekday without comma before date
            "%a %m/%d/%Y %I:%M %p",          # Mon 3/7/2011 12:18 PM
            "%a %m/%d/%Y %I:%M:%S %p",       # Mon 3/7/2011 12:18:00 PM
            "%A, %B %d %Y %I:%M %p",         # Friday, March 4 2011 04:40 PM (no comma before year)
            "%A, %B %d %Y %I:%M:%S %p",      # Friday, March 4 2011 04:40:00 PM
            # Comma after year formats
            "%B %d, %Y, %I:%M:%S %p",        # January 30, 2015, 12:00:34 PM (comma before time)
            "%B %d, %Y %I:%M:%S %p",         # April 6, 2011 10:28:36 AM (no comma, timezone stripped)
            # Day-first with 24-hour
            "%A, %d %B %Y %H:%M",            # Sunday, 15 January 2017 05:51
            "%A, %d %B %Y %H:%M:%S",         # Sunday, 15 January 2017 05:51:00
            # RFC with timezone in parens (stripped by regex)
            "%a, %d %b %Y %H:%M:%S %z",      # Fri, 1 Jul 2016 07:01:36 -0400 (EDT)
            # Short month with comma after year
            "%A, %b %d, %Y, %I:%M %p",       # Tuesday, Jan 24, 2017, 10:04 AM
            # Day Month Year 24-hour (no weekday)
            "%d %B %Y %H:%M",                # 24 July 2018 21:54
            "%d %B, %Y %H:%M %p",            # 18 January, 2013 2:40 AM
            # Period instead of comma after day
            "%A, %B %d. %Y %H:%M",           # Thursday, January 28. 2010 11:24
            # Short month 24-hour
            "%b %d, %Y %H:%M:%S",            # Oct 12, 2009 17:44:42
            # Month day year 12-hour without weekday
            "%B %d, %Y %I:%M %p",            # November 16, 2017 3:26 PM
            # Short weekday with full date and parens
            "%a %m/%d/%Y %I:%M:%S %p",       # Fri 10/7/2016 10:30:45 PM (UTC stripped)
            # Date-only formats
            "%B %d, %Y",             # January 23, 2009
            "%B %d, %Y",             # November 14, 2015
            "%m/%d/%Y",              # 06/20/2007
            "%m/%d/%y",              # 06/20/07
            "%d/%m/%Y",              # 07/24/2006 (European date-only)
        ]

        for fmt in formats:
            try:
                # Remove timestamp in parentheses if present
                clean_date = re.sub(r'\s*\(\d+\)\s*$', '', date_str)
                # Remove timezone suffixes: (GMT+XX:XX), EST, PST, etc.
                clean_date = re.sub(r'\s*\(GMT[+-]\d{2}:\d{2}\)\s*', '', clean_date)
                # Remove GMT+N or GMT-N (single digit)
                clean_date = re.sub(r'\s+GMT[+-]\d+\s*', ' ', clean_date)
                # Remove timezone in parens like (UTC), (EDT), etc.
                clean_date = re.sub(r'\s*\((EST|PST|CST|MST|EDT|PDT|CDT|MDT|UTC|GMT|GDT|BST|IST)\)\s*', ' ', clean_date)
                # Remove timezone abbreviations (expanded list, no $ anchor to catch mid-string)
                clean_date = re.sub(r'\s+(EST|PST|CST|MST|EDT|PDT|CDT|MDT|UTC|GMT|GDT|BST|IST)\s*', ' ', clean_date)
                dt = datetime.strptime(clean_date.strip(), fmt)
                return {
                    "iso": dt.isoformat(),
                    "timestamp": int(dt.timestamp()),
                    "display": dt.strftime("%Y-%m-%d %I:%M %p")
                }
            except:
                continue

        # If all parsing fails, return None
        return None

    def parse_subject_metadata(self, subject: str) -> Dict:
        """Extract metadata from subject line (Re:/Fwd: chains, dates, etc.)"""
        if not subject:
            return {"clean_subject": "", "reply_depth": 0, "is_forward": False}

        original = subject
        reply_count = 0
        is_forward = False

        # Count Re: and Fwd: prefixes
        while True:
            if re.match(r'^\s*re:\s*', subject, re.IGNORECASE):
                subject = re.sub(r'^\s*re:\s*', '', subject, flags=re.IGNORECASE)
                reply_count += 1
            elif re.match(r'^\s*(fwd?|fw):\s*', subject, re.IGNORECASE):
                subject = re.sub(r'^\s*(fwd?|fw):\s*', '', subject, flags=re.IGNORECASE)
                is_forward = True
            else:
                break

        return {
            "clean_subject": subject.strip(),
            "reply_depth": reply_count,
            "is_forward": is_forward,
            "original": original
        }

    def clean_email_body(self, body: str) -> str:
        """Clean up email body text"""
        if not body:
            return ""

        # Fix OCR-corrupted URLs by removing spaces within URL patterns
        # Pattern: https :// or http :// with spaces in domain and path
        def fix_url_spaces(match):
            url = match.group(0)
            # Remove all spaces from the URL
            return url.replace(' ', '')

        # Find and fix URLs with spaces (common OCR error)
        # Matches: https :// or http :// followed by domain and path with spaces
        # Captures until end of line or whitespace break (2+ spaces)
        body = re.sub(r'https?\s*:\s*//\s*[^\s]+(?:\s+[^\s]+)*?(?=\s{2,}|\n|$)', fix_url_spaces, body)

        # Fix common OCR errors
        # Fix "Thun" → "Thu" in date patterns (On Thun, → On Thu,)
        body = re.sub(r'\bOn\s+Thun,', 'On Thu,', body)

        # Fix standalone "Nobt" → "Nope" (common OCR error for short responses)
        body = re.sub(r'^\s*Nobt\s*$', 'Nope', body, flags=re.MULTILINE)

        # Fix "I " at start of line when followed by lowercase (likely "l")
        # Example: "I ike" → "like"
        body = re.sub(r'(?<=\n)I\s+([a-z])', r'l\1', body)

        # Remove multiple consecutive blank lines
        body = re.sub(r'\n\s*\n\s*\n+', '\n\n', body)

        # Remove page numbers and footer markers
        body = re.sub(r'Page \d+ of \d+', '', body)
        body = re.sub(r'HOUSE_OVERSIGHT_\d+', '', body)

        # Remove "Sent from my iPhone/iPad/BlackBerry" signatures
        body = re.sub(r'\n\s*Sent from my (iPhone|iPad|BlackBerry|Android).*$', '', body, flags=re.IGNORECASE)

        # NOTE: Do NOT remove disclaimers here - they are handled by extract_disclaimer() later
        # which properly extracts and canonicalizes them

        # Remove excessive underscores/dashes used as separators
        body = re.sub(r'\n_{10,}\n', '\n', body)
        body = re.sub(r'\n-{10,}\n', '\n', body)

        # Remove email header artifacts that sometimes appear in body
        body = re.sub(r'From:\s*\[mailto:.*?\]', '', body)
        body = re.sub(r'Sent:\s*\d+/\d+/\d+.*?\n', '', body)

        # Clean up common email signatures/footers
        lines = body.split('\n')
        cleaned_lines = []
        skip_rest = False

        for line in lines:
            if skip_rest:
                break

            # Skip lines that are just underscores or dashes
            if re.match(r'^[_\-\s]+$', line):
                continue

            # NOTE: Do NOT skip disclaimer lines here - they are handled by extract_disclaimer() later

            cleaned_lines.append(line)

        result = '\n'.join(cleaned_lines).strip()

        # Final cleanup - remove trailing whitespace from each line
        result = '\n'.join(line.rstrip() for line in result.split('\n'))

        return result

    def is_epstein_email(self, email: str) -> bool:
        """Check if email belongs to Epstein"""
        if not email:
            return False
        email_lower = email.lower().strip()
        return any(epstein_email.lower() in email_lower for epstein_email in self.EPSTEIN_EMAILS)

    def is_epstein_name(self, name: str) -> bool:
        """Check if name matches Epstein patterns"""
        if not name:
            return False
        name_lower = name.lower().strip()
        return any(pattern in name_lower for pattern in self.EPSTEIN_NAME_PATTERNS)

    def is_associate_name(self, name: str) -> bool:
        """Check if name matches known associate patterns"""
        if not name:
            return False
        name_lower = name.lower().strip()
        return any(assoc in name_lower for assoc in self.ASSOCIATE_NAMES)

    def get_associates_in_name(self, name: str) -> List[str]:
        """Return list of associate names found in the given name"""
        if not name:
            return []
        name_lower = name.lower().strip()
        found = []
        for assoc in self.ASSOCIATE_NAMES:
            if assoc in name_lower:
                # Return canonical form (title case)
                found.append(assoc.title())
        return found

    def is_irrelevant_email(self, email_dict: dict) -> bool:
        """
        Determine if an email is irrelevant (ONLY obvious spam - be conservative)
        IMPORTANT: Every email could be pivotal to the case, so only flag clear spam
        Criteria:
        1. Known spam senders (travel marketing, newsletters)
        2. Clear spam patterns (unsubscribe, marketing language)
        NOTE: Do NOT exclude fragments - they may provide important context
        """
        subject = (email_dict.get("subject") or "").lower()
        body = (email_dict.get("body") or "").lower()
        from_field = (email_dict.get("from") or "").lower()

        combined = f"{subject} {body} {from_field}"

        # Check for known spam senders only
        spam_senders = [
            'asmallworld@',  # Travel marketing spam
        ]

        for sender in spam_senders:
            if sender in from_field:
                return True

        # Only flag clear unsubscribe spam
        if 'unsubscribe' in combined and ('newsletter' in combined or 'mailing list' in combined):
            return True

        return False

    def parse_recipients(self, recipient_str: str) -> List[str]:
        """
        Parse semicolon or comma-separated recipient list
        Strips quotes and whitespace
        """
        if not recipient_str:
            return []

        # Strip quotes (both single and double)
        cleaned = recipient_str.replace("'", "").replace('"', '')

        # Split on semicolons and commas
        recipients = re.split(r'[;,]', cleaned)

        # Strip whitespace and filter empty strings
        return [r.strip() for r in recipients if r.strip()]

    def generate_id(self, from_email: str, to_email: str, date: str, subject: str, source_file: str = "", position: int = 0) -> str:
        """Generate unique ID for email using content + source metadata"""
        content = f"{from_email}|{to_email}|{date}|{subject}|{source_file}|{position}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def canonicalize_sender(self, sender: str) -> str:
        """Map sender to canonical form using discovered patterns"""
        if not sender:
            return sender

        # First, aggressively normalize the sender field
        sender = self.normalize_sender_field(sender)
        if not sender:
            return sender

        # Strip trailing OCR number garbage (5+ digits, possibly with punctuation)
        sender = re.sub(r'\s+\d{5,}[\.\-=]*$', '', sender)
        sender = re.sub(r'\s+[\d=\-\.\|]+$', '', sender)  # Remove patterns like "111=11"
        sender = sender.strip()

        # Remove trailing single characters (OCR artifacts like " I", " l", etc.)
        sender = re.sub(r'\s+[IilL1]$', '', sender)

        # Remove trailing special character combinations (OCR artifacts like "'IL", "`", "BT", etc.)
        sender = re.sub(r"['`]+[IiLl]*$", '', sender)
        sender = re.sub(r'\s+(BT|Bt|bt)$', '', sender, flags=re.IGNORECASE)
        sender = sender.strip()

        # Remove trailing single period or comma
        sender = re.sub(r'[\.,]$', '', sender).strip()

        # Extract email if present (handles "Name <email>" or "Name ‹email›")
        email, name = self.extract_email_and_name(sender)

        # If we found an email, use it
        if email:
            return self.normalize_email(email)

        # Normalize case and whitespace for name-only senders
        sender_clean = ' '.join(sender.split()).strip()
        sender_lower = sender_clean.lower()

        # FIRST: Check NAME_CORRECTIONS for OCR error fixes
        if sender_lower in self.NAME_CORRECTIONS:
            return self.NAME_CORRECTIONS[sender_lower]

        # Check canonical mapping
        if sender_lower in self.CANONICAL_SENDERS:
            return self.CANONICAL_SENDERS[sender_lower]

        # Check if we've seen this alias before
        if sender_lower in self.sender_aliases:
            return self.sender_aliases[sender_lower]

        # Return with normalized capitalization (Title Case for names)
        if re.match(r'^[A-Za-z\s\.]+$', sender_clean):
            return sender_clean.title()

        return sender_clean

    def _segment_run_together_text(self, text: str) -> str:
        """
        Segment run-together text by adding spaces between words.
        Uses a greedy algorithm with common English words.
        """
        if not text or len(text) < 5:
            return text

        # Common English words to look for (lowercase)
        # Prioritize longer words first for better matching
        common_words = [
            # Long words (7+ chars)
            'through', 'without', 'because', 'between', 'another', 'however', 'opening', 'everything',
            'something', 'anything', 'nothing', 'everyone', 'someone', 'anyone', 'opened', 'watching',
            # Medium words (4-6 chars)
            'please', 'watch', 'would', 'could', 'should', 'which', 'their', 'there', 'these',
            'those', 'about', 'after', 'where', 'while', 'being', 'until', 'again', 'never',
            'every', 'other', 'under', 'might', 'think', 'still', 'since', 'first', 'three',
            'years', 'light', 'right', 'world', 'house', 'point', 'bring', 'found', 'given',
            'asked', 'going', 'makes', 'place', 'seems', 'taken', 'knows', 'human', 'shall',
            'before', 'around', 'during', 'always', 'become', 'change', 'little', 'moment',
            'turned', 'wanted', 'people', 'looked', 'almost', 'enough', 'family', 'really',
            'within', 'others', 'myself', 'opened',
            # Short words (2-3 chars) - very common
            'the', 'for', 'and', 'you', 'that', 'with', 'have', 'this', 'will', 'your',
            'from', 'they', 'know', 'want', 'been', 'more', 'when', 'make', 'like', 'time',
            'just', 'him', 'see', 'get', 'may', 'way', 'day', 'too', 'any', 'say', 'she',
            'two', 'how', 'our', 'out', 'now', 'man', 'old', 'put', 'why', 'let', 'off',
            'did', 'got', 'new', 'set', 'who', 'yet', 'all', 'can', 'her', 'was', 'one',
            'had', 'but', 'not', 'are', 'his', 'has', 'are', 'were', 'been', 'eyes', 'eye',
            'is', 'as', 'at', 'be', 'by', 'do', 'go', 'he', 'if', 'in', 'it', 'me', 'my',
            'no', 'of', 'on', 'or', 'so', 'to', 'up', 'us', 'we',
            'test', 'best', 'rest', 'next', 'last', 'must', 'back', 'take', 'give', 'keep',
            'both', 'each', 'even', 'ever', 'also', 'such', 'same', 'well', 'much', 'very',
            # Common OCR errors
            'eys',  # "eyes" without the 'i'
        ]

        # Convert to lowercase for matching
        text_lower = text.lower()
        result = []
        i = 0

        while i < len(text_lower):
            # Try to match the longest possible word
            matched = False

            # Try words in order (longer first)
            for word in common_words:
                word_len = len(word)
                if i + word_len <= len(text_lower):
                    if text_lower[i:i + word_len] == word:
                        # Match found - add the word with original casing
                        result.append(text[i:i + word_len])
                        i += word_len
                        matched = True
                        break

            if not matched:
                # No word matched - just add the character
                result.append(text[i])
                i += 1

        # Join with spaces, but clean up multiple spaces
        segmented = ' '.join(result)
        # Clean up: remove multiple spaces
        segmented = re.sub(r'\s+', ' ', segmented)

        return segmented.strip()

    def fix_ocr_urls(self, text: str) -> str:
        """Fix OCR-broken URLs by removing whitespace (spaces, newlines, tabs) within URL patterns"""
        if not text:
            return text

        # FIRST PASS: Fix YouTube URLs that have text merged after the video ID
        # YouTube video IDs are exactly 11 characters: alphanumeric, hyphen, underscore
        # Pattern: https://www.youtube.com/watch?v=XXXXXXXXXXX<merged_text>
        youtube_pattern = r'(https?://(?:www\.)?youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})([a-z]{5,})'

        max_iterations = 10
        for _ in range(max_iterations):
            match = re.search(youtube_pattern, text, re.IGNORECASE)
            if not match:
                break

            # Keep only the URL part (protocol + domain + video ID)
            # The third group is merged text that should be separated
            url_part = match.group(1) + match.group(2)
            merged_text = match.group(3)

            # Replace the broken URL with just the clean URL, followed by space and the text
            # Add spaces back into the run-together text
            broken = match.group(0)

            # Segment the run-together text by adding spaces
            segmented_text = self._segment_run_together_text(merged_text)

            fixed = url_part + ' ' + segmented_text
            text = text.replace(broken, fixed, 1)

        # SECOND PASS: Fix complete URLs from http(s):// to common file extensions
        # This handles cases like "https://example.com/20 1 9/file .html" where digits have spaces
        # Also handles "https ://www. cnbc. com" where OCR added spaces in the protocol/domain
        # Common web file extensions
        extensions = r'(?:\.html|\.htm|\.php|\.asp|\.aspx|\.jsp|\.pdf|\.jpg|\.jpeg|\.png|\.gif|\.css|\.js)'

        # Find all URLs that start with http(s):// (with possible spaces) and end with a file extension
        # Pattern allows optional spaces after http/https, around :, and around //
        # This catches URLs like "https ://www. cnbc. com/path .html"
        complete_url_pattern = r'https?\s*:\s*//\s*[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'\(\)*+,;=%\s]+?' + extensions

        max_iterations = 20
        for _ in range(max_iterations):
            match = re.search(complete_url_pattern, text, re.IGNORECASE)
            if not match:
                break

            # Remove ALL whitespace from the matched URL
            broken_url = match.group(0)
            fixed_url = re.sub(r'\s+', '', broken_url)
            text = text.replace(broken_url, fixed_url, 1)

        # THIRD PASS: Fix URLs that end with long alphanumeric IDs (article IDs, resource IDs, etc.)
        # This handles cases like HuffPost URLs: "...us- removal us 5bedf361e4b0510a1f2f16e9"
        # Many modern URLs don't have file extensions but end with IDs
        # Pattern: http(s):// followed by URL chars (including spaces) ending with a long alphanumeric ID
        # Stop before newlines or disclaimer text like "Please note"
        article_url_pattern = r'https?\s*:\s*//\s*[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'\(\)*+,;=%\s]+?[a-z0-9]{12,}(?=\s*\n|\s*$|\s+Please)'

        for _ in range(max_iterations):
            match = re.search(article_url_pattern, text, re.IGNORECASE)
            if not match:
                break

            # Remove ALL whitespace from the matched URL
            broken_url = match.group(0)
            fixed_url = re.sub(r'\s+', '', broken_url)
            text = text.replace(broken_url, fixed_url, 1)

        # PASS 3.5: Fix article URLs ending with path segments/slugs (no file extension)
        # This handles news article URLs like: "https://www.washingtontimes.com/news/20 1 7/dec/ 1 0/article-slug/"
        # Pattern: http(s):// followed by URL chars ending with a slug (word characters and hyphens) and optional trailing slash
        # The slug should be at least 3 chars and can contain hyphens
        # Stop at end of line, newline, or before "Please" (disclaimer start)
        article_slug_pattern = r'https?\s*:\s*//\s*[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'\(\)*+,;=%\s]+?[a-z][\w\-]{2,}/?(?=\s*\n|\s*$|\s+Please|\s+$)'

        for _ in range(max_iterations):
            match = re.search(article_slug_pattern, text, re.IGNORECASE)
            if not match:
                break

            # Remove ALL whitespace from the matched URL
            broken_url = match.group(0)
            fixed_url = re.sub(r'\s+', '', broken_url)
            text = text.replace(broken_url, fixed_url, 1)

        # FOURTH PASS: Fix URLs broken in the middle (original logic)
        # This handles cases where the URL doesn't end with an extension or ID
        for _ in range(max_iterations):
            # Pattern to find URLs that are broken by whitespace in the middle
            # Key: the continuation must look like a URL part, not regular text
            # Match URL + whitespace + URL-like continuation (contains /, -, _, . or starts with these)
            # This prevents matching regular text like "please note" after a URL
            match = re.search(
                r'(https?://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'\(\)*+,;=%]+)'  # URL start
                r'(\s+)'  # Whitespace (the break)
                r'([a-zA-Z0-9\-\._~:/?#\[\]@!$&\'\(\)*+,;=%]*[/\-_.=?&#][a-zA-Z0-9\-\._~:/?#\[\]@!$&\'\(\)*+,;=%]+)',  # URL continuation (must contain URL-specific chars)
                text
            )

            if not match:
                break

            # Remove ALL whitespace (spaces, newlines, tabs, carriage returns) from this match
            broken_url = match.group(0)
            fixed_url = broken_url.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
            text = text.replace(broken_url, fixed_url, 1)

        return text

    def extract_disclaimer(self, body: str) -> tuple:
        """
        Extract Epstein's standard disclaimer from body, return (clean_body, disclaimer)

        When a disclaimer is detected (even with OCR errors), it's replaced with the
        canonical/correct version for consistency.
        """
        if not body:
            return body, None

        # The canonical, correct disclaimer text
        CANONICAL_DISCLAIMER = """Please note: The information contained in this communication is confidential, may be attorney-client privileged, may constitute inside information, and is intended only for the use of the addressee. It is the property of JEE. Unauthorized use, disclosure or copying of this communication or any part thereof is strictly prohibited and may be unlawful. If you have received this communication in error, please notify us immediately by return e-mail or by e-mail to jeevacation@gmail.com, and destroy this communication and all copies thereof, including all attachments."""

        # Patterns to DETECT a disclaimer (any variation, including OCR errors)
        # Once detected, the entire disclaimer is removed and replaced with canonical version
        # Ordered from most specific to least specific - DO NOT modify existing patterns, only add new ones
        disclaimer_detection_patterns = [
            # === COMPLETE DISCLAIMERS (most specific, check first) ===

            # Standard "please note" disclaimer - capture through end markers and any remaining disclaimer text
            r'(?:^|\n)\s*please\s*note[\s\S]+?(?:copyright[\s\-]*all rights reserved|all rights reserved)',

            # OCR error: "pleasenote" run together - capture through complete ending
            r'pleasenote[A-Za-z\s]*information[A-Za-z\s]*contain[A-Za-z\s]*communication[A-Za-z\s]*confidential[\s\S]+?(?:copyright[\s\-]*all rights reserved|all rights reserved)',

            # "please note" followed by "The information contained" - captures both
            r'(?:^|\n)\s*please\s*note\s*\n\s*The information contained in this communication[\s\S]+?(?:strictly prohibited[\s\S]{0,200}|jeevacation@gmail\.com[\s\S]{0,200}|copyright[\s\-]*all rights reserved)',

            # === TRUNCATED DISCLAIMERS (ordered from most specific to least specific) ===

            # Truncated - longer version that goes through "property of" (e.g., HOUSE_OVERSIGHT_032737)
            r'(?:^|\n)\s*please\s*note\s*[\n\s]*The information contained in this communication[\s\S]+?property of[\s\S]{0,50}?(?=\n\s*\n|$)',

            # Truncated - medium length that goes through "addressee" but not "property of"
            r'(?:^|\n)\s*please\s*note\s*[\n\s]*The information contained in this communication[\s\S]+?addressee[\s\S]{0,100}?(?=\n\s*\n|$)',

            # Truncated - very short version ending soon after "confidential"/"privileged" (e.g., HOUSE_OVERSIGHT_030799)
            # This catches disclaimers cut off early like "...confidential, may be attorney-client privileged, may"
            r'(?:^|\n)\s*please\s*note\s*[\n\s]*The information contained in this communication is\s*confidential[\s\S]{0,150}?(?=\n\s*\n|$)',

            # Truncated - extremely short, just "please note" with optional whitespace or "wrote:" after (e.g., HOUSE_OVERSIGHT_025200)
            # Catches cases like "that will be fun\nplease note" or "please note\nwrote:"
            r'(?:^|\n)\s*please\s*note\s*(?:wrote:)?\s*(?=\n|$)',

            # === OTHER VARIATIONS ===

            # Starts directly with "The information contained" (shorter version, no "please note")
            r'(?:^|\n)\s*The information contained in this communication[\s\S]+?(?:strictly prohibited[\s\S]{0,200}|jeevacation@gmail\.com[\s\S]{0,200})(?:\n\n|$)',
        ]

        disclaimer = None
        clean_body = body

        # Keep removing disclaimers until none are found (handles multiple disclaimers in one email)
        while True:
            found = False
            for pattern in disclaimer_detection_patterns:
                match = re.search(pattern, clean_body, re.IGNORECASE | re.DOTALL)
                if match:
                    # Found a disclaimer - replace it with the canonical version
                    disclaimer = CANONICAL_DISCLAIMER
                    clean_body = clean_body[:match.start()] + clean_body[match.end():]
                    clean_body = clean_body.strip()
                    found = True
                    break  # Start over with all patterns on the new clean_body

            if not found:
                break  # No more disclaimers found

        return clean_body, disclaimer

    def strip_quoted_content(self, body: str) -> str:
        """Strip quoted/forwarded content from email body to show only new content"""
        if not body:
            return body

        # Patterns that indicate quoted/forwarded content starts
        quote_patterns = [
            # Gmail-style quotes: "On [date] at [time], [name] wrote:"
            r'(?:^|\n)On\s+[A-Z][a-z]{2},\s+[A-Z][a-z]{2,}\s+\d{1,2},\s+\d{4}\s+at\s+[\d:]+\s+[AP]M',
            # Formal forward headers: "From: ... Sent: ... To: ... Subject:"
            r'(?:^|\n)From:\s*.+?\s*\n\s*Sent:\s*.+?\s*\n\s*To:',
            # Another common format: "-----Original Message-----"
            r'(?:^|\n)-+\s*Original Message\s*-+',
            # Inline forward: "> wrote:" or "< wrote:"
            r'(?:^|\n)[<>]\s*wrote:',
            # "wrote:" artifact at start of line (may have text before/after it)
            # Matches patterns like "wrote:", "wrote: text", "Name wrote:", "Subject: Re: ... wrote:"
            r'(?:^|\n)\s*(?:.*?:)?\s*wrote:',
        ]

        # Find the earliest occurrence of any quote pattern
        earliest_pos = len(body)
        for pattern in quote_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                earliest_pos = min(earliest_pos, match.start())

        # Truncate at the quote start
        if earliest_pos < len(body):
            body = body[:earliest_pos].strip()

        # Also strip common email signatures that don't add value
        signature_patterns = [
            r'(?:^|\n)Sent from my BlackBerry.*',
            r'(?:^|\n)Sent from my iPhone.*',
            r'(?:^|\n)Sent from my iPad.*',
            r'(?:^|\n)Get Outlook for.*',
            r'(?:^|\n)Sent from Yahoo Mail.*',
        ]

        for pattern in signature_patterns:
            body = re.sub(pattern, '', body, flags=re.IGNORECASE | re.DOTALL)

        return body.strip()

    def deduplicate_senders(self):
        """Post-process emails to deduplicate sender variations"""
        # Build alias map from emails with both name and email
        for email in self.emails:
            if email.get("from_name") and email.get("from"):
                name_lower = email["from_name"].lower().strip()
                if '@' in email["from"]:
                    # Map name to email (case-insensitive)
                    self.sender_aliases[name_lower] = email["from"]

        # Apply canonicalization
        for email in self.emails:
            email["from"] = self.canonicalize_sender(email["from"])
            email["to"] = self.canonicalize_sender(email["to"]) if email.get("to") else email.get("to")

            # Also canonicalize all recipients in to_list and cc_list
            if email.get("to_list"):
                email["to_list"] = [self.canonicalize_sender(r) for r in email["to_list"]]

            if email.get("cc_list"):
                email["cc_list"] = [self.canonicalize_sender(r) for r in email["cc_list"]]

            # Update Epstein flags after canonicalization (check both to_list and cc_list)
            all_recipients = email.get("to_list", []) + email.get("cc_list", [])
            email["is_epstein_sender"] = self.is_epstein_email(email["from"]) or self.is_epstein_name(email.get("from", ""))
            email["is_epstein_recipient"] = (
                self.is_epstein_email(email["to"]) or
                self.is_epstein_name(email.get("to", "")) or
                any(self.is_epstein_email(r) or self.is_epstein_name(r) for r in all_recipients)
            )

            # Update associate flags after canonicalization
            email["is_associate_sender"] = self.is_associate_name(email["from"]) or self.is_associate_name(email.get("from", ""))
            email["is_associate_recipient"] = (
                self.is_associate_name(email["to"]) or
                self.is_associate_name(email.get("to", "")) or
                any(self.is_associate_name(r) for r in all_recipients)
            )
            email["associate_names"] = list(set(
                self.get_associates_in_name(email["from"]) +
                self.get_associates_in_name(email.get("from", "")) +
                self.get_associates_in_name(email["to"]) +
                self.get_associates_in_name(email.get("to", "")) +
                [assoc for r in all_recipients for assoc in self.get_associates_in_name(r)]
            ))

            # Recalculate is_irrelevant flag
            email["is_irrelevant"] = self.is_irrelevant_email(email)

            # IMPORTANT: If Epstein is sending to himself, mark as "Unknown Recipient"
            # (Epstein shouldn't appear as his own recipient)
            if email["is_epstein_sender"] and email["is_epstein_recipient"]:
                email["to"] = "Unknown Recipient"
                email["to_list"] = ["Unknown Recipient"]
                email["cc_list"] = []
                email["is_epstein_recipient"] = False

    def get_statistics(self) -> Dict:
        """Get parsing statistics"""
        epstein_sent = sum(1 for e in self.emails if e["is_epstein_sender"])
        epstein_received = sum(1 for e in self.emails if e["is_epstein_recipient"])

        # Count unique senders and recipients
        senders = {}
        recipients = {}

        for email in self.emails:
            if email["from"]:
                senders[email["from"]] = senders.get(email["from"], 0) + 1

            # Count all recipients from to_list (not just primary 'to')
            if email.get("to_list"):
                for recipient in email["to_list"]:
                    if recipient and recipient != "Unknown Recipient":
                        recipients[recipient] = recipients.get(recipient, 0) + 1
            elif email["to"]:
                # Fallback if to_list is not available
                recipients[email["to"]] = recipients.get(email["to"], 0) + 1

        # Get date range
        dates = [e["timestamp"] for e in self.emails if e["timestamp"] > 0]
        date_range = None
        if dates:
            min_date = datetime.fromtimestamp(min(dates))
            max_date = datetime.fromtimestamp(max(dates))
            date_range = {
                "earliest": min_date.strftime("%Y-%m-%d"),
                "latest": max_date.strftime("%Y-%m-%d")
            }

        return {
            **self.stats,
            "epstein_sent": epstein_sent,
            "epstein_received": epstein_received,
            "unique_senders": len(senders),
            "unique_recipients": len(recipients),
            "sender_counts": dict(sorted(senders.items(), key=lambda x: x[1], reverse=True)),
            "recipient_counts": dict(sorted(recipients.items(), key=lambda x: x[1], reverse=True)),
            "date_range": date_range
        }

    def save_to_json(self, output_path: str):
        """Save emails to JSON file"""
        data = {
            "emails": self.emails,
            "statistics": self.get_statistics(),
            "generated_at": datetime.now().isoformat()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(self.emails)} emails to {output_path}")
