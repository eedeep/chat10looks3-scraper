import urllib
from unittest import TestCase

from chatscraper import ChatScraper
from bs4 import BeautifulSoup


class ChatScraperTests(TestCase):
    RSS_FEED_URL = 'http://www.chat10looks3.com/podcast/?format=rss'

    def setUp(self):
       self.chat_scraper = ChatScraper(self.RSS_FEED_URL)

    def test_feed_exists(self):
       self.assertTrue(self.chat_scraper.feed['feed']['title'])

    def test_entry_link_is_valid_url(self):
       self.assertIsInstance(
           urllib.parse.urlparse(self.chat_scraper.feed.entries[0].link),
           urllib.parse.ParseResult
       )

    def test_parse_episode_page(self):
        page = self.chat_scraper.parse_episode_page(
            self.chat_scraper.feed.entries[0].link
        )
        self.assertIsInstance(page, BeautifulSoup)

    def test_get_show_notes_links(self):
        links = self.chat_scraper.get_show_notes_links_for_episode(
            self.chat_scraper.feed.entries[0].link
        )
        self.assertIsInstance(links, dict)
        self.assertTrue(len(list(links.values())) > 0)

    def test_categorise_links(self):
        links = self.chat_scraper.get_show_notes_links_for_episode(
            self.chat_scraper.parse_episode_page(self.chat_scraper.feed.entries[0].link)
        )
        categorised_links_dict = self.chat_scraper.categorise_links(links)
        self.assertTrue('film' in categorised_links_dict)
        self.assertTrue('book' in categorised_links_dict)
        self.assertTrue('podcast' in categorised_links_dict)
        self.assertTrue('music' in categorised_links_dict)
        self.assertTrue('misc' in categorised_links_dict)

    def test_sorted_category_items(self):
        unsorted_category_items = [
            {'link_text': 'B', 'url': 'https://wwww.bbc.com'},
            {'link_text': 'C', 'url': 'https://wwww.cbc.com'},
            {'link_text': 'A', 'url': 'https://wwww.abc.com'},
        ]
        sorted_category_items = self.chat_scraper._sorted_category_items(unsorted_category_items)
        self.assertEqual(
            [{'link_text': 'A', 'url': 'https://wwww.abc.com'},
             {'link_text': 'B', 'url': 'https://wwww.bbc.com'},
             {'link_text': 'C', 'url': 'https://wwww.cbc.com'}],
            sorted_category_items
        )

    def test_is_book(self):
        books = [
            ('The Great Gatsby', 'https://www.booktopia.com.au/the-great-gatsby-f-scott-fitzgerald/prod9780199536405.html'),
            ('The Great Gatsby', 'https://www.booktopia.com.au/the-great-gatsby-f-scott-fitzgerald/prod9780199536405.html'),
            ('Midnight\'s Children', 'https://www.bookdepository.com/Midnights-Children-Salman-Rushdie/9780099511892'),
            ('A Fraction of The Whole', 'https://www.amazon.com/Fraction-Whole-Steve-Toltz/dp/0385521731/?tag=animaideas-20'),
            ('The Wife Drought ebook', 'https://www.amazon.com.au/Wife-Drought-Annabel-Crabb-ebook/dp/B00L0OOV4Q'),
            ('Rachel Allen author page', 'https://www.amazon.com/Rachel-Allen/e/B001JRZGT8/?tag=animaideas-20'),
        ]
        for book in books:
            self.assertTrue(
                self.chat_scraper._is_book(book[0], book[1])
            )

        # Test movies on amazon aren't deemed a TV show
        films = [
            ('Die Hard', 'https://www.amazon.com/Die-Hard-Bruce-Willis/dp/B000SZK41M/?tag=animaideas-20'),
            ('Misery', 'https://www.amazon.com/Misery-James-Caan/dp/B002QUWYWE/?tag=animaideas-20'),
            ('The Comfort of Strangers DVD', 'https://www.amazon.com/Comfort-Strangers-Region-2/dp/B00015N57O/?tag=animaideas-20'),
        ]
        for film in films:
            self.assertFalse(self.chat_scraper._is_book(film[0], film[1]))

    def test_is_tv_show(self):
        tv_shows = [
            ('The Handmaid\'s Tale', 'https://www.rottentomatoes.com/tv/the_handmaid_s_tale/s01/'),
            ('The Handmaid\'s Tale S01 Ep01', 'https://www.rottentomatoes.com/tv/the_handmaid_s_tale/s01/e01'),
            ('Mad as Hell', 'http://www.abc.net.au/tv/programs/shaun-micallefs-mad-as-hell/'),
            ('The Affair', 'https://www.amazon.com/Episode-2/dp/B00S949GPO/?tag=animaideas-20'),
            ('Veep', 'https://www.amazon.com/Fundraiser/dp/B00BS4N946/?tag=animaideas-20'),
            ('The Americans', 'https://www.amazon.com/Pilot/dp/B00B8QQVEE'),
        ]
        for tv_show in tv_shows:
            self.assertTrue(
                self.chat_scraper._is_tv_show(tv_show[0], tv_show[1])
            )

        # Test a movie on RT isn't deemed a TV show
        self.assertFalse(
            self.chat_scraper._is_tv_show('The Departed', 'https://www.rottentomatoes.com/m/departed/')
        )

    def test_is_podcast(self):
        podcasts = [
            ('Richard Fidler', 'http://www.abc.net.au/radio/programs/conversations/conversations-george-saunders-(r)/9045402'),
        ]
        for podcast in podcasts:
            self.assertTrue(
                self.chat_scraper._is_podcast(podcast[0], podcast[1])
            )

    def test_is_music(self):
        musics = [
            ('Them Crooked Vultures', 'https://www.amazon.com/Them-Crooked-Vultures/dp/B002TUU2XE/?tag=animaideas-20'),
            ('Lorde Royals', 'https://www.amazon.com/Them-Crooked-Vultures/dp/B002TUU2XE/?tag=animaideas-20://www.amazon.com/Royals/dp/B00FAEQ22G/?tag=animaideas-20'),
        ]
        for music in musics:
            self.assertTrue(
                self.chat_scraper._is_music(music[0], music[1])
            )

        # Test a TV show on amazon isn't deemed music
        self.assertFalse(
            self.chat_scraper._is_music('Veep', 'https://www.amazon.com/Fundraiser/dp/B00BS4N946/?tag=animaideas-20')
        )

    def test_print_list_for_single_episode(self):
        self.chat_scraper.print_list([18])

    def test_print_list_for_multiple_episodes(self):
        self.chat_scraper.print_list([16,17])
