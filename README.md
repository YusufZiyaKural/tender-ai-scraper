# tender-ai-scraper
Automated Python tool that leverages LLMs to parse unstructured tender documents into clean JSON/Excel formats.



## Features

* **Smart Data Extraction:** Uses `undetected_chromedriver` and `BeautifulSoup` to bypass simple bot protections and scrape data seamlessly.
* **AI Integration:** Integrates `google-genai` (Gemini 2.5 Flash) to analyze raw tender texts and intelligently extract key metrics like categories, institutions, prices, and stakeholders.
* **Consortium Handling:** Automatically detects joint ventures/consortiums and splits them into individual stakeholder records for accurate data analysis.
* **Checkpoint System:** The script saves progress to a local JSON file (`veri_yedek.json`) after each successful AI parsing. If the script crashes or rate limits are hit, it resumes exactly where it left off.
* **Excel Export:** Automatically exports the final structured dataset into a clean `.xlsx` file using `pandas`.
* **Resilience:** Implements exponential backoff to handle temporary AI API timeouts or network interruptions gracefully.



## Tech Stack

* **Language:** Python 3.x
* **Automation & Scraping:** `undetected_chromedriver`, `selenium`, `beautifulsoup4`
* **AI & Parsing:** `google-genai`
* **Data Manipulation:** `pandas`, `json`



## Setup & Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/tender-data-scraper.git](https://github.com/yourusername/tender-data-scraper.git)
   cd tender-data-scraper


2. Install the required dependencies:
```bash
pip install undetected-chromedriver selenium beautifulsoup4 pandas google-genai openpyxl

```


3. Set up your Google Gemini API Key:
* Open the script and locate the `api_key` parameter.
* Replace it with your actual API key (or configure it via environment variables).



## Usage

Run the script from your terminal:

```bash
python genAI_3_checkpoint.py

```

1. The script will launch a Chrome browser.
2. It will pause and ask you to log in to the target website manually.
3. Once logged in, press `ENTER` in the terminal to begin the scraping process.
4."Upon pressing ENTER, the console will provide real-time updates as the system navigates through target categories, extracts source links, processes unstructured text via Gemini AI, and serializes the structured data into Excel format.



## Disclaimer

This script is developed for educational and personal data structuring purposes. Please ensure you comply with the target website's Terms of Service and local data scraping regulations before using this automation.
