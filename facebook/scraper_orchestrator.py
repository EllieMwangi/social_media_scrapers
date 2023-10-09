import os
import csv
import time
import glob
import random
import logging
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from scraper import scrape_about_page
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
        options.add_argument("window-size=1920x1080")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')

        self.driver = webdriver.Chrome(options=options)

    def extract_blob_files(self):
        self.azure_blob_instance.get_latest_file()
        self.azure_blob_instance.download_latest_file()

    def scrape_profile_urls(self):

        for file in glob.glob('data/*'):
            profiles_file_name = file

        expected_fields =  ['profile_link','company_id','business_name','business_description','address','latitude','longitude','link_address','categories','emails', 'phone_numbers', 'website_urls', 'hours_of_operation']

        logger.info(f"Writing output file headers")
        with open(str.replace(profiles_file_name, '.csv','_scrapped_data.csv'),mode='a+', encoding='utf-8', newline='\n') as file:
            writer = csv.DictWriter(file, fieldnames=expected_fields)
            writer.writeheader()

        email = os.getenv("FACEBOOK_EMAIL")
        password = os.getenv("FACEBOOK_PASSWORD")

        logger.info("Logging into Facebook")
        self.driver.get("https://m.facebook.com/login/")

        src = self.driver.page_source

        # Now using beautiful soup
        soup = BeautifulSoup(src, 'lxml')

        logger.info(f"{soup}")
            
        logger.info("Sleep for 5 seconds....")
        time.sleep(5)

        username =  self.driver.find_element(By.NAME, "email")
        username.send_keys(email)  
        
        pword =  self.driver.find_element(By.NAME, "pass")
        pword.send_keys(password)        
        
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        

        logger.info("Sleep for 60 seconds..")
        time.sleep(random.randint(60,90))

        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

        data_facebook_ids = pd.read_csv(profiles_file_name)

        for row in data_facebook_ids.to_dict('records'):

            logging.info(f"Scraping about page for facebook page: {row['profile_link']}")
            scrape_about_page(row, self.driver, profiles_file_name)
            random_sleep = random.randint(5,10)
            logger.info(f"Sleep for {random_sleep} seconds")
            time.sleep(random_sleep)
            
        self.driver.quit()

    def upload_scraped_file(self):

        logger.info(f"Retrieve scraped results filename")
        for file in glob.glob('data/*_scrapped_data.csv'):
            results_file_name = file

        self.azure_blob_instance.upload_file(results_file_name)

    def main(self):

        self.extract_blob_files()
        self.scrape_profile_urls()
        self.upload_scraped_file()





        
            
            