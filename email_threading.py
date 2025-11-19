import re
from typing import Dict, List
from difflib import SequenceMatcher

class EmailThreader:
    """Create conversation threads from emails"""

    def __init__(self, emails: List[Dict]):
        self.emails = emails
        self.threads = []

    def deduplicate_emails(self, emails: List[Dict]) -> List[Dict]:
        """
        Remove duplicate emails that appear in multiple source files.
        Emails are considered duplicates if they have the same:
        - Timestamp (within 5 seconds)
        - Sender
        - Recipient
        - Body (exact match or very similar)

        For duplicates, tracks all source files where the email appeared.
        """
        seen = {}
        deduplicated = []

        for email in emails:
            # Create a signature for this email using the email's unique ID
            # This is the most precise way to identify true duplicates
            email_id = email.get("id", "")

            # Fallback to content-based key if no ID
            if not email_id:
                timestamp = email.get("timestamp", 0)
                from_addr = (email.get("from") or "").lower().strip()
                to_addr = (email.get("to") or "").lower().strip()
                subject = (email.get("subject") or "").lower().strip()
                body = (email.get("body") or "").strip()
                # Use full body and exact timestamp for precise matching
                key = (timestamp, from_addr, to_addr, subject, body)
            else:
                key = email_id

            if key not in seen:
                # First occurrence - initialize the duplicate_sources list
                email["duplicate_sources"] = [email.get("source_file", "")]
                seen[key] = email
                deduplicated.append(email)
            else:
                # Duplicate found - add this source file to the list
                existing_email = seen[key]
                source_file = email.get("source_file", "")
                if source_file and source_file not in existing_email["duplicate_sources"]:
                    existing_email["duplicate_sources"].append(source_file)

        return deduplicated

    def create_threads(self) -> List[Dict]:
        """Group emails into conversation threads"""

        # Deduplicate emails first (same message in multiple source files)
        deduplicated_emails = self.deduplicate_emails(self.emails)

        # Sort emails by timestamp
        sorted_emails = sorted(
            [e for e in deduplicated_emails if e.get("timestamp", 0) > 0],
            key=lambda x: x["timestamp"]
        )

        # Group by subject similarity and participants
        thread_groups = {}
        unthreaded = []

        for email in sorted_emails:
            thread_id = self.find_thread_match(email, thread_groups)

            if thread_id:
                thread_groups[thread_id]["emails"].append(email)
                # Update participants
                if email["from"]:
                    thread_groups[thread_id]["participants"].add(email["from"])
                if email["to"]:
                    thread_groups[thread_id]["participants"].add(email["to"])
            else:
                # Create new thread
                new_thread_id = f"thread_{len(thread_groups)}"
                participants = set()
                if email["from"]:
                    participants.add(email["from"])
                if email["to"]:
                    participants.add(email["to"])

                thread_groups[new_thread_id] = {
                    "id": new_thread_id,
                    "subject": email.get("subject", "No Subject"),
                    "emails": [email],
                    "participants": participants,
                    "start_date": email.get("date"),
                    "has_epstein": email["is_epstein_sender"] or email["is_epstein_recipient"]
                }

        # Convert to list and update metadata
        self.threads = []
        for thread_id, thread in thread_groups.items():
            thread["participants"] = list(thread["participants"])
            thread["email_count"] = len(thread["emails"])

            # Get date range
            timestamps = [e["timestamp"] for e in thread["emails"]]
            thread["first_timestamp"] = min(timestamps)
            thread["last_timestamp"] = max(timestamps)

            self.threads.append(thread)

        # Sort threads by latest email
        self.threads.sort(key=lambda t: t["last_timestamp"], reverse=True)

        return self.threads

    def find_thread_match(self, email: Dict, existing_threads: Dict) -> str:
        """Find if email matches an existing thread (enhanced algorithm)"""

        subject = email.get("subject", "")
        subject_clean = email.get("subject_clean", "")
        from_addr = email.get("from", "")
        to_addr = email.get("to", "")
        timestamp = email.get("timestamp", 0)
        reply_depth = email.get("reply_depth", 0)
        is_forward = email.get("is_forward", False)

        best_match = None
        best_score = 0

        # Use clean subject if available
        search_subject = subject_clean if subject_clean else subject

        for thread_id, thread in existing_threads.items():
            score = 0

            # Higher score for replies (Re: Re: Re:)
            if reply_depth > 0:
                score += 20

            # Check subject similarity (if both have subjects)
            if search_subject and thread["subject"]:
                normalized_subject = self.normalize_subject(search_subject)
                normalized_thread_subject = self.normalize_subject(thread["subject"])

                if normalized_subject == normalized_thread_subject:
                    score += 60  # Increased from 50
                elif normalized_subject in normalized_thread_subject or normalized_thread_subject in normalized_subject:
                    score += 35  # Increased from 30
                else:
                    # Check similarity ratio
                    similarity = SequenceMatcher(None, normalized_subject, normalized_thread_subject).ratio()
                    if similarity > 0.7:  # Increased threshold from 0.6
                        score += int(similarity * 25)

            # Check if participants match (higher weight)
            if from_addr in thread["participants"] or to_addr in thread["participants"]:
                score += 25  # Increased from 20

            # Check if it's a back-and-forth (from/to reversed) - STRONG signal
            thread_emails = thread["emails"]
            if thread_emails:
                last_email = thread_emails[-1]
                if (from_addr == last_email.get("to") and to_addr == last_email.get("from")):
                    score += 50  # Increased from 40

                # Check if reply_depth is sequential
                last_reply_depth = last_email.get("reply_depth", 0)
                if reply_depth == last_reply_depth + 1:
                    score += 15

            # Check timestamp proximity (within 30 days, not just 7)
            if thread_emails and timestamp > 0:
                last_timestamp = thread_emails[-1].get("timestamp", 0)
                if last_timestamp > 0:
                    time_diff_days = abs(timestamp - last_timestamp) / 86400
                    if time_diff_days < 1:
                        score += 15  # Very recent
                    elif time_diff_days < 7:
                        score += 10
                    elif time_diff_days < 30:
                        score += 5

            # Penalty for forwards (less likely to be in same thread)
            if is_forward:
                score -= 10

            # Track best match
            if score > best_score:
                best_score = score
                best_match = thread_id

        # Require minimum score to match (increased from 40)
        if best_score >= 50:
            return best_match

        return None

    def normalize_subject(self, subject: str) -> str:
        """Normalize subject line for comparison"""
        if not subject:
            return ""

        # Convert to lowercase
        s = subject.lower()

        # Remove Re:, Fwd:, etc.
        s = re.sub(r'^(re|fwd|fw):\s*', '', s)
        s = re.sub(r'\s+', ' ', s)

        return s.strip()

    def get_epstein_threads(self) -> List[Dict]:
        """Get only threads involving Epstein"""
        return [t for t in self.threads if t["has_epstein"]]

    def get_thread_by_participant(self, email_address: str) -> List[Dict]:
        """Get threads involving a specific participant"""
        return [t for t in self.threads if email_address in t["participants"]]
