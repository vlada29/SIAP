import scrapy
import os
import json
import requests

class BookSpider(scrapy.Spider):
    name = "youGloriousLittleBookSpider"
    start_urls = [
        'https://www.goodreads.com/book/popular_by_date/2018/'
    ]

    def parse(self,response):
        base_url = 'https://www.goodreads.com'
        for book in response.css('a.bookTitle::attr(href)').extract():
            next_page = base_url+book
            yield scrapy.Request(next_page, callback = self.parseBook)

    def parseBook(self,response):
        currDir = os.getcwd()

        self.review = ''
        self.bookUrl = 'https://images.gr-assets.com/books/'

        newBook = dict()

        def extractTitle(query):
            newBook['title'] = response.css(query).extract_first().strip()
            return newBook['title']
        def extractAuthor(query):
            newBook['author'] = response.css(query).extract_first().strip()
            return newBook['author']
        def extractRating(query):
            newBook['rating'] = response.css(query).extract_first().strip()
            return newBook['rating']
        def extractVotes(query):
            newBook['votes'] = response.css(query).extract_first().strip()
            return newBook['votes']
        def extractDetails(query):
            detailsText = response.css(query).extract()
            firstLine = detailsText.pop(0)
            add = False
            for dt in detailsText:
                if dt.startswith(firstLine):
                    add = True
                if add:
                    self.review = self.review + dt
            
            return ''
        def extractImage(query):
            firstNoFull = response.css(query).extract()[8]
            firstNo = firstNoFull.split('/')[7]
            secondNoFull = firstNoFull.split('/')[8]
            secondNo = secondNoFull.split('.')[0]
            self.bookUrl = self.bookUrl + firstNo[:-1]+'l/'+secondNo+'.jpg'
            return ''
        def extractPub(query):
            fullDetails = response.css(query).extract()[1]
            publisher = fullDetails.split('by')[1].strip()
            datePublished = fullDetails.split('by')[0].strip()
            newBook['datePublished'] = datePublished
            newBook['publisher'] = publisher
            return ''
        def extractIsbn(query):
            isbn = ''
            
            try:
                isbn = response.xpath(query).extract_first()
            except:
                isbn = '1'

            if isbn is None:
                print('Drugicpaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
                isbn = response.css('div.infoBoxRowItem::text').extract()[1].strip()

            newBook['ISBN'] = isbn
            return newBook['ISBN']
        def extractAwards(query):
            awards = []
            try:
                awards = response.xpath(query).extract()
            except:
                awards = []
            newBook['awards'] = awards
            return awards
            

        yield {
            'title' : extractTitle('span.fn::text'),
            'author' : extractAuthor('div.authorName__container a.authorName span::text'),
            'rating' : extractRating('span.value span.average::text'),
            'votes' : extractVotes('a.gr-hyperlink span.votes::text'),
            'details' : extractDetails('div.readable span::text'),
            'image': extractImage('meta::attr(content)'),
            'publication' : extractPub('div.uitext div.row::text'),
            'isbn' : extractIsbn('//div[@itemprop="isbn"]/text()'),
            'awards' : extractAwards('//div[@itemprop="awards"]/a/text()')
        }

        path = currDir + '/books/2018/'+newBook['title']

        try:  
            os.mkdir(path)
        except OSError:  
            print ("Creation of the directory %s failed" % path)

        detailsFilename = path + '/details.json'

        with open(detailsFilename, 'w') as fp:
            json.dump(newBook, fp, sort_keys=True, indent=4)

        reviewFilename = path + '/review.txt'

        with open(reviewFilename, "w") as text_file:
            text_file.write(self.review)

        bookImageFilename = path + '/cover.jpeg'

        f = open(bookImageFilename,'wb')
        f.write(requests.get(self.bookUrl).content)
        f.close()
