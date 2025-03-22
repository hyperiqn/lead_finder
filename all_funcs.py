import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import time
from openai import OpenAI

client = OpenAI(api_key='')

def enhance_query(initial_query):
    prompt = f"""Rewrite the following search query to be more effective for DuckDuckGo: {initial_query}
    return only the query, do not include quotes."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in search optimization."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        temperature=0.3
    )
    enhanced_query = response.choices[0].message.content.strip()
    return enhanced_query

def search_duckduckgo(query):
    url = f"https://duckduckgo.com/html/?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}  
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("a", class_="result__a")
    top_links = [result.get("href") for result in results[:5]]
    for i, link in enumerate(top_links):
        if link.startswith("//duckduckgo.com/l/?uddg="):
            top_links[i] = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])
    return top_links

def scrape_page_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        results = []
        
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            title = heading.get_text(strip=True)
            description_paragraphs = []
            
            for sibling in heading.find_next_siblings():
                if sibling.name and sibling.name.startswith("h"):
                    break 
                if sibling.name == "p":
                    description_paragraphs.append(sibling.get_text(strip=True))
            
            if description_paragraphs:
                results.append({
                    "title": title,
                    "description": " ".join(description_paragraphs)
                })
        return results
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def extract_information_from_scraped_data(scraped_data, original_query):
    prompt = f"""
    Based on the following scraped data, respond to this query: "{original_query}"
    
    Extract exactly the information requested in the query. If the query asks for a specific number of items, 
    provide exactly that many. Present the results in a clear, numbered list. Do not include any extra information unless it has been explicitly asked for.
    
    Scraped Data:
    {scraped_data}
    """
    
    response = client.chat.completions.create(
        model="o3-mini",  
        messages=[
            {"role": "system", "content": "You are a data extraction specialist focused on identifying relevant information from web content."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=1500
    )
    
    extracted_information = response.choices[0].message.content.strip()
    return extracted_information

def parse_list_items(extracted_text):
    lines = extracted_text.strip().split('\n')
    clean_items = []
    
    current_item = ""
    for line in lines:
        line = line.strip()
        if line and (line[0].isdigit() and '. ' in line[:5]):
            if current_item: 
                clean_items.append(current_item)
            current_item = line.split('. ', 1)[1].strip()
        elif line and current_item:  
            current_item += " " + line
    
    if current_item:
        clean_items.append(current_item)
    
    if not clean_items:
        clean_items = [line for line in lines if line]
    
    return clean_items

def find_linkedin_pages(startups):
    linkedin_urls = {}
    for startup in startups:
        query = f"{startup} linkedin bangalore"
        time.sleep(1)
        links = search_duckduckgo(query)
        linkedin_url = next((link for link in links if "linkedin.com/company" in link), None)
        if linkedin_url:
            linkedin_urls[startup] = linkedin_url
            print(f"Found LinkedIn for {startup}: {linkedin_url}")
        else:
            print(f"No LinkedIn found for {startup}")
    return linkedin_urls

def extract_linkedin_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator="\n", strip=True)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except Exception as e:
        return f"Error: {str(e)}"

def extract_company_info(linkedin_data, company_name, linkedin_url):
    prompt = f"""
    Extract the website and the headquarter's location from the scraped web data for the company:
    {linkedin_data}
    Only return the website and headquarter location tab separated with the website before the location. Do not include the column name before it. If you do not find one or the other return NA for that value.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a data extraction specialist focused on identifying relevant information from web content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=50
    )
    extracted_information = response.choices[0].message.content.strip()
    parts = extracted_information.split(' ', 1)
    website = parts[0].strip() if len(parts) > 0 else "NA"
    location = parts[1].strip() if len(parts) > 1 else "NA"
    return {
        "company_name": company_name,
        "website": website,
        "location": location,
        "linkedin_url": linkedin_url
    }


def main():
    initial_query = "find 10 tech giants in bangalore"
    enhanced_query = enhance_query(initial_query)
    print(f"Enhanced query: {enhanced_query}")

    top_links = search_duckduckgo(enhanced_query)
    print("Top links found:")
    for link in top_links:
        print(link)

    combined_scraped_data = ""
    for link in top_links:
        page_content = scrape_page_content(link)
        content_str = ""
        for item in page_content:
            content_str += f"Title: {item['title']}\nDescription: {item['description']}\n\n"
        combined_scraped_data += content_str + "\n"

    startups_info = extract_information_from_scraped_data(combined_scraped_data, initial_query)
    startups_info = parse_list_items(startups_info)
    print("\nExtracted startup information:")
    print(startups_info)


    linkedin_urls = find_linkedin_pages(startups_info)

    company_info = []
    for company, linkedin_url in linkedin_urls.items():
        linkedin_data = extract_linkedin_content(linkedin_url)
        info = extract_company_info(linkedin_data, company, linkedin_url)
        company_info.append(info)


    print("\nFinal company information:")
    for info in company_info:
        print(f"Company: {info['company_name']}")
        print(f"Website: {info['website']}")
        print(f"Location: {info['location']}")
        print(f"LinkedIn: {info['linkedin_url']}")
        

if __name__ == "__main__":
    main()
