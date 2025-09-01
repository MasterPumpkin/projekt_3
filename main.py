"""
main.py: třetí projekt do Engeto Online Python Akademie

author: Josef Nuhlíček
email: josef.nuhlicek@gmail.com
"""

"""Election data scraper for Czech Parliamentary Elections 2017.

This script scrapes election results from volby.cz for a specified territorial unit.
It downloads municipality data, extracts voter statistics and party results,
then exports all data to a CSV file for analysis.
"""

import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import pandas as pd

# HTML parsing constants
HTML_PARSER = 'lxml'

# CSS selectors for scraping
MAIN_TABLE_SELECTOR = 'table.table tr'
MUNICIPALITY_CODE_SELECTOR = 'td.cislo a'
MUNICIPALITY_NAME_SELECTOR = 'td.overflow_name'
REGISTERED_VOTERS_SELECTOR = 'td[headers="sa2"]'
ENVELOPES_SELECTOR = 'td[headers="sa3"]'
VALID_VOTES_SELECTOR = 'td[headers="sa6"]'
PARTY_RESULTS_CONTAINER_SELECTOR = 'div.t2_470'

# Text processing constants
NON_BREAKING_SPACE = '\xa0'
REGULAR_SPACE = ' '
INVALID_PARTY_NAME = "-"

# Table structure constants
HEADER_ROW_INDEX = 1  # Skip first row (header) when processing table rows
MIN_CELLS_PER_ROW = 3  # Minimum cells needed: party number, name, votes
PARTY_NUMBER_CELL_INDEX = 0
PARTY_NAME_CELL_INDEX = 1
PARTY_VOTES_CELL_INDEX = 2

# CSV column names
CODE_COLUMN = 'code'
LOCATION_COLUMN = 'location'
REGISTERED_COLUMN = 'registered'
ENVELOPES_COLUMN = 'envelopes'
VALID_COLUMN = 'valid'
PARTY_NAME_KEY = 'nazev'
PARTY_VOTES_KEY = 'hlasy'

# Default values
DEFAULT_VOTES = 0
DEFAULT_VALUE = 'N/A'

# File encoding
CSV_ENCODING = 'utf-8'

# Progress bar settings
PROGRESS_DESC = "Zpracovávám obce"
PROGRESS_UNIT = "obec"


def get_soup_from_url(url: str) -> BeautifulSoup | None:
    """Downloads a URL and returns a BeautifulSoup object. Returns None on error.

    Args:
        url (str): The URL to download and parse.

    Returns:
        BeautifulSoup | None: Parsed BeautifulSoup object or None if error occurs.

    Example:
        >>> soup = get_soup_from_url("https://example.com")
        >>> if soup:
        ...     print("Successfully parsed HTML")
    """
    try:
        # Download the webpage
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse HTML content
        soup = BeautifulSoup(response.text, HTML_PARSER)
        return soup

    except requests.exceptions.RequestException as error:
        print(f"  -> CHYBA: Nepodařilo se stáhnout stránku: {error}")
        return None


def clean_number(text: str) -> int:
    """Safely converts text to integer, removing regular and non-breaking spaces.

    Args:
        text (str): Text string containing a number with possible spaces.

    Returns:
        int: Cleaned integer value, returns 0 if conversion fails.

    Example:
        >>> clean_number("1 234")
        1234
        >>> clean_number("5\xa0678")
        5678
        >>> clean_number("invalid")
        0
    """
    # Check if text is empty or None
    if not text:
        return DEFAULT_VOTES

    try:
        # Remove all types of spaces and convert to integer
        cleaned_text = text.replace(
            NON_BREAKING_SPACE, '').replace(REGULAR_SPACE, '')
        number = int(cleaned_text)
        return number

    except (ValueError, TypeError):
        # Return 0 if conversion fails
        return DEFAULT_VOTES


