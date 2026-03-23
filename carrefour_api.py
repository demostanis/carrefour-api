import requests
import json
import os
import time


class CarrefourAPI:
    BASE_URL = "https://www.carrefour.fr/api"
    SEARCH_URL = f"{BASE_URL}/marketing/search_panel"
    CART_URL = f"{BASE_URL}/cart"
    COOKIE_FILE = "carrefour_session.json"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.carrefour.fr",
            }
        )
        self.load_session()

    def load_session(self):
        """Loads cookies from a local file."""
        if os.path.exists(self.COOKIE_FILE):
            with open(self.COOKIE_FILE, "r") as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)

    def save_session(self):
        """Saves current session cookies to a local file."""
        with open(self.COOKIE_FILE, "w") as f:
            json.dump(self.session.cookies.get_dict(), f)

    def _ensure_fresh_session(self):
        """
        Internal check: if a request fails with 403 (Cloudflare) or 401,
        this would be the place to trigger a browser-based refresh.
        In this environment, you should use the browser subagent if you get a 403.
        """
        pass

    def search(self, query):
        """
        Search for products using the organic results.
        If headers are correct, Carrefour returns JSON directly.
        """
        url = f"https://www.carrefour.fr/s?q={query}"
        # Ensure we have headers that trigger JSON response
        headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
        }
        response = self.session.get(url, headers=headers)

        if response.status_code == 403:
            raise Exception(
                "Cloudflare blocking. Please refresh tokens using the browser."
            )

        response.raise_for_status()

        try:
            data = response.json()
            # The structure is {"data": [...], "meta": {...}}
            items = data.get("data", [])

            # These items already have the 'attributes' structure expected by extract_product_info
            # So we can just return them as a pseudo-placement
            self.save_session()
            return [{"products": items}]
        except Exception as e:
            # Fallback to HTML scraping if JSON parse fails
            import re

            match = re.search(
                r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});", response.text, re.DOTALL
            )
            if not match:
                match = re.search(
                    r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})($|(?=<))",
                    response.text,
                    re.DOTALL,
                )

            if not match:
                raise Exception(
                    f"Failed to parse JSON and could not find __INITIAL_STATE__. Error: {e}"
                )

            state = json.loads(match.group(1))
            vuex = state.get("vuex", {})
            items = vuex.get("search", {}).get("results", {}).get("items", [])

            if not items:
                items = state.get("search", {}).get("results", {}).get("items", [])

            products = []
            for item in items:
                products.append({"attributes": item})

            self.save_session()
            return [{"products": products}]

    def get_cart(self):
        self.session.headers["Referer"] = "https://www.carrefour.fr/cart"
        response = self.session.get(self.CART_URL)
        response.raise_for_status()
        self.save_session()
        data = response.json()
        return data.get("cart", {})

    def update_cart(
        self, basket_service_id, ean, quantity, sub_basket_type="express_delivery"
    ):
        """Updates item quantity in cart. 'counter' is the total target quantity."""
        return self.update_cart_batch(
            [
                {
                    "basketServiceId": basket_service_id,
                    "counter": quantity,
                    "ean": ean,
                    "subBasketType": sub_basket_type,
                }
            ]
        )

    def update_cart_batch(self, items):
        """Updates multiple items in cart at once."""
        payload = {
            "trackingRequest": {"pageType": "search", "pageId": "search"},
            "items": items,
        }
        response = self.session.patch(self.CART_URL, json=payload)
        response.raise_for_status()
        self.save_session()
        data = response.json()
        return data.get("cart", {})

    def extract_all_products(self, search_results):
        extracted = []
        for placement in search_results:
            products = placement.get("products", [])
            for p in products:
                info = self.extract_product_info(p)
                if info:
                    extracted.append(info)
        return extracted

    def extract_product_info(self, product_node):
        attrs = product_node.get("attributes", {})
        ean = attrs.get("ean")
        basket_id = attrs.get("offerServiceId")
        offers = attrs.get("offers", {})
        ean_offers = offers.get(ean, {})

        if not basket_id and ean_offers:
            basket_id = list(ean_offers.keys())[0]

        specific_offer = ean_offers.get(basket_id, {}) if basket_id else {}

        if not ean or not basket_id:
            return None

        return {
            "title": attrs.get("title"),
            "ean": ean,
            "basketServiceId": basket_id,
            "subBasketType": "express_delivery",  # Always express_delivery per user req
            "price": specific_offer.get("attributes", {}).get("price", {}).get("price"),
        }


if __name__ == "__main__":
    # To use: create carrefour_session.json with initial cookies first.
    api = CarrefourAPI()
    try:
        print("Cart total:", api.get_cart().get("totalAmount", 0))
    except Exception as e:
        print(f"Error: {e}")
