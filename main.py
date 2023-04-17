import selenium as s
from selenium import webdriver
import bs4 as bs
from bs4 import BeautifulSoup 
import requests
import os 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import shutil
import time

cwd = os.getcwd()
firefoxdriverpath = os.path.join(cwd,"resources/firefoxdriver")
driver = webdriver.Firefox(firefoxdriverpath)

#retrives the response from the url as byte stream
driver.get("https://www.google.com/search?q=swimming+pool+in+homes&tbm=isch&ved=2ahUKEwjHppGv-Y3-AhXUTaQEHVaOAbAQ2-cCegQIABAA&oq=swimming+pool+in+homes&gs_lcp=CgNpbWcQAzIFCAAQgAQ6BAgjECc6BggAEAUQHjoGCAAQCBAeOggIABCABBCxA1CbCljDK2DQLWgAcAB4AIABpQOIAZ8UkgEKMC4xMy4xLjAuMZgBAKABAaoBC2d3cy13aXotaW1nwAEB&sclient=img&ei=H-YqZIebF9SbkdUP1pyGgAs&bih=909&biw=936&client=firefox-b-d")

# dealing with the cookies page
button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[1]/div/div/button/span")))
button.click()
a = input("waiting for user load maximum data and press enter")

#scrolling all the way up
driver.execute_script("window.scrollTo(0,0);")

#parsers the text as html code
page_html = driver.page_source
soup = BeautifulSoup(page_html, "html.parser")

#gets all the html containers matching the given attributes
containers = soup.find_all('div',attrs={"class":"isv-r PNCib MSM1fd BUooTd"})

#iterate through the images by iterating through the result set
i = 1
j = 1
k = 0
for tag in containers:
    k = k + 1
    while(j<=k):
        #get xpath of each html tag
        xpath = f'/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div[{i}]/a[1]/div[1]/img'
        try:           

            #click on the image
            image = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            image.click()
            

            imagepath = '/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div[2]/div/div[2]/div[2]/div[2]/c-wiz/div/div[2]/div[1]/a/img[1]'
            
            # get the tag corresponding to the image
            tagi = driver.find_element(By.XPATH, imagepath)     
            src = tagi.get_attribute('src')
            print('here')
            response = requests.get(src)
            print('here2')
            filepath = f"/home/sagarvincent/projects/Softwareengineering/Webscrapper/data/images/{i}.jpg"
            if response.status_code == 200:
                try:
                    with open(filepath, 'wb') as f:                        
                        f.write(response.content)
                        
                except:
                    print('couldnt download')

        except:
            
            print(i)
            i = i + 1
            
            if j == len(containers)-1:
                # close the browser after process
                print(j,k)
                driver.quit()
                break

            continue

        
        print(f'{j}th image')
        i = i + 1
        j = j + 1

        



