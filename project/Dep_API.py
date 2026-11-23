import requests

API_KEY = "8b2151643bef495c80123b276b375b7c"


def fetch_departures(stop_id, selected_transport="All"):

    url = "https://realtime-api.trafiklab.se/v1/departures/" + str(stop_id)

    response = None

    try:
        response = requests.get(url + "?key=" + API_KEY, timeout=8)
        if response.status_code != 200:
            return []

        data = response.json()
        departures = data.get("departures", [])


        TRANSPORT_MAP = {
            "Bus": "BUS",
            "Train": "TRAIN",
            "Ferry": "BOAT"
        }

        if selected_transport != "All":
            mode = TRANSPORT_MAP[selected_transport]

            departures = [
                dep for dep in departures
                if (dep.get("route") or {}).get("transport_mode") == mode
            ]

        departures = departures[:10]

        for dep in departures:

            if dep.get("canceled"):
                dep["status"] = "Cancelled"

            elif (dep.get("delay") or 0) > 0:
                dep["status"] = "Delayed"

            elif (dep.get("delay") or 0) < 0:
                dep["status"] = "Early"

            elif dep.get("is_realtime"):
                dep["status"] = "On time"

            else:
                dep["status"] = "Scheduled"

        return departures

    except OSError:
        return None
    finally:
        if response is not None:
            response.close()






