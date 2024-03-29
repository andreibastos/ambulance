# coding: utf-8
import sys
import argparse
from urllib import request
import base64
import hashlib
import socket
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
from PIL import Image


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-q", "--queries", nargs='+',
                required=True, help="query to search")
ap.add_argument("-c", "--count", type=int, default=10, help="count to search")
ap.add_argument("-l", "--links", help="link directory", default='links')
ap.add_argument("-i", "--images", default='images', help="images folder")

args = vars(ap.parse_args())

# timeout 10 seconds per image
socket.setdefaulttimeout(10)

# Adding information about user agent
opener = request.build_opener()
opener.addheaders = [
    ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
request.install_opener(opener)

# get paths
DRIVER_PATH = './chromedriver'
queries = args['queries']
max_links = args['count']
OUTPUT_FOLDER_IMAGES = args['images']
OUTPUT_FOLDER_LINKS = args['links']


def createDirectoryIfNotExist(folder):
  if not os.path.exists(folder):
    os.makedirs(folder)

createDirectoryIfNotExist(OUTPUT_FOLDER_IMAGES)
createDirectoryIfNotExist(OUTPUT_FOLDER_LINKS)

def fetch_image_and_download(query: str, max_links_to_fetch: int, wd: webdriver.Chrome, sleep_between_interactions: int = 1):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

    # build the google query
    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

    # load the page
    wd.get(search_url.format(q=query))

    image_urls = set()
    images_base64 = set()
    image_count = 0
    results_start = 0
    output_folder = os.path.join(OUTPUT_FOLDER_IMAGES, query)
    filepath_links = os.path.join(OUTPUT_FOLDER_LINKS, query)

    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = wd.find_elements(By.CLASS_NAME,"Q4LuWd")
        number_results = len(thumbnail_results)

        print(
            f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue
            
            try:
                # extract image urls
                actual_images = wd.find_elements(By.CLASS_NAME, 'iPVvYb')
                for actual_image in actual_images:
                    src = actual_image.get_attribute('src')
                    print(src)
                    if src and 'http' in src:
                        image_urls.add(src)
                        download_image(output_folder, src)
                    elif 'data:' in src:
                        images_base64.add(src)
                        download_base64(output_folder, src)
            except:
                print('error to find img.iPVvYb')

            with open(filepath_links, 'a') as f:
                for link in image_urls:
                    f.write("%s\n" % link)

            image_count = len(image_urls) + len(images_base64)
            print('{p:2.2f}%'.format(p=100*image_count/max_links_to_fetch))
            sys.stdout.write("\033[F")  # Cursor up one line

            if image_count >= max_links_to_fetch:
                print(f"Found: {image_count} image, done!")
                return image_urls, images_base64

        has_more = wd.find_element(By.CLASS_NAME, 'YstHxe')
        if (has_more and not 'none' in has_more.get_attribute('style')):
            load_more_button = wd.find_element(By.CLASS_NAME,"mye4qd")
            print('load more')
            if load_more_button:
                load_more_button.click()
                time.sleep(10)
        else:
            try:
                see_more = wd.find_element(By.CLASS_NAME,'r0zKGf')
                if see_more:
                    print('dont has more')
                    break
            except:
                continue

        # move the result startpoint further down
        results_start = len(thumbnail_results)
    print(f"Found: {image_count} image, done!")
    print('{p:2.2f}%'.format(p=100*image_count/max_links_to_fetch))
    return image_urls, images_base64


def download_image(folder_path: str, url: str):
    try:
        # before = time.time()
        img_path, headers = request.urlretrieve(url)
        # now = time.time()
        # print('{i:2.2f} seconds'.format(i=now-before))
        img_data = open(img_path, 'rb').read()

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")
        return

    try:
        folder_path = os.path.join(folder_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path,511,True)
        file_path = os.path.join(
            folder_path, hashlib.sha1(img_data).hexdigest()[:10] + '.jpg')
        
        # convertendo para RGB para tirar o PNG ou gif
        image = Image.open(img_path)
        image = image.convert('RGB')
        image.save(file_path)
        
        # print(f"SUCCESS - saved as {file_path}")

    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")


def download_base64(folder_path: str, img_data: str):
    header, content = img_data.split(',')
    image_content = base64.decodebytes(content.encode())
    extension = header.split(';')[0].split('/')[1]
    if os.path.exists(folder_path):
        file_path = os.path.join(folder_path, hashlib.sha1(
            image_content).hexdigest()[:10] + '.{}'.format(extension))
    else:
        os.makedirs(folder_path)
        file_path = os.path.join(folder_path, hashlib.sha1(
            image_content).hexdigest()[:10] + '.{}'.format(extension))
    with open(file_path, "wb") as fh:
        fh.write(image_content)


if __name__ == '__main__':
    driver = webdriver.Chrome()

    for query in queries:
        links, base64s = fetch_image_and_download(query, max_links, driver)
        if not os.path.exists(OUTPUT_FOLDER_LINKS):
            os.makedirs(OUTPUT_FOLDER_LINKS)
        
    driver.quit()
