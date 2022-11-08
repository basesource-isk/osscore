
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from varname import nameof
from main.models import ResponseHtmlTestLine
import os
import platform

def runSeleniumTest(yamlDict):
    chrome_options=Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.accept_insecure_certs=True
    s=platform.system()
    print(f'==={nameof(s)}:{s}')
    if 'windows' in s.lower():
        driver=webdriver.Chrome("./utils/chromedriver.exe",options=chrome_options)
    else:
        driver=webdriver.Chrome(options=chrome_options)
    
    resultList=list()
    pages=yamlDict['pages']
    baseUrl=yamlDict['base url']
    urls=list()
    for page in pages:
        url=baseUrl+page['url']
        urls.append(url)
    i=0
    for page in pages:
        if page=='' or page=='\n':
            continue
        url=baseUrl+page['url']
        attr=page['method']
        val=page['value']
        text=page['text']
        click=page['click']
        driver.get(url)
        driver.implicitly_wait(1)
        result=str()
        elem=None
        attr_value=None
        try:
            if attr=='id':
                elem=driver.find_element(By.ID,val)
                attr_value=elem.get_attribute(attr)
            elif attr=='name':
                elem=driver.find_element(By.NAME,val)
                attr_value=elem.get_attribute(attr)
            elif attr=='xpath':
                elem=driver.find_element(By.XPATH,val)
                attr_value=elem.get_attribute(attr)
            elif attr=='linktext':
                elem=driver.find_element(By.PARTIAL_LINK_TEXT)
                attr_value=elem.text
            elif attr=='tag':
                elem=driver.find_element(By.TAG_NAME,val)
                attr_value=elem.tag_name
            elif attr=='class':
                elem=driver.find_element(By.CLASS_NAME,val)
                attr_value=elem.get_attribute(attr)
            elif attr=='css':
                elem=driver.find_element(By.CSS_SELECTOR,val)
                attr_value=attr
            result='ОК'
        except:
            result='FAIL'
        color=str()
        if result=='FAIL':
            color='red'
            elem=None
        else:
            color='green'
            elem=elem.screenshot_as_base64
        page=ResponseHtmlTestLine(i,url,attr,val,result,elem,color)
        resultList.append(page)
        i+=1
    
    driver.close()
    return resultList