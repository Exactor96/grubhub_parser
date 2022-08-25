import asyncio
import csv
import sys
from typing import Any
from urllib.parse import urlparse

import aiohttp

AUTH_URL = 'https://api-gtm.grubhub.com/auth'
RESTAURANT_DATA_URL = ('https://api-gtm.grubhub.com/restaurants/{' +
                       'restaurant_id}?hideChoiceCategories=true&version=4&variationId=rtpFreeItems&' +
                       'orderType=standard&hideUnavailableMenuItems=true&hideMenuItems=false')
CLIENT_ID = 'beta_UmWlpstzQSFmocLy3h1UieYcVST'  # maybe can get via automated browser
MENU_MODIFIERS_URL = 'https://api-gtm.grubhub.com/restaurants/{restaurant_id}/menu_items/{menu_item_id}'


async def auth() -> dict[str, Any]:
    """Authorization function. Returns data after auth."""
    payload = {
        "brand": "GRUBHUB",
        "client_id": CLIENT_ID,
        "scope": "anonymous"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(AUTH_URL, json=payload) as response:
            data = await response.json()
            data = data.get('session_handle')
    if data:
        return data
    else:
        raise ValueError('No session data found after auth request')


async def get_modifiers(dish_id: int, restaurant_id: int,
                        session_data: dict[str, Any]) -> set[tuple[Any, Any, Any, Any, float]]:
    """Returns all modifiers for dish. Uses additional request."""
    async with aiohttp.ClientSession() as session:
        async with session.get(MENU_MODIFIERS_URL.format(
                menu_item_id=dish_id, restaurant_id=restaurant_id),
                headers={'authorization': f'Bearer {session_data["access_token"]}'}) as resp:
            response_data = await resp.json()

    # Modifier Group Name,Modifier Min,Modifier Max,Option Name,Option Price
    results = set()
    modifiers_data = response_data.get('choice_category_list')
    if modifiers_data:
        for modifier in modifiers_data:
            modifier_group_name = modifier['name']
            modifier_min = modifier.get('min_choice_options', 0)
            modifier_max = modifier.get('max_choice_options', 0)
            for option in modifier['choice_option_list']:
                modifier_name = option['description']
                modifier_price = option['price']['amount'] / 100
                results.add((modifier_group_name, modifier_min, modifier_max, modifier_name, modifier_price))
    return results


async def main():
    url = sys.argv[1]
    #url = 'https://www.grubhub.com/restaurant/impeckable-wings-901-nw-24th-st-san-antonio/3159434?hidemenuitem=false'

    parsed_url = urlparse(url)

    if parsed_url.hostname not in ['grubhub.com', 'www.grubhub.com']:  # Checking for valid url
        print('not a grubhub url')
        exit(1)

    try:
        restaurant_id = int(parsed_url.path.split('/')[-1])  # checking for restaurant id is an integer
    except ValueError:
        print(f"{parsed_url.path.split('/')[-1]} must be integer. Check your url")
        restaurant_id = 0
        exit(1)

    data_file = f'{restaurant_id}.csv'

    session_dict = await auth()

    async with aiohttp.ClientSession() as session:
        async with session.get(RESTAURANT_DATA_URL.format(restaurant_id=restaurant_id),
                               headers={'authorization': f'Bearer {session_dict["access_token"]}'}) as resp:
            restaurant_data = await resp.json()

    print(f"Restaurant Name: {restaurant_data['restaurant']['name']}")
    print(f"Restaurant Address Line 1: {restaurant_data['restaurant']['address']['street_address']}")
    print(f"Restaurant City : {restaurant_data['restaurant']['address']['locality']}")
    print(f"Restaurant State : {restaurant_data['restaurant']['address']['region']}")
    rating_data = restaurant_data['restaurant'].get('rating_bayesian10_point')
    if rating_data:
        print(f"Restaurant Stars: {rating_data['rating_value']}")
        print(f"Restaurant Review Count: {rating_data['rating_count']}")
    else:
        print(f"Restaurant Stars: 0")
        print(f"Restaurant Review Count: 0")

    menu_data = restaurant_data['restaurant']['menu_category_list']

    first_csv_section = set()
    second_csv_section = set()
    dish_ids = []
    for item in menu_data:
        category = item['name']
        menu_items = item['menu_item_list']
        # Category Name,Item Name,Item Description,Item Price
        for dish in menu_items:
            dish_id = dish['id']
            dish_name = dish['name']
            dish_description = dish['description']
            price = dish['price']['amount'] / 100
            if price == 0:
                price = dish['minimum_price_variation']['amount'] / 100
            first_csv_section.add((category, dish_name, dish_description, price))
            dish_ids.append((dish_id, restaurant_id))

    coros = [get_modifiers(dish_id, restaurant_id, session_dict) for dish_id, restaurant_id in dish_ids]
    results = await asyncio.gather(*coros)

    for result in results:
        if not result:
            continue
        result: set[Any]
        for item in result:
            second_csv_section.add(item)

    writer = csv.writer(open(data_file, 'w'))

    writer.writerow(('Category Name', 'Item Name', 'Item Description', 'Item Price'))
    writer.writerows(sorted(first_csv_section))  # can be modified on each row write
    writer.writerow(('Modifier Group Name', 'Modifier Min', 'Modifier Max', 'Option Name', 'Option Price'))
    writer.writerows(sorted(second_csv_section))


if __name__ == '__main__':
    asyncio.run(main())
