from flask import Flask, request, jsonify
from carrefour_api import CarrefourAPI
import json
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("CarrefourServer")

app = Flask(__name__)
api = CarrefourAPI()


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    try:
        results = api.search(query)
        products = api.extract_all_products(results)

        response_data = []
        for p in products:
            # Use simpler ID format: <ean>,<basket_id>
            product_id = f"{p['ean']},{p['basketServiceId']}"

            response_data.append(
                {
                    "id": product_id,
                    "name": p["title"],
                    "price": p.get("price"),
                }
            )

        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in search: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/batch_search", methods=["POST"])
def batch_search():
    """Batch search for multiple queries. Body should be a JSON string or list in 'data' field."""
    payload = request.json
    logger.debug(f"Received batch search request: {payload}")
    if not payload or "data" not in payload:
        return jsonify({"error": "Missing 'data' field in request body"}), 400

    try:
        raw_data = payload["data"]
        if isinstance(raw_data, str):
            queries = json.loads(raw_data.removeprefix("json"))
        elif isinstance(raw_data, list):
            queries = raw_data
        else:
            return jsonify(
                {"error": "'data' field must be a JSON-encoded string or a list"}
            ), 400
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in batch_search: {e}")
        return jsonify({"error": "'data' field must be a JSON-encoded string"}), 400

    if not isinstance(queries, list):
        return jsonify({"error": "Decoded 'data' must be a list of strings"}), 400

    all_results = {}
    for q in queries:
        try:
            results = api.search(q)
            products = api.extract_all_products(results)
            formatted = []
            for p in products:
                product_id = f"{p['ean']},{p['basketServiceId']}"
                formatted.append(
                    {
                        "id": product_id,
                        "name": p["title"],
                        "price": p.get("price"),
                    }
                )
            all_results[q] = formatted
        except Exception as e:
            logger.error(f"Error in batch_search for query {q}: {e}")
            all_results[q] = {"error": str(e)}

    return jsonify(all_results)


@app.route("/add", methods=["POST"])
def add_to_cart():
    data = request.json
    product_id = data.get("id")
    quantity = data.get("quantity", 1)

    if not product_id:
        return jsonify({"error": "Missing 'id' in request body"}), 400

    try:
        # Decode the simple ID format: <ean>,<basket_id>
        parts = product_id.split(",")
        if len(parts) != 2:
            return jsonify({"error": "Invalid ID format. Use '<ean>,<basket_id>'"}), 400

        ean, basket_id = parts
        sub_basket = (
            "marketplace" if basket_id.startswith("MKP_") else "express_delivery"
        )

        cart = api.get_cart()
        current_qty = 0

        # Traverse categories to find existing quantity
        for category in cart.get("items", []) or []:
            for product_item in category.get("products", []) or []:
                p_obj = product_item.get("product")
                if not p_obj:
                    continue
                p_attrs = p_obj.get("attributes", {})
                if p_attrs.get("ean") == ean:
                    current_qty = product_item.get("counter", 0)
                    break
            if current_qty > 0:
                break

        target_qty = current_qty + quantity
        updated_cart = api.update_cart(basket_id, ean, target_qty, sub_basket)

        return jsonify(
            {
                "message": f"Successfully updated quantity for {ean} to {target_qty}",
                "cart_total": updated_cart.get("totalAmount"),
            }
        )
    except Exception as e:
        logger.error(f"Error in add_to_cart: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/batch", methods=["POST"])
def batch_update():
    """Batch update quantities. Body should be a JSON string or list in 'data' field."""
    payload = request.json
    logger.debug(f"Received batch update request: {payload}")
    if not payload or "data" not in payload:
        return jsonify({"error": "Missing 'data' field in request body"}), 400

    try:
        raw_data = payload["data"]
        if isinstance(raw_data, str):
            data = json.loads(raw_data.removeprefix("json"))
        elif isinstance(raw_data, list):
            data = raw_data
        else:
            return jsonify(
                {"error": "'data' field must be a JSON-encoded string or a list"}
            ), 400
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in batch_update: {e}")
        return jsonify({"error": "'data' field must be a JSON-encoded string"}), 400

    if not isinstance(data, list):
        return jsonify({"error": "Decoded 'data' must be a list"}), 400

    try:
        cart = api.get_cart()
        current_quantities = {}
        for category in cart.get("items", []) or []:
            for product_item in category.get("products", []) or []:
                p_obj = product_item.get("product")
                if not p_obj:
                    continue
                p_attrs = p_obj.get("attributes", {})
                e = p_attrs.get("ean")
                if e:
                    current_quantities[e] = product_item.get("counter", 0)

        # Aggregate quantities to handle multiple entries for the same product in the batch
        aggregated_updates = {}
        for item in data:
            product_id = item.get("id")
            quantity = item.get("quantity", 1)

            if not product_id:
                continue

            parts = product_id.split(",")
            if len(parts) != 2:
                continue

            ean, basket_id = parts
            if ean not in aggregated_updates:
                aggregated_updates[ean] = {
                    "basketServiceId": basket_id,
                    "quantity": quantity,
                }
            else:
                aggregated_updates[ean]["quantity"] += quantity

        items_to_update = []
        for ean, update_info in aggregated_updates.items():
            current_qty = current_quantities.get(ean, 0)
            target_qty = current_qty + update_info["quantity"]

            b_id = update_info["basketServiceId"]
            sub_basket = (
                "marketplace" if b_id.startswith("MKP_") else "express_delivery"
            )

            items_to_update.append(
                {
                    "basketServiceId": b_id,
                    "counter": target_qty,
                    "ean": ean,
                    "subBasketType": sub_basket,
                }
            )

        if not items_to_update:
            return jsonify({"error": "No valid items found in batch request"}), 400

        updated_cart = api.update_cart_batch(items_to_update)

        return jsonify(
            {
                "message": f"Successfully updated {len(items_to_update)} items",
                "cart_total": updated_cart.get("totalAmount"),
            }
        )
    except Exception as e:
        logger.error(f"Error in batch_update: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/cart", methods=["GET"])
def get_cart():
    try:
        cart = api.get_cart()
        items = []
        for category in cart.get("items", []) or []:
            for product_item in category.get("products", []) or []:
                qty = product_item.get("counter")
                p_obj = product_item.get("product")
                if not p_obj:
                    continue
                p_attrs = p_obj.get("attributes", {})

                ean = p_attrs.get("ean")
                title = p_attrs.get("title")
                basket_id = p_attrs.get("offerServiceId")
                offers = p_attrs.get("offers", {})
                ean_offers = offers.get(ean, {}) if ean else {}
                specific_offer = ean_offers.get(basket_id, {}) if basket_id else {}
                offer_attrs = (
                    specific_offer.get("attributes", {}) if specific_offer else {}
                )
                price_obj = offer_attrs.get("price", {}) if offer_attrs else {}
                price = price_obj.get("price") if price_obj else None

                items.append(
                    {
                        "ean": ean,
                        "name": title,
                        "quantity": qty,
                        "price": price,
                        "total": product_item.get("totalItemPrice"),
                    }
                )

        return jsonify(
            {
                "items": items,
                "total_amount": cart.get("totalAmount"),
                "item_count": len(items),
            }
        )
    except Exception as e:
        logger.error(f"Error in get_cart: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9310)
