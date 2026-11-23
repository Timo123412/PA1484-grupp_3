import json
import requests

api_key = "8b2151643bef495c80123b276b375b7c"

response = requests.get(
    "https://realtime-api.trafiklab.se/v1/stops/list",
    params={"key": api_key},
    timeout=120
)

response.raise_for_status()
alla_stops = response.json()["stop_groups"]

karlskrona_stops = []

for grupp in alla_stops:

    if grupp.get("area_type") != "RIKSHALLPLATS":
        continue

    modes = grupp.get("transport_modes", [])

    if not any(mode in ("BUS", "TRAIN", "BOAT") for mode in modes):
        continue

    for hallplats in grupp.get("stops", []):
        lat = hallplats.get("lat")
        lon = hallplats.get("lon")

        if lat is None or lon is None:
            continue

        if 56.05 <= lat <= 56.35 and 15.40 <= lon <= 15.95:
            karlskrona_stops.append({
                "name": grupp["name"],
                "id": grupp["id"]
            })
            break

karlskrona_stops.sort(
    key=lambda stopp: stopp["name"].lower()
)

with open("stops.json", "w", encoding="utf-8") as fil:
    json.dump(karlskrona_stops, fil, ensure_ascii=False, indent=2)



#explanation of the code:
#here first we fetch data for all stops in Sweden, then it filters by area id and transport type
# after that we use coordinates to only cover karlskorna. We use coordinate limits.