def scrape_municipalities_list(main_page_soup: BeautifulSoup, base_url: str) -> list:
    """Extracts list of municipalities with their codes, names and detail links from main page.

    Args:
        main_page_soup (BeautifulSoup): Parsed HTML of the main election results page.
        base_url (str): Base URL for constructing absolute links to municipality details.

    Returns:
        list: List of dictionaries containing municipality data with keys:
            - code (str): Municipality code
            - location (str): Municipality name
            - link (str): Full URL to municipality detail page

    Example:
        >>> soup = BeautifulSoup(html_content, 'lxml')
        >>> municipalities = scrape_municipalities_list(soup, "https://volby.cz")
        >>> print(f"Found {len(municipalities)} municipalities")
    """
    municipalities = []  # List to store municipality data

    # Find all table rows in the main table
    table_rows = main_page_soup.select(MAIN_TABLE_SELECTOR)

    # Process each row to extract municipality information
    for row in table_rows:
        # Find the link element (contains municipality code)
        link_element = row.select_one(MUNICIPALITY_CODE_SELECTOR)
        # Find the name element (contains municipality name)
        name_element = row.select_one(MUNICIPALITY_NAME_SELECTOR)

        # Check if both elements exist
        if link_element and name_element:
            # Extract data from elements
            href = link_element.get('href')
            code = link_element.get_text(strip=True)
            name = name_element.get_text(strip=True)

            # Check if all required data is present
            if href and code and name:
                # Create full URL for municipality detail page
                full_link = urljoin(base_url, href)

                # Add municipality data to list
                municipality_data = {
                    CODE_COLUMN: code,
                    LOCATION_COLUMN: name,
                    'link': full_link
                }
                municipalities.append(municipality_data)

    print(f"Nalezeno {len(municipalities)} obcí ke zpracování.")
    return municipalities


def scrape_one_place_details(detail_soup: BeautifulSoup) -> dict | None:
    """Extracts election data and political party results from municipality detail page.

    Args:
        detail_soup (BeautifulSoup): Parsed HTML of municipality detail page.

    Returns:
        dict | None: Dictionary containing election data with keys:
            - registered (int): Number of registered voters
            - envelopes (int): Number of envelopes received
            - valid (int): Number of valid votes
            - parties (dict): Dictionary of party results with party numbers as keys
        Returns None if soup is invalid.

    Example:
        >>> soup = BeautifulSoup(detail_html, 'lxml')
        >>> data = scrape_one_place_details(soup)
        >>> if data:
        ...     print(f"Registered voters: {data['registered']}")
        ...     print(f"Parties found: {len(data['parties'])}")
    """
    # Check if soup is valid
    if not detail_soup:
        return None

    # Find elements containing election summary data
    registered_element = detail_soup.select_one(REGISTERED_VOTERS_SELECTOR)
    envelopes_element = detail_soup.select_one(ENVELOPES_SELECTOR)
    valid_votes_element = detail_soup.select_one(VALID_VOTES_SELECTOR)

    # Create dictionary to store election data
    election_data = {
        REGISTERED_COLUMN: clean_number(registered_element.get_text()) if registered_element else DEFAULT_VOTES,
        ENVELOPES_COLUMN: clean_number(envelopes_element.get_text()) if envelopes_element else DEFAULT_VOTES,
        VALID_COLUMN: clean_number(valid_votes_element.get_text()) if valid_votes_element else DEFAULT_VOTES,
        'parties': {}
    }

    # Find all tables containing party results
    result_tables = detail_soup.select(PARTY_RESULTS_CONTAINER_SELECTOR)

    # Process each table
    for table_container in result_tables:
        table = table_container.find('table')
        if not table:
            continue  # Skip if no table found

        # Process each row in the table (skip header row)
        # Skip first row (header)
        table_rows = table.find_all('tr')[HEADER_ROW_INDEX:]

        for row in table_rows:
            cells = row.find_all('td')

            # Check if row has enough cells (party number, name, votes)
            if len(cells) >= MIN_CELLS_PER_ROW:
                party_number = cells[PARTY_NUMBER_CELL_INDEX].get_text(
                    strip=True)
                party_name = cells[PARTY_NAME_CELL_INDEX].get_text(strip=True)
                votes_text = cells[PARTY_VOTES_CELL_INDEX].get_text(strip=True)
                votes = clean_number(votes_text)

                # Add party data if name is valid
                if party_name and party_name != INVALID_PARTY_NAME:
                    election_data['parties'][party_number] = {
                        PARTY_NAME_KEY: party_name,
                        PARTY_VOTES_KEY: votes
                    }

    return election_data


