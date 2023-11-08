import os
import csv
import time
import glob
import random
import logging
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from scraper import scrape_about_page
from selenium.webdriver.common.by import By
from blob_connector import AzureBlobStorage
import undetected_chromedriver as uc


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:S')
logger = logging.getLogger()

class ScraperOrchestrator:
    def __init__(self):
        logger.info("Create azure blob storage storage")
        self.azure_blob_instance = AzureBlobStorage()

        logger.info("Initialize selenium driver with specified options")
        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument("window-size=1920x1080")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')

        self.driver = uc.Chrome(options=options)

    def extract_blob_files(self):
        self.azure_blob_instance.get_latest_file()
        self.azure_blob_instance.download_latest_file()

    def scrape_profile_urls(self):

        for file in glob.glob('data/*'):
            profiles_file_name = file

        expected_fields = ['Company ID','Linkedin Profile','Company Name','Description', 'Address','Logo','Website', 'Phone', 'Industry','Founded', 'Company size', 'Headquarters', 'Specialties','Employees On LinkedIn']

        logger.info(f"Writing output file headers")
        with open(str.replace(profiles_file_name, '.csv','_scrapped_data.csv'),mode='a+', encoding='utf-8', newline='\n') as file:
            writer = csv.DictWriter(file, fieldnames=expected_fields)
            writer.writeheader()

        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        logger.info("Logging into LinkedIn")
        self.driver.get("https://linkedin.com/uas/login")
        
        logger.info("Sleep for 5 seconds....")
        time.sleep(5)
        
        username = self.driver.find_element(By.ID, "username")
        #logger.info(f"{username}")
        username.send_keys(email)  
        
        pword = self.driver.find_element(By.ID,"password")
        pword.send_keys(password)        
        
        self.driver.find_element(By.XPATH,"//button[@type='submit']").click()

        logger.info(f"Sleep 5 seconds ...")
        time.sleep(5)

        src = self.driver.page_source
    
        # Now using beautiful soup
        soup = BeautifulSoup(src, 'lxml')
        logger.info(f"{soup}")

        data_linkedin_urls = pd.read_csv(profiles_file_name)
        logging.info(f"Number of profiles to be scrapped: {data_linkedin_urls.shape}")
        logging.info(f"{data_linkedin_urls.head()}")

        # Loop through URLs
        output_file = str.replace(profiles_file_name, '.csv',f'_scrapped_data.csv')
        for row in data_linkedin_urls.to_dict('records'):
            logging.info(f"Scraping about page for linkedin url: {row['linkedin_profile']}")
            scrape_about_page(row, self.driver, output_file)
            random_sleep = random.randint(3,6)
            logger.info(f"Sleep for {random_sleep} seconds")
            time.sleep(random_sleep)
        
        logging.info(f"Upload results")
        self.upload_scraped_file(output_file)   
        self.driver.quit()

    def upload_scraped_file(self, results_file_name):

        logger.info(f"Upload scrapped linkedin_profiles...")
        self.azure_blob_instance.upload_file(results_file_name)

    def main(self):

        self.extract_blob_files()
        self.scrape_profile_urls()





        
            
            