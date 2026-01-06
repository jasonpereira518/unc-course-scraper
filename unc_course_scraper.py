#!/usr/bin/env python3
"""
UNC Course Availability Scraper
Continuously monitors JAPN 162 course availability every 5 minutes
"""

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import platform
import subprocess


class UNCCourseScraper:
    def __init__(self, course_subject="JAPN", course_number="162", term="2026 Spring"):
        self.base_url = "https://reports.unc.edu/class-search/advanced_search/"
        self.course_subject = course_subject
        self.course_number = course_number
        self.term = term
        self.driver = None
        self.last_availability_status = {}  # Track last known status to avoid repeated alerts
        
    def log(self, message, level="INFO"):
        """Print timestamped log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def play_alert_sound(self):
        """Play a system alert sound to notify user of course availability"""
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                # Use macOS built-in system sound
                os.system('afplay /System/Library/Sounds/Glass.aiff')
                self.log("🔔 Alert sound played!", "ALERT")
            elif system == "Linux":
                # Try to use beep or speaker-test
                try:
                    os.system('beep -f 1000 -l 500 2>/dev/null || speaker-test -t sine -f 1000 -l 1 2>/dev/null || echo -e "\a"')
                    self.log("🔔 Alert sound played!", "ALERT")
                except:
                    # Fallback to terminal bell
                    print("\a")
                    self.log("🔔 Alert sound played (terminal bell)!", "ALERT")
            elif system == "Windows":
                # Use Windows beep
                import winsound
                winsound.Beep(1000, 500)  # 1000 Hz for 500 ms
                self.log("🔔 Alert sound played!", "ALERT")
            else:
                # Fallback to terminal bell
                print("\a")
                self.log("🔔 Alert sound played (terminal bell)!", "ALERT")
        except Exception as e:
            self.log(f"Could not play alert sound: {e}. Using terminal bell instead.", "WARNING")
            print("\a")  # Terminal bell as fallback
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with appropriate options"""
        self.log("Initializing Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.log("Chrome WebDriver initialized successfully", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"ERROR: Failed to set up Chrome driver: {e}", "ERROR")
            self.log("Make sure ChromeDriver is installed and in your PATH", "ERROR")
            import traceback
            self.log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
            return False
    
    def search_course(self):
        """Navigate to the advanced search page and search for the course"""
        try:
            # Navigate to the advanced search page
            self.log(f"Navigating to {self.base_url}...")
            self.driver.get(self.base_url)
            self.log("Page loaded, waiting for elements...")
            
            # Wait for the page to load
            wait = WebDriverWait(self.driver, 15)
            
            # Find and fill in the "Subjects, Catalog Numbers, Sections" field
            # Try multiple selectors to find the subject field
            self.log("Searching for subject field...")
            subject_field = None
            selectors = [
                (By.NAME, "subject"),
                (By.ID, "id_subject"),
                (By.CSS_SELECTOR, "input[type='text'][name*='subject'], input[type='text'][id*='subject']"),
                (By.XPATH, "//input[contains(@placeholder, 'Subject') or contains(@label, 'Subject')]"),
                (By.XPATH, "//label[contains(text(), 'Subjects')]/following-sibling::input"),
            ]
            
            for by, selector in selectors:
                try:
                    subject_field = wait.until(EC.presence_of_element_located((by, selector)))
                    self.log(f"Found subject field using selector: {selector}")
                    break
                except Exception as e:
                    continue
            
            if not subject_field:
                # Last resort: find any text input that might be the subject field
                self.log("Trying fallback: searching for any text input...")
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                if inputs:
                    subject_field = inputs[0]  # Assume first text input is subject field
                    self.log("Using first text input as subject field")
            
            if subject_field:
                self.log(f"Filling subject field with: {self.course_subject} {self.course_number}")
                subject_field.clear()
                subject_field.send_keys(f"{self.course_subject} {self.course_number}")
                self.log("Subject field filled successfully")
            else:
                self.log("ERROR: Could not find subject field", "ERROR")
                return False
            
            # Find and select the term dropdown/input
            self.log(f"Searching for term field (looking for: {self.term})...")
            term_element = None
            term_selectors = [
                (By.NAME, "term"),
                (By.ID, "id_term"),
                (By.CSS_SELECTOR, "select[name*='term'], input[name*='term']"),
                (By.XPATH, "//label[contains(text(), 'Term')]/following-sibling::select | //label[contains(text(), 'Term')]/following-sibling::input"),
            ]
            
            for by, selector in term_selectors:
                try:
                    term_element = self.driver.find_element(by, selector)
                    self.log(f"Found term field using selector: {selector}")
                    break
                except Exception as e:
                    continue
            
            if term_element:
                if term_element.tag_name == "select":
                    from selenium.webdriver.support.ui import Select
                    select = Select(term_element)
                    # Try to select by visible text or partial text
                    try:
                        select.select_by_visible_text(self.term)
                        self.log(f"Selected term: {self.term}")
                    except Exception as e:
                        # Try selecting by partial match
                        self.log(f"Exact match failed, trying partial match...")
                        options = select.options
                        for option in options:
                            if self.term in option.text:
                                select.select_by_visible_text(option.text)
                                self.log(f"Selected term: {option.text}")
                                break
                else:
                    self.log(f"Filling term field with: {self.term}")
                    term_element.clear()
                    term_element.send_keys(self.term)
                    self.log("Term field filled successfully")
            else:
                self.log("WARNING: Could not find term field, proceeding without it", "WARNING")
            
            # Submit the form
            self.log("Submitting search form...")
            submitted = False
            submit_selectors = [
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Search')]"),
                (By.XPATH, "//input[@value='Search']"),
            ]
            
            for by, selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(by, selector)
                    submit_button.click()
                    submitted = True
                    self.log("Form submitted using submit button")
                    break
                except Exception as e:
                    continue
            
            if not submitted:
                # Try pressing Enter on the subject field
                self.log("Submit button not found, trying Enter key...")
                from selenium.webdriver.common.keys import Keys
                subject_field.send_keys(Keys.RETURN)
                self.log("Form submitted using Enter key")
            
            # Wait for results to load - look for the results table
            self.log("Waiting for search results to load...")
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                self.log("Results table found")
                time.sleep(2)  # Additional wait for dynamic content
            except TimeoutException:
                # Results might still be loading or no results found
                self.log("WARNING: Timeout waiting for table, waiting additional 3 seconds...", "WARNING")
                time.sleep(3)
            
            self.log("Search completed successfully", "SUCCESS")
            return True
            
        except TimeoutException as e:
            self.log(f"ERROR: Timeout waiting for page elements to load: {e}", "ERROR")
            import traceback
            self.log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
            return False
        except Exception as e:
            self.log(f"ERROR: Exception during search: {e}", "ERROR")
            import traceback
            self.log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
            return False
    
    def parse_results(self):
        """Parse the search results and extract course availability information"""
        try:
            self.log("Parsing search results...")
            # Get the page source after search
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')  # Using built-in parser instead of lxml
            self.log("Page source retrieved and parsed")
            
            # Find the results table - try multiple approaches
            self.log("Searching for results table...")
            table = None
            tables = soup.find_all('table')
            self.log(f"Found {len(tables)} table(s) on page")
            
            for t in tables:
                # Look for table with headers that match course search results
                headers = t.find_all(['th', 'td'])
                header_text = ' '.join([h.get_text(strip=True) for h in headers[:5]])
                if 'Subject' in header_text or 'Catalog' in header_text or 'Section' in header_text:
                    table = t
                    self.log("Found matching results table")
                    break
            
            if not table and tables:
                # Use the first table if no specific match
                table = tables[0]
                self.log("Using first table as results table")
            
            if not table:
                # Try using Selenium to find table directly
                self.log("Trying Selenium to find table...")
                try:
                    selenium_table = self.driver.find_element(By.TAG_NAME, "table")
                    if selenium_table:
                        # Get fresh HTML from Selenium
                        page_source = self.driver.page_source
                        soup = BeautifulSoup(page_source, 'html.parser')
                        table = soup.find('table')
                        self.log("Found table using Selenium")
                except Exception as e:
                    self.log(f"Could not find table with Selenium: {e}", "WARNING")
            
            if not table:
                self.log("ERROR: No results table found", "ERROR")
                # Debug: save page source
                try:
                    with open('debug_page.html', 'w', encoding='utf-8') as f:
                        f.write(page_source)
                    self.log("Saved page source to debug_page.html for inspection", "INFO")
                except Exception as e:
                    self.log(f"Could not save debug file: {e}", "ERROR")
                return []
            
            courses = []
            
            # Find header row to determine column indices
            self.log("Analyzing table structure...")
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                self.log(f"Found {len(headers)} columns: {', '.join(headers[:5])}...")
                # Map headers to indices
                col_indices = {}
                for i, header in enumerate(headers):
                    header_lower = header.lower()
                    if 'subject' in header_lower:
                        col_indices['subject'] = i
                    elif 'catalog' in header_lower:
                        col_indices['catalog'] = i
                    elif 'section' in header_lower and 'class' in header_lower:
                        col_indices['section'] = i
                    elif 'class' in header_lower and 'number' in header_lower:
                        col_indices['class_number'] = i
                    elif 'description' in header_lower:
                        col_indices['description'] = i
                    elif 'term' in header_lower:
                        col_indices['term'] = i
                    elif 'hours' in header_lower:
                        col_indices['hours'] = i
                    elif 'meeting' in header_lower and 'date' in header_lower:
                        col_indices['meeting_dates'] = i
                    elif 'schedule' in header_lower:
                        col_indices['schedule'] = i
                    elif 'room' in header_lower:
                        col_indices['room'] = i
                    elif 'instruction' in header_lower:
                        col_indices['instruction_type'] = i
                    elif 'instructor' in header_lower:
                        col_indices['instructor'] = i
                    elif 'available' in header_lower and 'seat' in header_lower:
                        col_indices['available_seats'] = i
            
            # Find all data rows (skip header)
            rows = table.find_all('tr')[1:] if table.find('tr') else []
            self.log(f"Found {len(rows)} data row(s) to process")
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 5:  # Need at least some columns
                    continue
                
                # Extract data using column indices if available, otherwise use position
                def get_cell(index, default=""):
                    if index is not None and index < len(cells):
                        return cells[index].get_text(strip=True)
                    return default
                
                subject = get_cell(col_indices.get('subject', 0))
                catalog_number = get_cell(col_indices.get('catalog', 1))
                class_section = get_cell(col_indices.get('section', 3))
                class_number = get_cell(col_indices.get('class_number', 4))
                description = get_cell(col_indices.get('description', 5))
                term = get_cell(col_indices.get('term', 6))
                hours = get_cell(col_indices.get('hours', 7))
                meeting_dates = get_cell(col_indices.get('meeting_dates', 8))
                schedule = get_cell(col_indices.get('schedule', 9))
                room = get_cell(col_indices.get('room', 10))
                instruction_type = get_cell(col_indices.get('instruction_type', 11))
                instructor = get_cell(col_indices.get('instructor', 12))
                available_seats_text = get_cell(col_indices.get('available_seats', 13))
                
                # Check if this is a JAPN 162 course
                # Subject might be empty for subsequent rows of same course
                is_target_course = False
                if subject and subject == self.course_subject:
                    if catalog_number == self.course_number:
                        is_target_course = True
                elif not subject or subject == "":
                    # Empty subject might mean it's a continuation row for same course
                    # Check if we have section number and it matches pattern
                    if class_section and class_section.isdigit():
                        is_target_course = True
                
                if is_target_course:
                    # Parse available seats
                    try:
                        available_seats = int(available_seats_text)
                    except (ValueError, TypeError):
                        available_seats = 0
                    
                    course_info = {
                        'subject': subject or self.course_subject,
                        'catalog_number': catalog_number or self.course_number,
                        'class_section': class_section,
                        'class_number': class_number,
                        'description': description,
                        'term': term,
                        'hours': hours,
                        'meeting_dates': meeting_dates,
                        'schedule': schedule,
                        'room': room,
                        'instruction_type': instruction_type,
                        'instructor': instructor,
                        'available_seats': available_seats
                    }
                    courses.append(course_info)
                    self.log(f"Found section {class_section}: {available_seats} seat(s) available")
            
            self.log(f"Parsing complete: found {len(courses)} matching course section(s)", "SUCCESS")
            return courses
            
        except Exception as e:
            self.log(f"ERROR: Exception while parsing results: {e}", "ERROR")
            import traceback
            self.log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
            return []
    
    def check_availability(self):
        """Main method to check course availability"""
        self.log("=" * 60)
        self.log("Starting availability check...")
        
        if not self.driver:
            if not self.setup_driver():
                self.log("ERROR: Failed to initialize driver", "ERROR")
                return None
        
        if not self.search_course():
            self.log("ERROR: Search failed", "ERROR")
            return None
        
        courses = self.parse_results()
        self.log(f"Availability check completed: {len(courses) if courses else 0} section(s) found")
        return courses
    
    def print_availability(self, courses):
        """Print formatted availability information"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*60}")
        print(f"Course Availability Check - {timestamp}")
        print(f"{'='*60}")
        
        if not courses:
            print(f"No sections found for {self.course_subject} {self.course_number}")
            return
        
        print(f"\nFound {len(courses)} section(s) for {self.course_subject} {self.course_number}:\n")
        
        # Check if any section has availability
        has_availability = False
        available_sections = []
        
        for course in courses:
            section = course['class_section']
            seats = course['available_seats']
            schedule = course['schedule']
            room = course['room']
            instructor = course['instructor']
            
            status = "✅ AVAILABLE" if seats > 0 else "❌ FULL"
            
            # Check if this section has availability
            section_key = f"{section}_{course['class_number']}"
            previous_seats = self.last_availability_status.get(section_key, 0)
            
            if seats > 0:
                has_availability = True
                available_sections.append(f"Section {section} ({seats} seat(s))")
                
                # Play alert whenever there's availability (1 or more seats)
                self.log(f"🎉 AVAILABILITY DETECTED! Section {section} has {seats} seat(s) available!", "ALERT")
                self.play_alert_sound()
                # Play multiple times for emphasis
                time.sleep(0.5)
                self.play_alert_sound()
                time.sleep(0.5)
                self.play_alert_sound()
                time.sleep(0.5)
                self.play_alert_sound()
                time.sleep(0.5)
                self.play_alert_sound()
                time.sleep(0.5)
                self.play_alert_sound()
                time.sleep(0.5)
                self.play_alert_sound()
                time.sleep(0.5)
                self.play_alert_sound()
                time.sleep(0.5)
                self.play_alert_sound()
            
            # Update last known status
            self.last_availability_status[section_key] = seats
            
            print(f"Section {section}:")
            print(f"  Status: {status} ({seats} seat(s) available)")
            print(f"  Schedule: {schedule}")
            print(f"  Room: {room}")
            print(f"  Instructor: {instructor}")
            print(f"  Class Number: {course['class_number']}")
            print()
        
        # Summary alert
        if has_availability:
            self.log(f"⚠️  ALERT: {len(available_sections)} section(s) have availability: {', '.join(available_sections)}", "ALERT")
        else:
            self.log("No availability found - all sections are full", "INFO")
    
    def run_continuous(self, interval_minutes=5):
        """Run the scraper continuously, checking every interval_minutes"""
        self.log("=" * 60)
        self.log(f"Starting UNC Course Scraper for {self.course_subject} {self.course_number}")
        self.log(f"Checking every {interval_minutes} minutes...")
        self.log("Press Ctrl+C to stop")
        self.log("=" * 60)
        
        check_count = 0
        try:
            while True:
                check_count += 1
                self.log(f"\n--- Check #{check_count} ---")
                
                try:
                    courses = self.check_availability()
                    if courses is not None:
                        self.print_availability(courses)
                    else:
                        self.log("ERROR: Availability check returned None", "ERROR")
                except Exception as e:
                    self.log(f"ERROR: Exception during availability check: {e}", "ERROR")
                    import traceback
                    self.log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
                
                # Wait for the specified interval with countdown
                self.log(f"\nWaiting {interval_minutes} minute(s) until next check...")
                total_seconds = interval_minutes * 60
                elapsed = 0
                
                # Show countdown updates
                while elapsed < total_seconds:
                    remaining = total_seconds - elapsed
                    
                    if remaining <= 60:
                        # Show every 10 seconds in the last minute
                        update_interval = 10
                    elif remaining <= 300:  # Last 5 minutes
                        update_interval = 30
                    else:
                        update_interval = 60  # Every minute for longer waits
                    
                    # Don't sleep longer than remaining time
                    sleep_time = min(update_interval, remaining)
                    
                    if remaining <= 60:
                        self.log(f"Next check in {remaining} second(s)...", "WAIT")
                    else:
                        minutes = remaining // 60
                        secs = remaining % 60
                        self.log(f"Next check in {minutes} minute(s) and {secs} second(s)...", "WAIT")
                    
                    time.sleep(sleep_time)
                    elapsed += sleep_time
                
                self.log("Wait period complete, starting next check...\n")
                
        except KeyboardInterrupt:
            self.log("\n\nStopping scraper (KeyboardInterrupt)...")
        except Exception as e:
            self.log(f"\n\nERROR: Unexpected exception: {e}", "ERROR")
            import traceback
            self.log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
        finally:
            if self.driver:
                self.log("Closing browser...")
                try:
                    self.driver.quit()
                    self.log("Browser closed successfully")
                except Exception as e:
                    self.log(f"Error closing browser: {e}", "ERROR")


def main():
    scraper = UNCCourseScraper(course_subject="JAPN", course_number="162", term="2026 Spring")
    scraper.run_continuous(interval_minutes=5)


if __name__ == "__main__":
    main()

