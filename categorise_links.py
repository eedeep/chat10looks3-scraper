#!/usr/bin/env python

import argparse
from chatscraper import ChatScraper

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape and categorise chat10looks3 episode links.')
    parser.add_argument('episode_numbers', metavar='N', type=int, nargs='+',
                       help='Episode numbers to scrape and categorise.')
    args = parser.parse_args()

    cs = ChatScraper('http://www.chat10looks3.com/podcast/?format=rss')
    cs.print_list(args.episode_numbers)
