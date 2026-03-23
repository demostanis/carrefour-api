from flask import Flask, request, jsonify
from carrefour_api import CarrefourAPI
import json

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
        return jsonify({"error": str(e)}), 500


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
        sub_basket = "express_delivery"  # Always hardcoded per user req

        cart = api.get_cart()
        current_qty = 0

        # Traverse categories to find existing quantity
        for category in cart.get("items", []):
            for product_item in category.get("products", []):
                p_attrs = product_item.get("product", {}).get("attributes", {})
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
        return jsonify({"error": str(e)}), 500


@app.route("/cart", methods=["GET"])
def get_cart():
    try:
        cart = api.get_cart()
        items = []
        for category in cart.get("items", []):
            for product_item in category.get("products", []):
                qty = product_item.get("counter")
                p_obj = product_item.get("product", {})
                p_attrs = p_obj.get("attributes", {})

                ean = p_attrs.get("ean")
                title = p_attrs.get("title")
                basket_id = p_attrs.get("offerServiceId")
                offers = p_attrs.get("offers", {})
                ean_offers = offers.get(ean, {})
                specific_offer = ean_offers.get(basket_id, {}) if basket_id else {}
                price = (
                    specific_offer.get("attributes", {}).get("price", {}).get("price")
                )

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
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9310)
