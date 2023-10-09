from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import logging
import time
import csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:S')

def generate_page_urls(driver, country):

    driver.get(f'https://www.linkedin.com/jobs/search/?location={country}')      

    logging.info(f"Sleep for 10 seconds...")
    time.sleep(10)

    src = driver.page_source
    soup = BeautifulSoup(src, 'lxml')

    logging.info(f"Extract existing job pagination numbers")
    available_pages = soup.find_all('div', {'class': 'jobs-search-results-list__pagination pv5 artdeco-pagination ember-view'})
    if len(available_pages) > 0:
        page_numbers = available_pages[0].find_all('li')
        page_numbers = [val.get_text().strip() for val in page_numbers]
        logging.info(f"Pagination goes up to page number {page_numbers[-1]}")
    else:
        logging.info(f"Failed to extract page numbers")

    logging.info("Generate job post page urls")
    final_page_number = page_numbers[-1]
    start_indexes = list(range(25, int(final_page_number)*25, 25))
    job_post_urls = [f'https://www.linkedin.com/jobs/search/?location={country}&start={val}' for val in start_indexes]
    job_post_urls = [f'https://www.linkedin.com/jobs/search/?location={country}'] + job_post_urls

    logging.info(f'Generated_urls: {job_post_urls}')

    job_posts_frame = pd.DataFrame(job_post_urls, columns=['job_post_url'])

    logging.info(f"Writing job post urls to  file")
    job_posts_frame.to_csv(f'data/{country}_job_post_urls.csv', index=False)

def scrape_job_posts(driver, url):
    logging.info(f"Extracting job postings on url: {url}")

    driver.get(url)

    logging.info(f"Sleep for 10 seconds")
    time.sleep(10)

    scrolling_element = driver.find_element(By.XPATH,'//*[@id="main"]/div/section[1]/div') 
    logging.info(f"Extracting job list container height..")
    last_height = driver.execute_script("return arguments[0].scrollHeight", scrolling_element)

    logging.info(f"Section Length: {last_height}")
    job_listings_list = []

    for i in range(0, int(last_height),100):
        logging.info(f"Scrolling down job list...")
        driver.execute_script("arguments[0].scrollTop = arguments[1]", scrolling_element, i)
        time.sleep(5)

    src = driver.page_source
    soup = BeautifulSoup(src, 'lxml')
    logging.info(f"Fetch all job postings on page ...")

    job_posts = soup.select('div[class*="job-card-container relative job-card-list"]')

    for post in job_posts:
        job_id = post['data-job-id']
        job_title_obj = post.find('div', {'class':'full-width artdeco-entity-lockup__title ember-view'})
        job_title = job_title_obj.get_text().strip()
        job_link_url = job_title_obj.find('a')['href']
        company_name_obj = post.find('div', {'class':'artdeco-entity-lockup__subtitle ember-view'})
        if company_name_obj is not None:
            company_title = company_name_obj.get_text().strip()
            company_link_url = company_name_obj.find('a')
            if company_link_url is not None:
                company_link_url = company_link_url['href']
                company_link_url = f"https://linkedin.com{company_link_url}"
            else:
                company_link_url = np.nan
        else:
            company_title = np.nan
            company_link_url = np.nan
        job_location = post.find('li', {'class':'job-card-container__metadata-item'}).get_text().strip()
        job_workplace_type = post.find('li', {'class': 'job-card-container__metadata-item job-card-container__metadata-item--workplace-type'})
        if job_workplace_type is not None:
            job_workplace_type = job_workplace_type.get_text().strip()
        else:
            job_workplace_type = np.nan
        job_posting_date = post.find('time')
        if job_posting_date is not None:
            job_posting_date = job_posting_date['datetime']
        else:
            job_posting_date = np.nan

        job_post_data = {'job_id':job_id,'job_title':job_title, 'job_link_url':f"https://linkedin.com{job_link_url}", 'company_name':company_title, 'company_linkedin_url':company_link_url, 'job_location':job_location, 'job_workplace_type':job_workplace_type, 'posting_date':job_posting_date}

        job_listings_list.append(job_post_data)

    logging.info("Writing job posts to file")
    with open('data/job_post_data.csv', 'a+', encoding='utf-8', newline='\n') as file:
        writer = csv.DictWriter(file, fieldnames=['job_id','job_title','job_link_url','company_name','company_linkedin_url', 'job_location','job_workplace_type','posting_date'])
        writer.writerows(job_listings_list)