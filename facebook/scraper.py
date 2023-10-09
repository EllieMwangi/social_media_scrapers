from bs4 import BeautifulSoup
import phonenumbers
import itertools
import numpy as np
import logging
import urllib
import time
import string
from csv import DictWriter
import re
from urlextract import URLExtract

extractor = URLExtract()
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:S')

def scrape_about_page(row, driver, output_file):

    driver.get(row['profile_link'])      
    # this will open the link
    start = time.time()

    # will be used in the while loop
    initialScroll = 0
    finalScroll = 1000

    logging.info('Scrolling facebook page...')
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
        time.sleep(10)
        # You can change it as per your needs and internet speed

        end = time.time()

        # We will scroll for 20 seconds.
        # You can change it as per your needs and internet speed
        if round(end - start) > 30:
            break

    src = driver.page_source

    # Now using beautiful soup
    soup = BeautifulSoup(src, 'lxml')


    # Days of the week
    days_of_week = ['Tuesday', 'Wednesday','Thursday', 'Friday', 'Saturday', 'Sunday','Monday']
    
    field_names = ['profile_link','company_id','business_name','business_description','address','latitude','longitude','link_address','categories','emails', 'phone_numbers', 'website_urls', 'hours_of_operation']

    version_1_objs = soup.find_all('div', {'data-nt':'FB:TEXT4'}) + soup.find_all('div', {'data-nt':'NT:BOX_3_CHILD'})
    version_2_objs = soup.find_all('div', {'id':'profile_intro_card'})

    if (len(version_1_objs) > 0) and (len(version_2_objs) == 0):
        logging.info(f"Data extracted from the facebook page: {row['profile_link']}. Parse facebook data ...")
        data_objects_text = [val.get_text().strip() for val in version_1_objs]
        href_links = soup.find_all('a', href=True)
        if len(href_links) > 0:
            href_links = [val['href'] for val in href_links]
               
        # Extract google maps object if present 
        map_object = soup.find('div', {'class':"profileMapTile"})

        if map_object is not None:
            map_link = map_object['style']
            latitude = map_link.split('%5D')[1].split('&')[0].split('%2C')[0].lstrip('=')
            longitude = map_link.split('%5D')[1].split('&')[0].split('%2C')[1].lstrip('=')

            if 'Get Directions' in data_objects_text:
                address_string = data_objects_text[data_objects_text.index('Get Directions') - 1]
            else:
                address_string = np.nan
        else:
            latitude = np.nan
            longitude = np.nan
            address_string = np.nan
            map_link = np.nan

        
        # Extract company business name
        business_name = soup.find('title').get_text().strip().split('-')[0].strip()
        business_description =  np.nan

        category_links = [link for link in href_links if 'pages/category' in link]
        category_names = [link.rstrip('/').split('/')[-1] for link in category_links]
        if len(category_names) == 0:
            category_names = np.nan

        emails = []
        phone_numbers = []
        website_urls = []

        for text_obj in data_objects_text:
                
            # Derive email address
            extract_emails = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", text_obj.strip())
            if len(extract_emails) > 0:
                emails.append(extract_emails)

            # Derive phone numbers
            extracted_numbers = list(phonenumbers.PhoneNumberMatcher(text_obj, row['country_code']))
            if extracted_numbers != []:
                    formatted_numbers = [phonenumbers.format_number(phonenumbers.parse(val.raw_string, row['country_code']), phonenumbers.PhoneNumberFormat.E164) for val in extracted_numbers]
                    phone_numbers.append(formatted_numbers)

            # Derive website urls
            extract_urls = extractor.find_urls(text_obj)
            if len(extract_urls) > 0:
                website_urls.append(extract_urls)

   
        if len(emails) > 0:
            emails = list(set(itertools.chain.from_iterable(emails)))
        else:
            emails = np.nan

        if len(phone_numbers) > 0:
            phone_numbers = list(set(itertools.chain.from_iterable(phone_numbers)))
        else:
            phone_numbers = np.nan

        if len(website_urls) > 0:
            website_urls = list(set(itertools.chain.from_iterable(website_urls)))
        else:
            website_urls = np.nan

        # Extract hour data if present
        available_days = []
        hour_data_obj = {}

        for text in data_objects_text:
            if text in days_of_week:
                available_days.append(text)

        if len(available_days) > 0:
            last_day_index = data_objects_text.index(available_days[-1])
            hours = data_objects_text[last_day_index + 1:last_day_index  + len(available_days) + 1]
            
            for i, j in zip(available_days, hours):
                hour_data_obj[i] = j

        if len(hour_data_obj) == 0:
            hour_data_obj = np.nan

        facebook_data_obj = {'profile_link':row['profile_link'],'company_id':row['company_id'],'business_name':business_name,'business_description':business_description, 'address':address_string, 'latitude':latitude,'longitude':longitude, 'link_address':map_link, 'categories':category_names, 'emails':emails, 'phone_numbers':phone_numbers, 'website_urls':website_urls, 'hours_of_operation':hour_data_obj}
        logging.info(f"Completed extracting {facebook_data_obj} from {row['profile_link']}")

    elif len(version_2_objs) > 0:
        business_name = soup.find('h3', {'class':'_6x2x'}).text
        business_description = soup.find('div', {'class':'_52ja _52jj _ck_ _2pia'})
        if business_description is not None:
            business_description = business_description.text
        else:
            business_description = np.nan

        data_objects_text = soup.find_all('span', {'class':'_7i5d'})
        data_objects_text = [val.text for val in data_objects_text]

        category_names = [val for val in data_objects_text if 'Page' in val]
        if len(category_names) == 0:
            category_names = np.nan


        if len(data_objects_text) > 2:
            address_string = data_objects_text[2]
            exclist = string.punctuation
            table_ = str.maketrans(exclist, ' '*len(exclist))
            cleaned_address = ''.join(address_string.translate(table_).split())
            if cleaned_address.isdigit():
                address_string = np.nan
        else:
            address_string = np.nan

        phone_numbers = []
        website_urls = []
        emails = []

        for text in data_objects_text:
            extracted_numbers = list(phonenumbers.PhoneNumberMatcher(text, row['country_code']))
            if extracted_numbers != []:
                    formatted_numbers = [phonenumbers.format_number(phonenumbers.parse(val.raw_string, row['country_code']), phonenumbers.PhoneNumberFormat.E164) for val in extracted_numbers]
                    phone_numbers.append(formatted_numbers)
            
            extract_urls = extractor.find_urls(text)
            if len(extract_urls) > 0:
                website_urls.append(extract_urls)

            extract_emails = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", text.strip())
            if len(extract_emails) > 0:
                emails.append(extract_emails)

        if len(emails) > 0:
            emails = list(set(itertools.chain.from_iterable(emails)))
        else:
            emails = np.nan

        if len(phone_numbers) > 0:
            phone_numbers = list(set(itertools.chain.from_iterable(phone_numbers)))
        else:
            phone_numbers = np.nan

        if len(website_urls) > 0:
            website_urls = list(set(itertools.chain.from_iterable(website_urls)))
        else:
            website_urls = np.nan

        href_links = soup.find_all('a', href = True)
        if len(href_links) > 0:
            href_links = [val['href'] for val in href_links]

        map_link = [val for val in href_links if 'maps.google.com' in val]

        if len(map_link) > 0:
            map_link = map_link[0]
            map_link = urllib.parse.unquote(map_link, encoding='utf-8', errors='replace')
            geocode = map_link.split('&hl')[0].split('q=')[1]
            if '%2C' in  geocode:
                latitude = geocode.split('%2C')[0]
                longitude = geocode.split('%2C')[1]   
            else:
                latitude = np.nan
                longitude = np.nan
        else:
            map_link = np.nan
            latitude = np.nan
            longitude = np.nan
     
        hour_data_obj = np.nan

        facebook_data_obj = {'profile_link':row['profile_link'],'company_id':row['company_id'],'business_name':business_name, 'business_description':business_description, 'address':address_string, 'latitude':latitude, 'longitude':longitude,'link_address':map_link, 'categories':category_names, 'emails':emails, 'phone_numbers':phone_numbers, 'website_urls':website_urls, 'hours_of_operation':hour_data_obj}
        logging.info(f"Completed extracting {facebook_data_obj} from {row['profile_link']}")
        
    else:
        logging.info(f"{row['profile_link']} facebook page is invalid!")
        facebook_data_obj = {}
        for col in field_names[2:]:
            facebook_data_obj[col] = np.nan
        facebook_data_obj['profile_link'] = row['profile_link']
        facebook_data_obj['company_id'] = row['company_id']

    logging.info('Writing results to file')
    with open(str.replace(output_file, '.csv','_scrapped_data.csv'), 'a+', newline='\n', encoding='utf-8') as file:
        writer = DictWriter(file, field_names)
        writer.writerow(facebook_data_obj)