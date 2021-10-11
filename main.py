#!/usr/bin/python
# atmanos
# a program to retrieve pdfs from online repositories
# 2021-10-08ymd
import requests
import urllib
import sys
from urllib import parse
from tqdm import tqdm
from bs4 import BeautifulSoup


def urlDownload(url, loc, bar):
    loc = loc.replace('/', '_') # replacing file-unsafe chars
    if len(sys.argv)>=2:
        loc = sys.argv[1]+"/"+loc
    if(bar):
        response = requests.get(url, stream=True)
        blockSize = 1024 # each block
        with open(loc, 'wb') as file:
            progBar = tqdm(unit="iB",unit_scale=True,  total = int(response.headers['Content-Length']))
            for data in response.iter_content(chunk_size=blockSize):
                if data:
                    progBar.update(len(data))
                    file.write(data)
    else:
        response = requests.get(url)
        file = open(loc, 'wb')
        file.write(response)
        file.close()


class book:
    year, pages, localId = 0, 0, 0
    md5, source, authors, extension, title, publisher = "","", "", "", "", ""
    downloadUrl = ""
    def printInfo(self):
        print("%s| %s by %s |Filetype: %s| Year: %s | Publisher: %s" %
              (self.localId, self.title, ", ".join(self.authors.split(',')[:3]),
               self.extension, self.year, self.publisher
               ))
    def download(self):
        if(self.source == "libgen"):
            self.downloadUrl = getLibgenMirrorUrl(self.md5)
            fileExtension = self.downloadUrl.split('.')[-1]
        elif(self.source == "gutenberg"):
            self.downloadUrl = getGutenbergMirrorUrl(self.localId)
            fileExtension = chosenFormat.split(".")[0]
        urlDownload(self.downloadUrl, self.title + "." + fileExtension, True)

#libgen
def searchLibgen(searchTerm):
    searchTerm = urllib.parse.quote(searchTerm) # make search url-ready
    baseSearchUrl = "https://libgen.is/search.php?req="
    fullUrl = baseSearchUrl + searchTerm
    response = requests.get(fullUrl)
    soup = BeautifulSoup(response.content, 'html.parser')
    f = soup.find_all(class_="c")
    itr = 0
    curBooks = []
    for obj in f[0].contents:
        if(itr % 2 != 0): # have to skip every other
            cB = book()
            cB.source = "libgen"
            cB.localId = obj.contents[0].text
            cB.authors = obj.contents[2].text
            titleSrc = obj.contents[4]
            cB.title = next(titleSrc.a.children, None).text
            cB.publisher = obj.contents[6].text
            cB.year = obj.contents[8].text
            cB.pages = obj.contents[10].text
            cB.extension = obj.contents[16].text
            cB.md5 = obj.contents[18].a['href'].split('/')[-1]
            #cB.downloadUrl = getLibgenMirrorUrl(cB.md5)
            curBooks.append(cB)
        itr+=1 # have to skip every other
    #firstOb = f[0].contents[1]
    #print(firstOb.contents[1])
    return curBooks

def getLibgenMirrorUrl(md5):
    currentMirrorBase = "http://library.lol/main/"
    fullMirror = currentMirrorBase + md5
    response = requests.get(fullMirror)
    soup = BeautifulSoup(response.content, 'html.parser')
    downloadDiv = soup.find('div', {"id": "download"})
    downloadUrl = downloadDiv.a['href']
    return downloadUrl



#gutenberg
def searchGutenberg(searchTerm):
    searchTerm = urllib.parse.quote(searchTerm) # make search url-ready
    baseSearchUrl = "https://www.gutenberg.org/ebooks/search/?query="
    fullUrl = baseSearchUrl + searchTerm # + "&sort_order=release_date"
    response = requests.get(fullUrl)
    soup = BeautifulSoup(response.content, 'html.parser')
    results = soup.find_all(class_="booklink")
    curBooks = []
    for result in results:
        cB = book()
        cellContent = result.find(class_="cell content")
        cB.source = "gutenberg"
        try:
            cB.authors = cellContent.find_all("span", class_="subtitle")[0].text
        except:
            break
        cB.title = cellContent.find_all("span", class_="title")[0].text
        #cB.year = int(cellContent.find_all("span", class_="extra")[0].text.split(", ")[-1]) only usable w/ sorting by date
        cB.localId = result.a['href'].split('/')[-1]
        # cB.downloadUrl = getGutenbergMirrorUrl(cB.localId)
        curBooks.append(cB)
    return curBooks

def getGutenbergMirrorUrl(bookId):
    currentMirrorBase = "https://www.gutenberg.org/ebooks/"
    fullMirror = currentMirrorBase + bookId
    response = requests.get(fullMirror)
    soup = BeautifulSoup(response.content, 'html.parser')
    formats = soup.find_all("td", {"property" : "dcterms:format"})
    formatList = []
    print("List of available formats: ", end="")
    for form in formats:
        ext = form.a['href'].split("/")[-1]
        ext = ext.split("?")[0]
        ext = ".".join(ext.split(".")[1:])
        print(ext+"|", end="")
        formatList.append(ext)
        print()
    chosenFormat = input("Choose one of the available formats: ")
    if chosenFormat not in formatList:
        if("epub.images" in formatList):
            chosenFormat = "epub.images"
        elif("epub.noimages" in formatList):
            chosenFormat = "epub.noimages"
        print("Defaulting to "+chosenFormat)
    while chosenFormat not in formatList:
        print("List of available formats: ", end="")
        for form in formatList:
            print(form+"|", end="")
        print()
        chosenFormat = input("Choose one of the available formats: ")
    downloadUrl = fullMirror+"."+chosenFormat
    return downloadUrl



def userScan(results):
    if(len(results) != 0):
        for i in results:
            print("===================")
            i.printInfo()
            print("===================")
            ans = input("Download this book? [y/N]") or 'n'
            if(ans[0].lower() == "y"):
                print("Retrieving document...")
                i.download()
                exit()
    else:
        print("No results from this repository.")
        return 0

searchStr = input("Enter your search: ")
result = searchLibgen(searchStr)
userScan(result)
print("No results from libgen, trying Gutenberg...")
result = searchGutenberg(searchStr)
userScan(result)
