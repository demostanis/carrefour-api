import requests
import json
import os
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("CarrefourAPI")


class CarrefourAPI:
    BASE_URL = "https://www.carrefour.fr/api"
    SEARCH_URL = f"{BASE_URL}/marketing/search_panel"
    CART_URL = f"{BASE_URL}/cart"
    COOKIE_FILE = os.getenv("CARREFOUR_COOKIE_FILE", "carrefour_session.json")

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
            logger.debug(f"Loading cookies from {self.COOKIE_FILE}")
            try:
                with open(self.COOKIE_FILE, "r") as f:
                    cookies = json.load(f)
                    self.session.cookies.update(cookies)
            except Exception as e:
                logger.error(f"Failed to load cookies: {e}")

    # def save_session(self):
    #     """Saves current session cookies to a local file."""
    #     logger.debug(f"Saving session cookies to {self.COOKIE_FILE}")
    #     try:
    #         # Ensure directory exists
    #         os.makedirs(
    #             os.path.dirname(os.path.abspath(self.COOKIE_FILE)), exist_ok=True
    #         )
    #         with open(self.COOKIE_FILE, "w") as f:
    #             json.dump(self.session.cookies.get_dict(), f)
    #     except Exception as e:
    #         logger.error(f"Failed to save session: {e}")

    def _ensure_fresh_session(self):
        """
        Internal check: if a request fails with 403 (Cloudflare) or 401,
        this would be the place to trigger a browser-based refresh.
        """
        pass

    def search(self, query):
        """
        Search for products using the organic results.
        If headers are correct, Carrefour returns JSON directly.
        """
        logger.debug(f"Searching for query: {query}")
        url = f"https://www.carrefour.fr/s?q={query}"
        # Ensure we have headers that trigger JSON response
        headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
        }
        response = self.session.get(url, headers=headers)

        if response.status_code == 403:
            logger.error("Cloudflare blocking detected during search")
            raise Exception(
                "Cloudflare blocking. Please refresh tokens using the browser."
            )

        response.raise_for_status()

        try:
            data = response.json()
            logger.debug(f"Successfully received JSON response for query: {query}")
            # The structure is {"data": [...], "meta": {...}}
            items = data.get("data", [])

            # These items already have the 'attributes' structure expected by extract_product_info
            # So we can just return them as a pseudo-placement
            # self.save_session()
            return [{"products": items}]
        except Exception as e:
            logger.debug(
                f"JSON parsing failed, falling back to HTML scraping for query: {query}. Error: {e}"
            )
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

            # self.save_session()
            return [{"products": products}]

    def get_cart(self):
        logger.debug("Fetching cart contents")
        self.session.headers["Referer"] = "https://www.carrefour.fr/cart"
        response = self.session.get(self.CART_URL)
        if response.status_code == 403:
            logger.error("Cloudflare blocking detected during get_cart")
            raise Exception(
                "Cloudflare blocking. Please refresh tokens using the browser."
            )
        response.raise_for_status()
        # self.save_session()
        data = response.json()
        cart = data.get("cart", {})
        logger.debug(f"Cart total amount: {cart.get('totalAmount')}")

        # Log items in cart to see their types
        items = cart.get("items", []) or []
        for i, cat in enumerate(items):
            for j, product_item in enumerate(cat.get("products", []) or []):
                logger.debug(f"Cart item {i}-{j} full: {json.dumps(product_item)}")
                ean = product_item.get("product", {}).get("attributes", {}).get("ean")
                sub_type = product_item.get("subBasketType")
                logger.debug(f"Cart item {i}-{j}: EAN {ean}, subBasketType {sub_type}")

        return cart

    def update_cart(
        self, basket_service_id, ean, quantity, sub_basket_type="express_delivery"
    ):
        """Updates item quantity in cart. 'counter' is the total target quantity."""
        logger.debug(f"Updating cart for EAN {ean} to quantity {quantity}")
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
        logger.debug(f"Batch updating {len(items)} items in cart")
        payload = {
            "trackingRequest": {"pageType": "search", "pageId": "search"},
            "items": items,
        }
        logger.debug(f"Cart update payload: {json.dumps(payload)}")
        response = self.session.patch(self.CART_URL, json=payload)
        if response.status_code == 403:
            logger.error("Cloudflare blocking detected during update_cart_batch")
            raise Exception(
                "Cloudflare blocking. Please refresh tokens using the browser."
            )

        if not response.ok:
            logger.error(
                f"Cart update failed with status {response.status_code}: {response.text}"
            )

        response.raise_for_status()
        # self.save_session()
        data = response.json()
        cart = data.get("cart", {})
        logger.debug(f"Cart successfully updated. New total: {cart.get('totalAmount')}")
        return cart

    def resolve_offer_service_id(self, ean, fallback_basket_service_id=None):
        """Resolve the current offer service ID for an EAN, with fallback."""
        try:
            results = self.search(ean)
            products = self.extract_all_products(results)
        except Exception as e:
            logger.debug(f"Failed to resolve offer service ID for {ean}: {e}")
            return (
                fallback_basket_service_id
                if self.is_valid_offer_service_id(fallback_basket_service_id)
                else None
            )

        for product in products:
            if product.get("ean") != ean:
                continue

            resolved_id = product.get("basketServiceId")
            if resolved_id and not resolved_id.startswith("MKP_"):
                return resolved_id

        if self.is_valid_offer_service_id(fallback_basket_service_id):
            return fallback_basket_service_id

        return None

    @staticmethod
    def is_valid_offer_service_id(basket_service_id):
        if not basket_service_id or basket_service_id.startswith("MKP_"):
            return False

        parts = basket_service_id.split("-")
        return len(parts) == 3 and len(parts[2]) >= 4

    @staticmethod
    def derive_sub_basket_type(basket_service_id):
        return (
            "marketplace"
            if basket_service_id.startswith("MKP_")
            else "express_delivery"
        )

    def extract_offer_service_id_from_cart_item(self, product_item):
        product = product_item.get("product", {})
        attrs = product.get("attributes", {})
        offer_service_id = attrs.get("offerServiceId")

        if self.is_valid_offer_service_id(offer_service_id):
            return offer_service_id

        return None

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
        # logger.debug(f"Extracting info from product node: {json.dumps(product_node)}")
        ean = attrs.get("ean")
        offers = attrs.get("offers", {})
        ean_offers = offers.get(ean, {}) if ean else {}

        basket_id = attrs.get("offerServiceId")
        if basket_id and ean_offers and basket_id not in ean_offers:
            basket_id = None

        if not basket_id and ean_offers:
            for offer_id in ean_offers.keys():
                if offer_id.startswith("MKP_"):
                    continue
                basket_id = offer_id
                break

        specific_offer = ean_offers.get(basket_id, {}) if basket_id else {}
        offer_attrs = specific_offer.get("attributes", {}) if specific_offer else {}
        availability = offer_attrs.get("availability", {}) if offer_attrs else {}

        if not ean or not basket_id:
            return None

        # Determine correct subBasketType
        if basket_id.startswith("MKP_"):
            return None  # Never return marketplace items

        if availability.get("purchasable") is not True:
            return None

        if availability.get("stopped") is True or availability.get("suspended") is True:
            return None

        sub_basket = "express_delivery"

        return {
            "title": attrs.get("title"),
            "ean": ean,
            "basketServiceId": basket_id,
            "subBasketType": sub_basket,
            "price": specific_offer.get("attributes", {}).get("price", {}).get("price"),
        }


if __name__ == "__main__":
    # To use: create carrefour_session.json with initial cookies first.
    api = CarrefourAPI()
    try:
        print("Cart total:", api.get_cart().get("totalAmount", 0))
    except Exception as e:
        print(f"Error: {e}")
