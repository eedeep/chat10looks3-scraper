import urllib
import validators
import requests
import feedparser
import logging
from time import sleep
from collections import defaultdict

from bs4 import BeautifulSoup
from validators import ValidationFailure
from requests.exceptions import ConnectionError

logger = logging.getLogger(__name__)

class ChatScraper(object):

    BASE_EPISODES_PAGE_URL = 'https://www.chat10looks3.com/podcast'

    KNOWN_BOOK_DIRECTORY_SITES = [
        'www.booktopia.com',
        'www.booktopia.com.au',
        'www.bookdepository.com',
        'www.bookdepository.com.au',
        'www.readings.com.au',
    ]

    AMAZON_URLS = [
        'www.amazon.com',
        'www.amazon.com.au',
    ]
    ROTTEN_TOMATOES_URL = 'www.rottentomatoes.com'
    ABC_AUSTRALIA_URL = 'www.abc.net.au'

    KNOWN_FILM_DIRECTORY_SITES = [
        'www.imdb.com',
        ROTTEN_TOMATOES_URL,
    ]

    KNOWN_TV_SHOW_DIRECTORY_SITES = [
        'www.stan.com.au',
        'www.netflix.com',
        'iview.abc.net.au',
        'tenplay.com.au',
        'www.funnyordie.com',
        'www.sbs.com.au',
    ]

    KNOWN_PODCAST_DIRECTORY_SITES = [
        'itunes.apple.com',
        'www.wbez.org',
        'www.npr.org',
        'libsyn.com',
        'www.thisamericanlife.org',
        'www.gimletmedia.com',
        'www.wnycstudios.org',
        'thedollop.net',
        'thedollop.libsyn.com',
        'www.mydadwroteaporno.com',
        'revisionisthistory.com',
    ]

    KNOWN_WEB_CLIP_SITES = [
        'www.youtube.com',
        'www.vimeo.com',
        'www.dailymotion.com',
    ]

    PODCAST_URL_PATH_FINGERPRINTS = [
        'podcast',
        'radio',
    ]


    def __init__(self, rss_feed_url):
        self.feed = feedparser.parse(rss_feed_url)

    def parse_page(self, page_url):
        """Parse an episode page with beautifulsoup"""
        headers = {
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'
        }
        page = requests.get(page_url, headers=headers)
        return BeautifulSoup(page.content, "html.parser")

    def get_show_notes_links_for_episode(self, episode_page_url):
        valid_links = dict()
        episode_page = self.parse_page(episode_page_url)
        try:
            h3_sibling = episode_page.h3.next_sibling.find_all('a')
            if h3_sibling.name == 'ul':
                show_notes_links = h3_sibling.find_all('a')
            elif h3_sibling.name == 'p':
                show_notes_links = h3_sibling.next_sibling.find_all('a')
            else:
                raise Exception('Cannot find show notes links')
        except AttributeError:
            show_notes_links = episode_page.ul.find_all('a')

        for a in show_notes_links:
            item_url = a['href']
            if validators.url(item_url):
                # Some urls involve a redirect, so follow that using requests
                # to get the real final url
                try:
                    r = requests.get(item_url)
                    valid_links[a.text] = r.url
                except ConnectionError:
                    valid_links[a.text] = item_url
            else:
                logger.info("Not a valid URL, ignoring: {}".format(item_url))
        return valid_links

    def _is_on_known_site(self, url, known_sites):
        url_parts = urllib.parse.urlparse(url)
        return url_parts.netloc in known_sites

    def _is_film(self, link_text, url):
        url_parts = urllib.parse.urlparse(url)
        if url_parts.netloc == self.ROTTEN_TOMATOES_URL:
            if '/m/' in url_parts.path:
                return True
            return False
        elif self._is_on_known_site(url, self.KNOWN_FILM_DIRECTORY_SITES):
            return True
        elif self._is_amazon_film(link_text, url):
            return True
        return False

    def _is_tv_show(self, link_text, url):
        url_parts = urllib.parse.urlparse(url)
        if url_parts.netloc in [self.ROTTEN_TOMATOES_URL, self.ABC_AUSTRALIA_URL]:
            if '/tv/' in url_parts.path:
                return True
            return False
        elif self._is_on_known_site(url, self.KNOWN_TV_SHOW_DIRECTORY_SITES):
            return True
        elif self._is_amazon_tv_show(link_text, url):
            return True
        return False

    def _is_amazon_tv_show(self, link_text, url):
        url_parts = urllib.parse.urlparse(url)
        if url_parts.netloc in self.AMAZON_URLS:
            page = self.parse_page(url)

            page_data = page.find(id='pageData')
            try:
                sub_page_type = page_data['data-sub-page-type']
                if sub_page_type == 'TVSeason':
                    return True
            except TypeError:
                pass

        return False

    def _is_amazon_film(self, link_text, url):
        url_parts = urllib.parse.urlparse(url)
        if url_parts.netloc in self.AMAZON_URLS:
            page = self.parse_page(url)

            page_data = page.find(id='pageData')
            try:
                sub_page_type = page_data['data-sub-page-type']
                if sub_page_type == 'Movie':
                    return True
            except TypeError:
                pass

            # Different type of movies page
            try:
                store_id = page.find(id='storeID')
                if store_id and store_id['value'] == 'movies-tv':
                    return True
            except TypeError:
                pass

        return False

    def _is_amazon_book(self, link_text, url):
        url_parts = urllib.parse.urlparse(url)
        if url_parts.netloc in self.AMAZON_URLS:
            page = self.parse_page(url)
            store_id = page.find(id='storeID')
            try:
                if store_id and store_id['value'] == 'books':
                    return True
            except TypeError:
                pass

            # It could be an ebook...
            if page.find(id='booksTitle'):
                return True

            # It could be an author's page...
            if page.find('img', class_='ap-author-image'):
                return True

        return False

    def _is_amazon_music(self, link_text, url):
        url_parts = urllib.parse.urlparse(url)
        if url_parts.netloc in self.AMAZON_URLS:
            page = self.parse_page(url)
            store_id = page.find(id='storeID')
            try:
                if store_id and store_id['value'] in ['music', 'dmusic']:
                    return True
            except TypeError:
                pass

        return False

    def _is_book(self, link_text, url):
        if self._is_on_known_site(url, self.KNOWN_BOOK_DIRECTORY_SITES):
            return True
        if self._is_amazon_book(link_text, url):
            return True
        return False

    def _is_podcast(self, link_text, url):
        if self._is_on_known_site(url, self.KNOWN_PODCAST_DIRECTORY_SITES):
            return True

        url_parts = urllib.parse.urlparse(url)
        for fingerprint in self.PODCAST_URL_PATH_FINGERPRINTS:
            fingerprint = fingerprint.lower()
            if fingerprint in url_parts.path.lower() or \
                fingerprint in url_parts.netloc.lower() or \
                fingerprint in link_text.lower():
                return True

        return False

    def _is_web_clip(self, link_text, url):
        if self._is_on_known_site(url, self.KNOWN_WEB_CLIP_SITES):
            return True
        return False

    def _is_music(self, link_text, url):
        if self._is_amazon_music(link_text, url):
            return True
        return False

    def _is_seven_thirty_interview(self, link_text, url):
        if url.startswith('http://www.abc.net.au/7.30/'):
            return True
        return False

    def categorise_links(self, links):
        results = dict(
            film=[], book=[], podcast=[], web_clip = [], music=[], tv_show=[]
        )
        notsure_list = []
        for link_text, url in links.items():
            categorised = False
            for item_type in results.keys():
                category_type_test_func_name = '_is_{}'.format(item_type)
                if getattr(self, category_type_test_func_name)(link_text, url):
                    results[item_type].append({'link_text': link_text, 'url': url})
                    categorised = True
                    break

            if not categorised:
                notsure_list.append({'link_text': link_text, 'url': url})

        results['misc'] = notsure_list
        return results

    def _sorted_category_items(self, category_items):
        return sorted(category_items, key=lambda k: k['link_text'])

    def print_category_items(self, all_items, category_name=''):
        category_names = list(category_name) if category_name else list(all_items.keys())

        for category_name in category_names:
            print('* {}:'.format(category_name.replace('_', ' ')))
            if all_items[category_name]:
                for categorised_item in self._sorted_category_items(all_items[category_name]):
                    print('     - {} [{}]'.format(categorised_item['link_text'], categorised_item['url']))
            else:
                print('    - nothing found')

    def print_list(self, episode_numbers=[]):
        episode_urls = []
        if not episode_numbers:
            episode_urls = [e.link for e in self.feed.entries]
        else:
            for episode_number in episode_numbers:
                episode_urls.append('{}/ep{}'.format(self.BASE_EPISODES_PAGE_URL, episode_number))

        links_by_episode = {}
        for episode_url in episode_urls:
            links_by_episode[episode_url] = self.categorise_links(
                self.get_show_notes_links_for_episode(episode_url)
            )
            sleep(5)

        all_show_notes = defaultdict(list)
        for episode_link, categorised_show_notes_links in links_by_episode.items():
            for category in categorised_show_notes_links:
                all_show_notes[category].extend(categorised_show_notes_links[category])

        self.print_category_items(all_show_notes)
