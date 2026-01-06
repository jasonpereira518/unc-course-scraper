# UNC Course Availability Scraper

A web scraper that continuously monitors the availability of JAPN 162 courses on the UNC class search website, checking every 5 minutes and printing availability status.

## Features

- Automatically searches for JAPN 162 courses
- Checks availability every 5 minutes
- Displays detailed course information including:
  - Section number
  - Available seats
  - Schedule
  - Room location
  - Instructor
- Runs continuously until stopped (Ctrl+C)

## Requirements

- Python 3.7+
- Chrome browser
- ChromeDriver (must be installed and in your PATH)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install ChromeDriver:
   - **macOS (using Homebrew):**
     ```bash
     brew install chromedriver
     ```
   - **Or download manually:**
     - Visit https://chromedriver.chromium.org/downloads
     - Download the version matching your Chrome browser
     - Add to your PATH

## Usage

Run the scraper:
```bash
python unc_course_scraper.py
```

The scraper will:
- Start checking immediately
- Print availability status every 5 minutes
- Continue running until you press Ctrl+C

## Customization

You can modify the course and term in the script:
- Edit the `main()` function to change course subject, number, or term
- Change the interval by modifying `interval_minutes` parameter

Example:
```python
scraper = UNCCourseScraper(
    course_subject="JAPN", 
    course_number="162", 
    term="2026 Spring"
)
scraper.run_continuous(interval_minutes=5)
```

## Output Example

```
Course Availability Check - 2026-01-15 10:30:00
============================================================

Found 2 section(s) for JAPN 162:

Section 001:
  Status: ❌ FULL (0 seat(s) available)
  Schedule: MW 11:15 AM-12:05 PM
  Room: Coker Hall-Rm 0201
  Instructor: Dixon, Dwayne Emil
  Class Number: 3793

Section 002:
  Status: ❌ FULL (0 seat(s) available)
  Schedule: MW 12:20 PM-01:10 PM
  Room: Hanes Art Center-Rm 0121
  Instructor: Dixon, Dwayne Emil
  Class Number: 7663
```

## Notes

- The scraper runs in headless mode (no browser window)
- Make sure you have a stable internet connection
- The website structure may change, requiring script updates

