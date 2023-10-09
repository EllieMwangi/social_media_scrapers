import os
import csv
import time
import glob
import random
import logging
import pandas as pd
from selenium import webdriver
from scraper import generate_page_urls, scrape_job_posts
from selenium.webdriver.common.by import By
from blob_connector import AzureBlobStorage


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:S')
logger = logging.getLogger()

class ScraperOrchestrator:
    def __init__(self):
        logger.info("Create azure blob storage storage")
        self.azure_blob_instance = AzureBlobStorage()

        logger.info("Initialize selenium driver with specified options")
        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')

        self.driver = webdriver.Chrome(options=options)

    def create_posting_urls(self):

        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        logger.info("Logging into LinkedIn")
        self.driver.get("https://linkedin.com/uas/login")
        
        logger.info("Sleep for 5 seconds....")
        time.sleep(5)
        
        username = self.driver.find_element(By.ID, "username")
        username.send_keys(email)  
        
        pword = self.driver.find_element(By.ID,"password")
        pword.send_keys(password)        
        
        self.driver.find_element(By.XPATH,"//button[@type='submit']").click()

        logger.info(f"Generate job posts urls")

        for country_name in ['Ghana', 'Nigeria']:
            generate_page_urls(driver=self.driver, country=country_name)

    def scrape_profile_urls(self):

        url_files_list = []

        for file in glob.glob('data/*_job_post_urls.csv'):
            logging.info(f"Extracting job post file: {file}")
            batch = pd.read_csv(file)
            url_files_list.append(batch)
        
        logging.info(f"Writing output file headers")
        with open('data/job_post_data.csv', 'a+', encoding='utf-8', newline='\n') as file:
            writer = csv.DictWriter(file, fieldnames=['job_id','job_title','job_link_url','company_name','company_linkedin_url', 'job_location','job_workplace_type','posting_date'])
            writer.writeheader()

        job_post_urls = pd.concat(url_files_list)
        for row in job_post_urls.to_dict('records'):

            scrape_job_posts(self.driver, row['job_post_url'],)
            random_sleep = random.randint(3,6)
            logger.info(f"Sleep for {random_sleep} seconds")
            time.sleep(random_sleep)
            
        self.driver.quit()

    def upload_scraped_file(self):

        logger.info(f"Retrieve scraped results filename")
        for file in glob.glob('data/*_post_data.csv'):
            results_file_name = file

        self.azure_blob_instance.upload_file(results_file_name)

    def main(self):

        self.create_posting_urls()
        self.scrape_profile_urls()
        self.upload_scraped_file()





        
            
            