import selenium as s
from selenium import webdriver
import bs4 as bs
from bs4 import BeautifulSoup 
import requests
import os 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


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
print(len(containers))

# close the browser after process
driver.quit()


