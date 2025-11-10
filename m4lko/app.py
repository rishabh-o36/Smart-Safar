from flask import Flask, request, render_template, redirect, url_for, session
import requests
from pytrends.request import TrendReq

app = Flask(__name__)
app.secret_key = "acddb"

# ─── API integration keys
WEATHER_API_KEY = "af7057dcef3dedf4a2a5a22a65e38d7d"
IQAIR_API_KEY = "87d7b413-83f3-4736-add7-413f610d68e1"
GEOAPIFY_API_KEY = "e17a817730a241a9beeabf52e0b524dd"
HOTEL_API_KEY = "685014414b7f5e0955e47381"
ORS_API_KEY = "5b3ce3597851110001cf62486bb9e2d3ac5e4f5c885ab2de399a14ca"

trends_cache = {}

# using these utility functions

def get_coordinates(city):
    try:
        r = requests.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": city, "limit": 1, "appid": WEATHER_API_KEY},
            timeout=10
        )
        if r.ok and (j := r.json()):
            if isinstance(j, list) and len(j) > 0:
                return j[0]["lat"], j[0]["lon"]
    except Exception as e:
        print("Error in get_coordinates:", e)
    return None, None

def convert_temp(k):
    c = k - 273.15
    f = c * 9 / 5 + 32
    return round(c, 1), round(f, 1)

def get_air_quality(lat, lon):
    try:
        r = requests.get(
            "http://api.airvisual.com/v2/nearest_city",
            params={"lat": lat, "lon": lon, "key": IQAIR_API_KEY},
            timeout=10
        )
        return r.json()["data"]["current"]["pollution"]["aqius"]
    except Exception as e:
        print("Error in get_air_quality:", e)
    return None

def get_source_air_quality(source_city):
    lat, lon = get_coordinates(source_city)
    if lat and lon:
        aqi = get_air_quality(lat, lon)
        return {
            "aqi_value": aqi,
            "air_quality": interpret_aqi(aqi)
        }
    return {
        "aqi_value": None,
        "air_quality": "No data"
    }

def compare_aqi(source_city, dest_lat, dest_lon):
    source_lat, source_lon = get_coordinates(source_city)
    source_aqi = get_air_quality(source_lat, source_lon)
    dest_aqi = get_air_quality(dest_lat, dest_lon)

    if source_aqi is None or dest_aqi is None:
        return {"show_warning": False}

    return {
        "show_warning": dest_aqi > source_aqi + 20,  # Trigger if destination is significantly worse
        "source_aqi": source_aqi,
        "dest_aqi": dest_aqi
    }


def get_location_features(lat, lon):
    try:
        resp = requests.get(
            "https://api.geoapify.com/v1/geocode/reverse",
            params={"lat": lat, "lon": lon, "apiKey": GEOAPIFY_API_KEY, "format": "json"},
            timeout=10
        )
        data = resp.json()
        if data and "features" in data and len(data["features"]) > 0:
            return data["features"][0]["properties"]
    except Exception as e:
        print("Error in get_location_features:", e)
    return {}

def get_tourist_interest(city):
    if city in trends_cache:
        return trends_cache[city]
    try:
        tr = TrendReq(hl="en-US", tz=330)
        tr.build_payload([city], timeframe="today 12-m")
        df = tr.interest_over_time()
        score = int(df[city].iloc[-1]) if not df.empty else 0
    except Exception as e:
        print("Error in get_tourist_interest:", e)
        score = 0
    trends_cache[city] = score
    return score

def interpret_interest(score):
    if score > 75:
        return "🚀 High"
    if score > 50:
        return "🌟 Moderate"
    return "🔍 Low"

def interpret_aqi(aqi):
    if aqi is None:
        return "No data"
    if aqi <= 50:
        return "🟢 Good"
    if aqi <= 100:
        return "🟡 Moderate"
    if aqi <= 150:
        return "🟠 Sensitive"
    if aqi <= 200:
        return "🔴 Unhealthy"
    if aqi <= 300:
        return "🟣 Very Unhealthy"
    return "⚫ Hazardous"

def weather_reco(desc, temp_c):
    d = desc.lower()
    if "rain" in d or "storm" in d:
        return "🌧 Carry waterproof gear"
    if temp_c > 42:
        return "🔥 Extreme heat – hydrate well"
    if temp_c < 10:
        return "❄ Cold – layer up"
    return "✅ Pleasant – go explore"

