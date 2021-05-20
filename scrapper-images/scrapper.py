# coding: utf-8
import sys
import argparse
from urllib import request
import base64
import hashlib
import socket
from selenium import webdriver
import time
import os

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


def fetch_image_and_download(query: str, max_links_to_fetch: int, wd: webdriver, sleep_between_interactions: int = 1):
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

    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
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
                actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
                for actual_image in actual_images:
                    src = actual_image.get_attribute('src')
                    # print(len(src))
                    if src and 'http' in src:
                        image_urls.add(src)
                        download_image(output_folder, src)
                    # elif 'data:' in src:
                    #     images_base64.add(src)
                    #     download_base64(output_folder, src)
            except:
                print('error to find img.n3VNCb')

            image_count = len(image_urls) + len(images_base64)
            print('{p:2.2f}%'.format(p=100*image_count/max_links_to_fetch))
            sys.stdout.write("\033[F")  # Cursor up one line

            if image_count >= max_links_to_fetch:
                print(f"Found: {image_count} image, done!")
                return image_urls, images_base64

        has_more = wd.find_element_by_css_selector('.YstHxe')
        if (has_more and not 'none' in has_more.get_attribute('style')):
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                wd.execute_script(
                    "document.querySelector('.mye4qd').click();")
                time.sleep(10)
        else:
            try:
                see_more = wd.find_element_by_css_selector('span.r0zKGf')
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

    try:
        folder_path = os.path.join(folder_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(
            folder_path, hashlib.sha1(img_data).hexdigest()[:10] + '.jpg')
        with open(file_path, 'wb') as f:
            f.write(img_data)
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
    wd = webdriver.Chrome(executable_path=DRIVER_PATH)

    for query in queries:
        wd.get('https://google.com')
        search_box = wd.find_element_by_css_selector('input.gLFyf')
        search_box.send_keys(query)
        links, base64s = fetch_image_and_download(query, max_links, wd)
        if not os.path.exists(OUTPUT_FOLDER_LINKS):
            os.makedirs(OUTPUT_FOLDER_LINKS)
        filepath_links = os.path.join(OUTPUT_FOLDER_LINKS, query)
        with open(filepath_links, 'a') as f:
            for link in links:
                f.write("%s\n" % link)
    wd.quit()
