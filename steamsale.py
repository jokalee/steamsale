#!/usr/bin/env python

"""A script that parses your Steam wishlist and finds discounts"""

from __future__ import print_function
from __future__ import unicode_literals
import sys
import requests
from re import sub
from pprint import pprint
from getopt import getopt, GetoptError
from bs4 import BeautifulSoup
from termcolor import colored


class Wishlist(object):
    """Class representing a Steam wishlist"""

    def __init__(self, steam_id):
        if steam_id.isdigit():
            url = 'http://steamcommunity.com/profiles/{}/wishlist'.format(
                steam_id)
        else:
            url = 'http://steamcommunity.com/id/{}/wishlist'.format(steam_id)
        req = requests.get(url)
        self.soup = BeautifulSoup(req.content, 'html.parser')
        self.tag = None
        self.items = []

    def _find_price(self):
        """Find default price or None"""
        price = self.tag.find(attrs={'class': 'price'})
        return price.text.strip() if price and price.text else None

    def _find_discount_pct(self):
        """Returns discount percentage or None"""
        discount_pct = self.tag.find(attrs={'class': 'discount_pct'})
        return discount_pct.text.strip() if discount_pct else None

    def _find_org_price(self):
        """Returns original price or None"""
        org_price = self.tag.find(attrs={'class': 'discount_original_price'})
        return org_price.text.strip() if org_price else None

    def _find_final_price(self):
        """Returns discounted final price or None"""
        final_price = self.tag.find(attrs={'class': 'discount_final_price'})
        return final_price.text.strip() if final_price else None

    def _find_url(self):
        """Returns game URL or None"""
        a = self.tag.find('a')
        if a is not None:
            return a.get('href', None)
        return None

    def find_items(self, only_sale=False, percent_off=0):
        """Parse and find wishlist items"""
        # Find divs containing wishlist items
        item_tags = self.soup.findAll(attrs={'class': "wishlistRow"})
        for item_tag in item_tags:
            self.tag = item_tag.find(attrs={'class': 'gameListPriceData'})
            title = item_tag.find('h4').text
            url = self._find_url()
            app_id = item_tag['id'].split('_')[1]
            default_price = self._find_price()
            discount_pct = self._find_discount_pct()
            original_price = self._find_org_price()
            final_price = self._find_final_price()

            if only_sale and not discount_pct:
                continue

            if percent_off > 0:
                if not discount_pct:
                    continue

                discount_amount = int(discount_pct
                                      .replace('-', '')
                                      .replace('%', ''))
                if discount_amount < percent_off:
                    continue

            self.items.append({
                'app_id': app_id,
                'url': url,
                'title': title,
                'discount_pct': discount_pct,
                'original_price': original_price,
                'final_price': default_price or final_price
            })

        return self.items

    def prettify(self, colors):
        """Create a string representation of items"""
        lines = []
        for item in self.items:
            if item['discount_pct']:
                lines.append('{} is on sale for {}, down from {} ({})'
                             .format(colored(item['title'], attrs=['bold']),
                                     colored(item['final_price'], 'green'),
                                     colored(item['original_price'], 'red'),
                                     colored(item['discount_pct'], 'cyan')))
            elif item['final_price']:
                name = colored(item['title'], attrs=['bold'])
                price = colored(item['final_price'].strip(), 'yellow')
                lines.append(
                    '{} is not on sale and costs {}'.format(name, price))
            else:
                lines.append('{} has no price (yet?)'.format(
                    colored(item['title'], attrs=['bold'])))
        out = '\n'.join(lines)
        return out if colors else sub(r'\x1b\[\d+m', '', out)  # Hack!


def usage():
    """Display usage"""
    print('usage: {} [OPTIONS] steam_id'
          '\n -h, --help\t\tDisplay usage'
          '\n -s, --sale\t\tShow only items that are on sale'
          '\n -p, --pct_off NUM\tShow sale items with this discount or greater'
          '\n -c, --colors\t\tUse colors in output'
          '\n -d, --dump\t\tDump dictionary'.format(sys.argv[0]))
    sys.exit(1)


def main():
    """Parse argv, find items and print them to stdout"""
    try:
        opts, args = getopt(sys.argv[1:], 'hdsp:c', ['help', 'dump', 'sale',
                                                     'pct_off=', 'colors'])
    except GetoptError as err:
        print(str(err))
        usage()
    if not args:
        usage()

    steam_id = args[0]
    only_sale = False
    percent_off = 0
    colors = False
    dump = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-s', '--sale'):
            only_sale = True
        elif opt in ('-p', '--pct_off'):
            if not arg.isdigit() or int(arg) < 1 or int(arg) > 99:
                print("--pct_off value must be a number between 1 and 99")
                usage()
            percent_off = int(arg)
        elif opt in ('-c', '--colors'):
            colors = True
        elif opt in ('-d', '--dump'):
            dump = True

    wishlist = Wishlist(steam_id)
    items = wishlist.find_items(only_sale, percent_off)
    if dump:
        pprint(items)
    else:
        print(wishlist.prettify(colors))


if __name__ == '__main__':
    main()
