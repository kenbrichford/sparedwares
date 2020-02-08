import os
import re
import json
from datetime import datetime

import bleach

from django.conf import settings as dj_settings
from django.db.models import Q
from django.contrib.gis.geoip2 import GeoIP2
from geoip2.errors import AddressNotFoundError

from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping
from ebaysdk.exception import ConnectionError as EbayError

from products.models import Product
from refinements.models import Aspect, Filter

class ItemResponse:
    """
    This class returns ebay items using the ebay APIs

    Attributes:
        request (HttpRequest): Current HTTP Request object
        product (Product): Current product object
    """

    app_id = os.environ.get('EBAY_APPID')
    sort_by = {
        'best': ['BestMatch', ['Auction', 'AuctionWithBIN', 'FixedPrice']],
        'price': ['PricePlusShippingLowest', ['AuctionWithBIN', 'FixedPrice']],
        '-price': ['PricePlusShippingHighest', ['AuctionWithBIN', 'FixedPrice']],
        'time': ['EndTimeSoonest', ['Auction', 'AuctionWithBIN']],
        '-time': ['StartTimeNewest', ['AuctionWithBIN', 'FixedPrice']],
    }

    def __init__(self, request, product):
        self.request = request
        self.product = product

        # Get parameters from request URL and set default values if they are
        # empty or not compliant
        sort = self.request.GET.get('sort', 'best')
        self.sort = sort if sort in list(self.sort_by.keys()) else 'best'

        strict = self.request.GET.get('strict', True)
        self.strict = strict if strict in [True, False] else True

        keywords = self.request.GET.get('keywords', None)
        self.keywords = bleach.clean(keywords, strip=True) if keywords else None

        models = self.request.GET.getlist('model')
        self.models = Product.objects.filter(slug__in=models)

        try:
            self.page = int(self.request.GET.get('page', 1))
        except ValueError:
            self.page = 1

        # Get items used to narrow down products shown
        self.filters = self.get_filters()
        self.queries = self.get_query()
        self.aspects = self.get_aspects()

    def get_filters(self):
        """
        Get a list of applicable filter categories to use for narrowing down
        returned products

        Returns:
            QuerySet: List of filters
        """
        keys = list(dict(self.request.GET).keys())
        vals = [v for l in list(dict(self.request.GET).values()) for v in l]
        filters = Filter.objects.filter(
            Q(product__in=self.product.get_family()) & Q(group__slug__in=keys) &
            Q(slug__in=vals)
        )
        return filters

    def get_query(self):
        """
        Get and/or set the query search terms to use for returning products
        from ebay

        Returns:
            [string]: List of query strings
        """
        queries = [self.product.query] if self.product.query else []
        queries.extend([model.query for model in self.models if model.query])
        query_dict = {}
        for each_filter in list(self.filters.exclude(query='').values('group', 'query')):
            query_dict.setdefault(each_filter['group'], []).append(each_filter['query'])
        for query in list(query_dict.values()):
            queries.append('(%s)' % ','.join(query) if len(query) > 1 else query[0])
        if self.keywords:
            queries.append(self.keywords)
        return queries

    def get_aspects(self):
        """
        Get a list of applicable filter values related to the list of filters

        Returns:
            QuerySet: List of aspect objects
        """
        aspect_set = Aspect.objects.filter(
            Q(product__in=self.product.get_ancestors(include_self=True)) |
            Q(product__in=self.models) | Q(filter__in=self.filters)
        )
        aspects = []
        for aspect in aspect_set:
            val = aspect.value.split('|')
            if not self.strict and not aspect.is_strict:
                val.append('Not Specified')
            aspects.append({'aspectName': aspect.name, 'aspectValueName': val})
        return aspects

    def get_client_ip(self):
        """
        Get the IP address of the user

        Returns:
            string: IP Address
        """
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[-1].strip()
        else:
            ip_address = self.request.META.get('REMOTE_ADDR')
        return ip_address

    def find_settings(self):
        """
        Get the settings used within the Ebay Finding API

        Returns:
            dict: A dictionary of setting keys and values
        """
        find_settings = {
            'categoryId': self.product.category.ebay_cat,
            'aspectFilter': self.aspects,
            'itemFilter': [
                {'name': 'Condition', 'value': [
                    '1000', '1500', '2000', '2500', '3000', '4000', '5000',
                    '6000'
                ]},
                {'name': 'FeedbackScoreMin', 'value': 10},
                {'name': 'HideDuplicateItems', 'value': 'true'},
                {'name': 'ListingType', 'value': self.sort_by[self.sort][1]},
                {'name': 'LocatedIn', 'value': 'US'},
                {'name': 'MaxQuantity', 'value': 1},
            ],
            'outputSelector': ['SellerInfo'],
            'affiliate': {'networkId': '9', 'trackingId': '5338417073'},
            'paginationInput': {'entriesPerPage':  20, 'pageNumber': self.page},
            'sortOrder': self.sort_by[self.sort][0],
        }

        if self.queries:
            find_settings['keywords'] = ' '.join(self.queries)
            find_settings['descriptionSearch'] = 'true'

        try:
            zipcode = GeoIP2().city(self.get_client_ip())['postal_code']
            find_settings['buyerPostalCode'] = zipcode
        except AddressNotFoundError:
            pass

        return find_settings

    def call_ebay(self, api, method, settings):
        """
        Set the name of cached file, and return Ebay data response.

        Parameters:
            api: Ebaysdk connection method
            method (string): Ebay API search type
            settings (dict): Settings dictionary

        Returns:
            dict: Ebay item data
        """
        if api == Finding:
            cache_name = 'cache/%s-%d-find.json' % (self.product.slug, self.page)
        else:
            cache_name = 'cache/%s-%d-shop.json' % (self.product.slug, self.page)
        cache_path = os.path.join(dj_settings.BASE_DIR, cache_name)

        response = check_cache(cache_path)

        if not response:
            try:
                response = api(appid=self.app_id, https=True, config_file=None).execute(
                    method, settings
                ).dict()
                cache_file = open(cache_path, 'w+')
                cache_file.write(json.dumps(response))
                cache_file.close()
            except EbayError as error:
                return error.response.dict()

        return response

    def parse_data(self, items, item, details):
        """
        Extract important data from Ebay response

        Parameters:
            items (int): Total number of items returned
            item (dict): Single ebay listing
            details (dict): More listing information from by Ebay Shopping API
        """
        buy_it_now = 'convertedBuyItNowPrice'
        info = item['listingInfo']

        if self.sort in ['best', 'time'] or buy_it_now not in info:
            cur = item['sellingStatus']['convertedCurrentPrice']
            price = "{0:.2f}".format(float(cur['value']))
            auction_type = 'Auction' if 'Auction' in info['listingType'] else 'Fixed'
        else:
            price = "{0:.2f}".format(float(info[buy_it_now]['value']))
            auction_type = 'Fixed/Auction'

        if 'shippingServiceCost' in item['shippingInfo']:
            ship = item['shippingInfo']['shippingServiceCost']
            shipping = '{0:.2f}'.format(float(ship['value']))
            shipping = 'free' if shipping == '0.00' else shipping
        else:
            shipping = 'variable'

        if item['condition']['conditionId'] in ['1000', '1500']:
            condition = 'New'
        elif item['condition']['conditionId'] in ['2000', '2500']:
            condition = 'Refurb'
        else:
            condition = 'Used'

        if details:
            if 'ConditionDescription' in details:
                text = details['ConditionDescription']
            elif 'Description' in details and details['Description']:
                text = details['Description']
            else:
                text = None
            images = details['PictureURL'] if 'PictureURL' in details else None
        else:
            text = None
            images = None
        text = (text[:1000] + '...') if text and len(text) > 1000 else text

        end = re.findall(r'[\d]+', item['sellingStatus']['timeLeft'])
        end = '%sd %sh %sm %ss' % tuple(end)

        items['list'].append({
            'url': item['viewItemURL'], 'images': images, 'type': auction_type,
            'title': item['title'], 'price': price, 'shipping': shipping,
            'condition': condition, 'text': text, 'end': end,
            'location': ', '.join(item['location'].split(',')[:2]),
            'seller': {
                'name': item['sellerInfo']['sellerUserName'][:20],
                'percent': item['sellerInfo']['positiveFeedbackPercent'],
                'ratings': item['sellerInfo']['feedbackScore']
            }
        })

    def get_items(self):
        """
        Initiates Ebay pull request

        Returns:
            dict: Item information or error
        """
        find = self.call_ebay(Finding, 'findItemsAdvanced', self.find_settings())
        if find['ack'] == 'Success':
            items = {
                'count': int(find['paginationOutput']['totalEntries']),
                'list': []
            }
            if items['count'] > 0:
                ids = [i['itemId'] for i in find['searchResult']['item']]
                shop_settings = {
                    'ItemID': ids, 'IncludeSelector': 'TextDescription'
                }
                shop = self.call_ebay(Shopping, 'GetMultipleItems', shop_settings)
                for item in find['searchResult']['item']:
                    if items['count'] > 1:
                        details = next(
                            (i for i in shop['Item'] if i['ItemID'] == item['itemId']),
                            None
                        )
                    else:
                        details = shop['Item']
                    self.parse_data(items, item, details)
            return items
        return {'error': find['errorMessage']}

def check_cache(path):
    """
    Check if a cached file exists. Get the file's update timestamp, and see
    if the cached file has been updated in the last hour.

    Returns:
        dict: Cached response if less than an hour old or None
    """
    result = None

    if os.path.exists(path):
        with open(path) as cache_file:
            data = json.load(cache_file)
            time_string = data["timestamp"] if "timestamp" in data else data["Timestamp"]
            cache_time = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S.%fZ")
            if (datetime.utcnow() - cache_time).total_seconds() < 3600:
                result = data

    return result
