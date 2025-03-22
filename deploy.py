import streamlit as st
import all_funcs as funcs

st.title("Company Information Scraper")

if 'startups_info' not in st.session_state:
    st.session_state.startups_info = None
if 'company_info' not in st.session_state:
    st.session_state.company_info = None

st.header("Search Settings")
query = st.text_input("Enter your search query:", "find 10 tech giants in bangalore")
enhance = st.checkbox("Enhance query with AI", value=True)

if st.button("Start Search"):
    with st.spinner("Processing..."):
        if enhance:
            enhanced_query = funcs.enhance_query(query)
            st.info(f"Enhanced query: {enhanced_query}")
        else:
            enhanced_query = query
        
        st.subheader("Finding top search results...")
        top_links = funcs.search_duckduckgo(enhanced_query)
        st.write(top_links)
        
        st.subheader("Extracting company information...")
        combined_scraped_data = ""
        for link in top_links:
            page_content = funcs.scrape_page_content(link)
            content_str = ""
            for item in page_content:
                content_str += f"Title: {item['title']}\nDescription: {item['description']}\n\n"
            combined_scraped_data += content_str + "\n"
        
        startups_info = funcs.extract_information_from_scraped_data(combined_scraped_data, query)
        st.session_state.startups_info = funcs.parse_list_items(startups_info)
        
        st.subheader("Companies Found:")
        for i, company in enumerate(st.session_state.startups_info, 1):
            st.write(f"{i}. {company}")

if st.session_state.startups_info is not None:
    if st.button("Find LinkedIn & Additional Info"):
        with st.spinner("Searching LinkedIn..."):
            linkedin_urls = funcs.find_linkedin_pages(st.session_state.startups_info)
            
            company_info = []
            for company, linkedin_url in linkedin_urls.items():
                linkedin_data = funcs.extract_linkedin_content(linkedin_url)
                info = funcs.extract_company_info(linkedin_data, company, linkedin_url)
                company_info.append(info)
            
            st.session_state.company_info = company_info

if st.session_state.company_info is not None:
    st.subheader("Detailed Company Information:")
    for info in st.session_state.company_info:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Company:** {info['company_name']}")
            st.write(f"**Website:** {info['website']}")
        with col2:
            st.write(f"**Location:** {info['location']}")
            st.write(f"**LinkedIn:** [{info['linkedin_url']}]({info['linkedin_url']})")
        st.divider()
    