def export_to_csv(municipalities_data: list, output_filename: str):
    """Exports final election data to a flat CSV file using Pandas.

    Args:
        municipalities_data (list): List of dictionaries containing municipality election data.
        output_filename (str): Output CSV filename including extension.

    Raises:
        IOError: If file cannot be written to disk.

    Example:
        >>> municipality_data = [{'code': '123', 'location': 'Prague', ...}]
        >>> export_to_csv(municipality_data, "election_results.csv")
        Data byla úspěšně uložena do election_results.csv.
    """
    print(f"Exportuji data do souboru: {output_filename}")

    # Step 1: Collect all unique political parties from all municipalities
    all_parties = {}  # Dictionary to store party number -> party name

    for municipality in municipalities_data:
        if 'parties' in municipality and municipality['parties']:
            for party_number, party_info in municipality['parties'].items():
                if party_number not in all_parties:
                    all_parties[party_number] = party_info[PARTY_NAME_KEY]

    # Step 2: Sort parties by their numbers using a simple loop
    temp_list_to_sort = []
    for party_number_text, party_name in all_parties.items():
        temp_list_to_sort.append(
            (int(party_number_text), (party_number_text, party_name))
        )

    temp_list_to_sort.sort()

    sorted_parties = []
    for number, original_item in temp_list_to_sort:
        sorted_parties.append(original_item)

    # Step 3: Create flat data structure for CSV
    csv_data = []
    base_columns = [CODE_COLUMN, LOCATION_COLUMN,
                    REGISTERED_COLUMN, ENVELOPES_COLUMN, VALID_COLUMN]

    for municipality in municipalities_data:
        # Start with basic municipality data
        csv_row = {}

        # Add basic information
        for column in base_columns:
            csv_row[column] = municipality.get(column, DEFAULT_VALUE)

        # Add vote counts for each party
        for party_number, party_name in sorted_parties:
            votes = DEFAULT_VOTES  # Default to 0 votes

            # Get actual votes if party exists in this municipality
            if ('parties' in municipality and
                municipality['parties'] and
                    party_number in municipality['parties']):
                votes = municipality['parties'][party_number][PARTY_VOTES_KEY]

            csv_row[party_name] = votes

        csv_data.append(csv_row)

    # Step 4: Create DataFrame and save to CSV
    dataframe = pd.DataFrame(csv_data)

    # Ensure columns are in correct order
    party_columns = [party_name for party_number, party_name in sorted_parties]
    final_column_order = base_columns + party_columns
    dataframe = dataframe[final_column_order]

    # Save to CSV file
    try:
        dataframe.to_csv(output_filename, index=False, encoding=CSV_ENCODING)
        print(f"Data byla úspěšně uložena do {output_filename}.")
    except IOError as error:
        print(f"  -> CHYBA: Nepodařilo se zapsat do souboru: {error}")


def main():
    """Main function that orchestrates the entire election data scraping process.

    Parses command line arguments, scrapes municipality list from main page,
    downloads detailed data for each municipality, and exports results to CSV.

    Command line arguments:
        url (str): URL of the territorial unit page (in quotes)
        filename (str): Name of output CSV file

    Example:
        $ python main.py "https://volby.cz/pls/ps2017nss/ps32?..." results.csv
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description=(
            "Scraping volebního webu volby.cz pro volby do PS 2017.\n"
            "Příklad použití:\n"
            "  python main.py \"https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103\" \"vysledky.csv\""
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Define required arguments
    parser.add_argument("url",
                        help="URL adresa územního celku (v uvozovkách).",
                        type=str)
    parser.add_argument("filename",
                        help="Název výstupního CSV souboru (v uvozovkách).",
                        type=str)

    # Parse arguments from command line
    arguments = parser.parse_args()

    # Step 1: Download and parse the main page
    print("\nStahuji hlavní stránku...")
    main_page_soup = get_soup_from_url(arguments.url)
    if not main_page_soup:
        print("Nepodařilo se stáhnout hlavní stránku. Ukončuji program.")
        return

    # Step 2: Extract list of all municipalities
    print("Získávám seznam obcí...")
    municipalities = scrape_municipalities_list(main_page_soup, arguments.url)

    if not municipalities:
        print("Nebyly nalezeny žádné obce. Ukončuji program.")
        return

    # Step 3: Download detailed data for each municipality
    print("--- Zahajuji stahování detailů pro všechny obce ---")

    for municipality in tqdm(municipalities, desc=PROGRESS_DESC, unit=PROGRESS_UNIT):
        # Download detail page for this municipality
        detail_soup = get_soup_from_url(municipality['link'])

        # Extract election data if download was successful
        if detail_soup:
            election_details = scrape_one_place_details(detail_soup)
            if election_details:
                # Add election data to municipality record
                municipality.update(election_details)

    print("\nStahování detailů dokončeno.")

    # Step 4: Export all data to CSV file
    export_to_csv(municipalities, arguments.filename)
    print("Program úspěšně dokončen.")


# Run the program when script is executed directly
if __name__ == "__main__":
    main()
