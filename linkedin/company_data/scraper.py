import csv
import time
import logging
import numpy as np
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:S')
logger = logging.getLogger()

def scrape_about_page(row, driver, file_name):

    driver.get(row['linkedin_profile'])      
    # this will open the link
    start = time.time()

    # will be used in the while loop
    initialScroll = 0
    finalScroll = 1000

    logger.info("Scrolling url page...")
    while True:
        driver.execute_script(f"window.scrollTo({initialScroll},{finalScroll})")
        # this command scrolls the window starting from
        # the pixel value stored in the initialScroll
        # variable to the pixel value stored at the
        # finalScroll variable
        initialScroll = finalScroll
        finalScroll += 1000

        # we will stop the script for 3 seconds so that
        # the data can load
        time.sleep(3)
        # You can change it as per your needs and internet speed

        end = time.time()

        # We will scroll for 20 seconds.
        # You can change it as per your needs and internet speed
        if round(end - start) > 15:
            break

    src = driver.page_source
    
    # Now using beautiful soup
    soup = BeautifulSoup(src, 'lxml')

    logger.info(f"Extracting company name...")
    company_name = soup.find('h1', {'class': 'ember-view text-display-medium-bold org-top-card-summary__title full-width'})
    if company_name is not None:
        company_name = company_name.get_text().strip()
    else:
        company_name = np.nan
    
    logger.info(f"Extracting about section...")
    about_section = soup.find('section', {'class': 'artdeco-card org-page-details-module__card-spacing artdeco-card org-about-module__margin-bottom'})

    if about_section is not None:
        overview = about_section.find('p')
        if overview is not None:
            overview = overview.get_text().strip()
        else:
            overview = np.nan
    else:
        overview = np.nan
        
    logger.info(f"Extracting logo image url..")
    logo_image = soup.find('div', {'class':'org-top-card-primary-content__logo-container'})

    if logo_image is not None:
        logo_image = logo_image.find('img')
        if logo_image is not None:
            logo_image = logo_image['src']
        else:
            logo_image = np.nan
    else:
        logo_image = np.nan

    if about_section is not None:
        company_details = about_section.find('dl')
        company_details_titles = company_details.find_all('dt')
        company_details_titles = [val.get_text().strip() for val in company_details_titles]
        company_details_data = company_details.find_all('dd')
        company_details_data = [' '.join(val.get_text().strip().split()) for val in company_details_data]
        employees_on_linkedin = [val for val in company_details_data if 'LinkedIn Includes' in val]
        if len(employees_on_linkedin) > 0:
            idx = company_details_data.index(employees_on_linkedin[0])
            company_details_data.pop(idx)
            company_details_titles.append('Employees On LinkedIn')
            company_details_data.append(employees_on_linkedin[0])
        print(company_details_titles)
        print(company_details_data)

    logger.info(f"Extracting company address...")
    company_address = soup.select('div[class*="org-location-card"]')
 
    if len(company_address) > 0:
        location_data = []
        for i in company_address:
            branch_name = i.find_all('h4')
            address_string = i.find_all('p')
            if len(branch_name) > 0:
                branch_name = [val.get_text().strip() for val in branch_name][0]
            else:
                branch_name = None
            
            if len(address_string) > 0:
                address_string = [val.get_text().strip() for val in address_string][0]
            else:
                address_string = None

            location_obj = {'location_title':branch_name, 'location_address':address_string}
            location_data.append(location_obj)
    else:
        location_data = np.nan

    company_linkedin_data = {'Company ID':row['company_id'],'Linkedin Profile': row['linkedin_profile'],'Company Name': company_name, 'Description':overview, 'Address':location_data, 'Logo':logo_image}

    expected_fields = ['Company ID','Linkedin Profile','Company Name','Description', 'Address','Logo','Website', 'Phone', 'Industry','Founded', 'Company size', 'Headquarters', 'Specialties','Employees On LinkedIn']

    if about_section is not None:
        for title, data in zip(company_details_titles, company_details_data):
            company_linkedin_data[title] = data

    for key in expected_fields:
        if key not in company_linkedin_data.keys():
            company_linkedin_data[key] = np.nan
    
    with open(file_name,mode='a+', encoding='utf-8', newline='\n') as file:
        writer = csv.DictWriter(file, fieldnames=expected_fields)
        writer.writerow(company_linkedin_data)