def eco_tips(desc, temp_c, location_features={}):
    d = desc.lower()
    tips = []

    # General eco-travel essentials
    general_tips = [
        "Reusable face mask",
        "Pocket-sized sanitizer",
        "Refillable water bottle",
        "Cloth or jute bags for shopping",
        "Avoid single-use plastic cutlery",
        "Eco-friendly sunscreen (reef-safe)",
        "Digital tickets/boarding passes",
        "Pack light to reduce travel emissions"
    ]

    # Add weather-specific eco tips
    if "rain" in d:
        tips.extend([
            "Biodegradable raincoat",
            "Quick-dry towel",
            "Avoid plastic umbrellas – use sturdy reusable one",
            "Dry your clothes naturally to save electricity"
        ])
    elif temp_c > 35:
        tips.extend([
            "Use shade instead of relying on AC",
            "Wear breathable natural fabrics",
            "Use fan instead of AC when possible",
            "Avoid cold plastic bottled drinks – go for local refreshments"
        ])
    else:
        tips.extend([
            "Explore on foot or rent a cycle",
            "Support eco-tours or nature walks",
            "Buy handmade or locally crafted items"
        ])

    # Add general sustainable behavior tips
    tips.extend(general_tips)

    # City-based custom eco tips
    city = location_features.get("city", "").lower()
    if "chennai" in city:
        tips.append("Try local sustainable brands from Tamil Nadu")
    elif "goa" in city:
        tips.append("Carry reusable beach mat and avoid plastic near shores")
    elif "delhi" in city:
        tips.append("Use Delhi Metro instead of taxis – lower carbon footprint")
    elif "lucknow" in city:
        tips.append("Visit local markets like Hazratganj – support small vendors")

    return tips


def packing_list(desc, temp_c, location_features={}):
    d = desc.lower()
    if "rain" in d and temp_c > 30:
        items = ["Umbrella", "Raincoat", "Waterproof shoes and Extra socks", "Quick Dry Clothes", "Mosquito Repellent",
                 "PowerBank", "First-Aid Kit"]
    elif temp_c > 35:
        items = ["Light Cotton Clothes", "Hat & Sunglasses", "Sunscreen", "Cooling towel", "Electrolyte Sachets",
                 "Face Mist"]
    elif temp_c > 20 and temp_c < 35:
        items = ["Thin Hoodie/Light Jacket ", "Deodorant", "Lightweight Blankets", "Mosquito Repellent", " Loose-fit Trousers"]

    elif temp_c < 20:
        items = ["Thermals (Top & Bottom)", "Warm jacket", "Gloves, Scarf and Sneakers ", "Lip Balm and Moisturisers",
                 "Hot Water Bottles"]
    area_type = location_features.get("category", "")
    if "coastal" in area_type.lower():
        items.append("Swimwear")
    return items

def get_multi_mode_estimates_to_lucknow(source_city):
    source_city = source_city.lower()

    distances_fares = {
        "delhi": {"distance": 555, "flight": "3702 - ₹4134"},
        "mumbai": {"distance": 1569, "flight": "3784 - ₹10456"},
        "agra": {"distance": 242, "flight": "1995 - ₹21280"},
        "ayodhya": {"distance": 130, "flight": "2288 - ₹5675"},
        "chennai": {"distance": 1914, "flight": "6330 - ₹10185"},
        "bangalore": {"distance": 1881, "flight": "6330 - ₹10185"},
        "punjab": {"distance": 939, "flight": "3250- ₹10185"}

    }

    data = distances_fares.get(source_city)
    if not data:
        return None

    dist = data["distance"]
    train_low = int(0.5 * dist)
    train_high = int(3.5 * dist)
    bus_fare = int(1.65 * dist)
    bus_acfare = int(2.3 * dist)

    return {
        "source": source_city.title(),
        "destination": "Lucknow",
        "distance_km": f"{dist} km",
        "train_range": f"₹{train_low} – ₹{train_high}",
        "bus_fare": f"₹{bus_fare} – ₹{ bus_acfare}",
        "flight_fare": f"₹{data['flight']}"
    }

def generate_travel_advice(temp_c, desc, aqi, trend_score, city):
    advice_parts = []
    try:
        aqi = float(aqi)
    except (ValueError, TypeError):
        aqi = 0
    try:
        trend_score = int(trend_score)
    except (ValueError, TypeError):
        trend_score = 0

    condition_normalized = desc.lower() if isinstance(desc, str) else ""
    bad_conditions = ["storm", "rain", "very hot", "very cold", "snow", "thunderstorm", "high"]
    poor_aqi_threshold = 150
    low_trend_threshold = 30

    if condition_normalized == "clear" and aqi <= 100 and trend_score >= 50:
        advice_parts.append(
            "Overall, it's a great time to explore. Pack light, stay curious, and have a fantastic trip!"
        )
    elif condition_normalized in bad_conditions or aqi > poor_aqi_threshold or trend_score < low_trend_threshold:
        alternatives = {
            "lucknow": ["Nainital", "Goa"],
            "delhi": ["Goa", "Lucknow"],
            "goa": ["Mumbai", "Lucknow"],
            "Punjab": ["Mumbai", "Chandigarh"]
        }
        fallback = alternatives.get(city.lower(), ["Ooty", "Goa"])
        advice_parts.append(
            f"However, conditions may not be ideal for travel. Consider exploring {fallback[0]} or {fallback[1]} instead."
        )
    else:
        advice_parts.append(
            "Conditions are decent—nothing extreme. With a little preparation, your trip can still be enjoyable!"
        )

    return " ".join(advice_parts)

# ─── Attractions, Routing, Parking, and Hotel informattions

def get_route_info(start_lat, start_lon, end_lat, end_lon, mode="driving-car"):
    try:
        response = requests.post(
            f"https://api.openrouteservice.org/v2/directions/{mode}",
            headers={
                "Authorization": ORS_API_KEY,
                "Content-Type": "application/json"
            },
            json={"coordinates": [[start_lon, start_lat], [end_lon, end_lat]]},
            timeout=10
        )
        data = response.json()
        summary = data["features"][0]["properties"]["summary"]
        return {
            "distance_km": round(summary["distance"] / 1000, 2),
            "duration_min": round(summary["duration"] / 60, 1)
        }
    except Exception as e:
        print("Error fetching route:", e)
        return {"distance_km": None, "duration_min": None}


def get_nearest_place(lat, lon, category):
    try:
        radius = 300000
        res = requests.get(
            "https://api.geoapify.com/v2/places",
            params={
                "categories": category,
                "filter": f"circle:{lon},{lat},{radius}",
                "limit": 1,
                "apiKey": GEOAPIFY_API_KEY
            },
            timeout=10
        )
        res.raise_for_status()
        data = res.json()
        features = data.get("features", [])

        if not features:
            print(f"No {category} found near ({lat}, {lon}) within {radius}m")
            return None

        f = features[0]
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [])

        if not coords or len(coords) != 2:
            print(f"Missing or invalid coordinates for {category}")
            return None

        # Attempting  to  several fallbacks for  name clarity  for self understanding
        name = (
            props.get("name")
            or props.get("address_line1")
            or props.get("address")
            or props.get("street")
            or props.get("city")
            or category
        )

        return {
            "name": name,
            "lat": coords[1],
            "lon": coords[0]
        }
    except Exception as e:
        print(f"Error fetching nearest {category}:", e)
        return None
def get_attractions_with_routes(lat, lon):
    try:
        response = requests.get(
            "https://api.geoapify.com/v2/places",
            params={
                "categories": "tourism.attraction,catering.restaurant,leisure,entertainment",
                "filter": f"circle:{lon},{lat},15000",
                "limit": 5,
                "apiKey": GEOAPIFY_API_KEY
            },
            timeout=10
        )
        data = response.json()
        attractions = data.get("features", [])
        print(f"Fetched {len(attractions)} attractions from Geoapify.")
    except Exception as e:
        print("Error fetching attractions:", e)
        return [{"name": "⚠ Error retrieving attractions.", "address": ""}]

    if not attractions:
        return [{"name": "😕 No attractions found nearby.", "address": "Try a larger city or widen the search radius."}]

    enriched = []
    for spot in attractions:
        try:
            name = spot["properties"].get("name", "Unnamed Attraction")
            addr = spot["properties"].get("formatted", "Address N/A")
            enriched.append({"name": name, "address": addr})
        except Exception as e:
            print("Error processing attraction:", e)

    return enriched or [{"name": "⚠ No attractions could be displayed.", "address": ""}]

def get_parking(lat, lon):
    try:
        r = requests.get(
            "https://api.geoapify.com/v2/places",
            params={
                "categories": "parking",
                "filter": f"circle:{lon},{lat},4000",
                "apiKey": GEOAPIFY_API_KEY
            },
            timeout=10
        )
        feats = r.json().get("features", [])
    except Exception as e:
        print("Error in get_parking:", e)
        feats = []

    out = []
    for f in feats:
        props = f.get("properties", {})
        addr = props.get("formatted")
        if not addr:
            continue
        out.append({
            "name": props.get("name", "Parking"),
            "address": addr
        })
    return out

def get_hotels(city):
    try:
        mp = requests.get(
            "https://api.makcorps.com/mapping",
            params={"api_key": HOTEL_API_KEY, "name": city},
            timeout=10
        ).json()
        if not isinstance(mp, list):
            mp = []
    except Exception as e:
        print("Error in get_hotels (mapping):", e)
        mp = []

    try:
        free = requests.get(
            f"https://api.makcorps.com/free/{city.lower()}",
            headers={"Authorization": f"JWT {HOTEL_API_KEY}"},
            timeout=10
        ).json()
    except Exception as e:
        print("Error in get_hotels (free):", e)
        free = []

    price_map = {}
    if isinstance(free, list):
        for entry in free:
            if isinstance(entry, list) and len(entry) >= 2:
                info, rates = entry[0], entry[1]
                name = info.get("hotelName") or info.get("name")
                best = None
                if isinstance(rates, list):
                    for r in rates:
                        for k, v in r.items():
                            if k.startswith("price") and v:
                                try:
                                    p = float(v)
                                    best = p if best is None or p < best else best
                                except:
                                    pass
                if name and best is not None:
                    price_map[name] = best

    hotels = []
    for item in mp:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "HOTEL":
            continue
        name = item.get("details", {}).get("highlighted_name") or item.get("name")
        address = item.get("details", {}).get("address", "Address N/A")
        price = price_map.get(name)
        hotels.append({
            "name": name,
            "address": address,
            "price": f"₹{price:.0f}" if price else "Price N/A",
            "url": f"https://www.google.com/search?q={name.replace(' ', '+')}+hotel"
        })
    if not hotels:
        lat, lon = get_coordinates(city)
        if lat and lon:
            try:
                fallback_resp = requests.get(
                    "https://api.geoapify.com/v2/places",
                    params={
                        "categories": "accommodation.hotel",
                        "filter": f"circle:{lon},{lat},5000",
                        "limit": 20,
                        "apiKey": GEOAPIFY_API_KEY
                    },
                    timeout=10
                ).json()
                fallback_features = fallback_resp.get("features", [])
                for f in fallback_features:
                    nm = f["properties"].get("name", "Unnamed Hotel")
                    addr = f["properties"].get("formatted", "Address N/A")
                    hotels.append({"name": nm, "address": addr, "price": "Price N/A"})
            except Exception as e:
                print("Error in fallback hotels:", e)

    return hotels or [{"name": "No hotels found", "address": "Try another city", "price": "N/A"}]

# input app access routes

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/feasibility")
def feasibility():
    source = request.args.get("source", "").strip()
    city = request.args.get("place", "").strip()
    date = request.args.get("date", "").strip()

    if not city or not date or not source:
        return render_template("index.html", error="Enter source, place & date.")

    lat, lon = get_coordinates(city)
    if not lat:
        return render_template("index.html", error="Invalid place.")

    try:
        wf = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": WEATHER_API_KEY},
            timeout=10
        ).json()
    except Exception as e:
        print("Error fetching weather:", e)
        return render_template("index.html", error="Weather data unavailable.")

    temp_c, temp_f = convert_temp(wf["list"][0]["main"]["temp"])
    desc = wf["list"][0]["weather"][0]["description"]

    aqi = get_air_quality(lat, lon)
    trend_score = get_tourist_interest(city)
    advice = generate_travel_advice(temp_c, desc, aqi, trend_score, city)
    location_features = get_location_features(lat, lon)

    # ✅ Add transport info based on source city
    transport_data = get_multi_mode_estimates_to_lucknow(source)
    aqi_comparison = compare_aqi(source, lat, lon)
    session["aqi_warning"] = aqi_comparison if aqi_comparison["show_warning"] else None
    session["result_data"] = {
        "place": city,
        "date": date,
        "predicted_temp_c": temp_c,
        "predicted_temp_f": temp_f,
        "weather_desc": desc,
        "suitability": weather_reco(desc, temp_c),
        "aqi_value": aqi,
        "air_quality": interpret_aqi(aqi),
        "tourist_score": trend_score,
        "tourist_interest": interpret_interest(trend_score),
        "travel_advice": advice,
        "famous_destinations": get_attractions_with_routes(lat, lon),
        "eco_tips": eco_tips(desc, temp_c, location_features),
        "packing_list": packing_list(desc, temp_c, location_features),
        "Hotels": get_hotels(city),
        "parking_info": get_parking(lat, lon),
        "transport_info": transport_data  # ✅ Added here
    }

    return redirect(url_for("result", cat="overview"))


@app.route("/result/<cat>")
def result(cat):
    return render_template("result.html", cat=cat, result=session.get("result_data", {}))

if __name__ == "__main__":
    app.run(debug=True)