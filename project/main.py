import sys
import time
import json
import os

import lvgl as lv
import network

from board_lvgl import start_board
from debug_log import log

from secrets import WIFI_SSID, WIFI_PASSWORD
from Dep_API import fetch_departures


with open("stops.json", "r") as fil:
    STOP_DATA=json.load(fil)
STOPS=[stopp["name"] for stopp in STOP_DATA]

TRANSPORTS = [
    "Bus",
    "Train",
    "Ferry",
    "All"
]
#reseting to default settings
DEFAULT_SETTINGS = {
    "stop": STOPS[0],
    "stop_id": STOP_DATA[0]["id"],
    "transport": TRANSPORTS[0]
}

class Application:
    def __init__(self):
        self.display, self.touch, self.handler = start_board()
        self.tile2_dark = False
        self.create_ui()
        self.load_settings()
        self.connect_wifi()
        self.update_timetable()

        log("student application ready")

    @staticmethod
    def apply_tile_colors(tile, label, dark):
        tile.set_style_bg_opa(lv.OPA.COVER, 0)
        tile.set_style_bg_color(
            lv.color_hex(0x000000 if dark else 0xFFFFFF), 0
        )
        label.set_style_text_color(
            lv.color_hex(0xFFFFFF if dark else 0x000000), 0
        )

    def on_tile2_clicked(self, _event):
        self.tile2_dark = not self.tile2_dark
        self.apply_tile_colors(self.tile2, self.tile2_label, self.tile2_dark)

    def on_save_button_clicked(self, _event):

        stop_index = self.stop_dropdown.get_selected()
        transport_index = self.transport_dropdown.get_selected()

        selected_stop = STOP_DATA[stop_index]
        selected_transport = TRANSPORTS[transport_index]

        settings = {
            "stop": selected_stop["name"],
            "stop_id": selected_stop["id"],
            "transport": selected_transport
        }

        with open("settings.json", "w") as stream:
            json.dump(settings, stream)

        self.save_button_label.set_text("Saved")
        self.update_timetable()



    def on_reset_button_clicked(self, _event):
        with open("settings.json", "w") as stream:
            json.dump(DEFAULT_SETTINGS, stream)

        self.stop_dropdown.set_selected(STOPS.index(DEFAULT_SETTINGS["stop"]))
        self.transport_dropdown.set_selected(
            TRANSPORTS.index(DEFAULT_SETTINGS["transport"])
        )
        self.update_timetable()
        self.save_button_label.set_text("Save")
        self.reset_button_label.set_text("Reset done")

    def load_settings(self):
        settings = DEFAULT_SETTINGS
        if "settings.json" in os.listdir():
            with open("settings.json", "r") as stream:
                settings = json.load(stream)

        selected_stop = settings.get("stop", DEFAULT_SETTINGS["stop"])
        selected_transport = settings.get("transport", DEFAULT_SETTINGS["transport"])

        if selected_stop in STOPS:
            self.stop_dropdown.set_selected(STOPS.index(selected_stop))

        if selected_transport in TRANSPORTS:
            self.transport_dropdown.set_selected(
                TRANSPORTS.index(selected_transport)
            )


    
    def update_timetable(self):
        stop_index = self.stop_dropdown.get_selected()
        transport_index = self.transport_dropdown.get_selected()

        stop = STOP_DATA[stop_index]
        selected_transport = TRANSPORTS[transport_index]
        self.tile3_label.set_text(
            "Stop: " + stop["name"] +
            "\nTransport: " + selected_transport
        )
        departures = None
        message = "Wi-Fi disconnected"
        if network.WLAN(network.STA_IF).isconnected():
            departures = fetch_departures(stop["id"], selected_transport)
            message = "Network error" if departures is None else "No departures found"
        if not departures:
            self.table.set_row_count(2)
            self.table.set_cell_value(1, 0, "-")
            self.table.set_cell_value(1, 1, "-")
            self.table.set_cell_value(1, 2, message)
            self.table.set_cell_value(1, 3, "-")
            return
        self.table.set_row_count(len(departures) + 1)
        for i, departure in enumerate(departures):

            departure_time = (
                departure.get("realtime")
                or departure.get("scheduled")
            )

            time_text = (
                departure_time[11:16]
                if departure_time else "-"
            )

            route = departure.get("route") or {}

            line = str(route.get("designation") or "-")
            destination = str(route.get("direction") or "-")
            status = departure.get("status", "Scheduled")
            row = i + 1

            self.table.set_cell_value(row, 0, time_text)
            self.table.set_cell_value(row, 1, line)
            self.table.set_cell_value(row, 2, destination)
            self.table.set_cell_value(row, 3, status)

    def create_ui(self):
        'Function: Creates UI'
        self.tileview = lv.tileview(lv.screen_active())
        self.tileview.set_size(600, 450)
        self.tileview.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

        self.tile1 = self.tileview.add_tile(0, 0, lv.DIR.RIGHT | lv.DIR.BOTTOM)
        self.tile2 = self.tileview.add_tile(1, 0, lv.DIR.LEFT | lv.DIR.RIGHT)
        self.tile3 = self.tileview.add_tile(2, 0, lv.DIR.LEFT)
        self.tile4 = self.tileview.add_tile(0, 1, lv.DIR.TOP)

        self.tile1_label = lv.label(self.tile1)

        self.tile1_label.set_text("Project Blekingetrafiken\nGroup 3\nVersion: 1.1\nRamina Izadpanahi\nIslam Madwar\nLucas Rokicki\nTimothy Gillberg\nHiran Ismail")

        self.tile1_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile1_label.center()
        self.apply_tile_colors(self.tile1, self.tile1_label, False)


        self.tile2_label = lv.label(self.tile2)
        self.tile2_label.set_text("Welcome to the workshop")
        self.tile2_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile2_label.center()
        self.apply_tile_colors(self.tile2, self.tile2_label, False)
        self.tile2.add_flag(lv.obj.FLAG.CLICKABLE)
        self.tile2.add_event_cb(
            self.on_tile2_clicked, lv.EVENT.CLICKED, None
        )

        #tile 3
        self.tile3_label = lv.label(self.tile3)

        self.tile3_label.set_text("departure table")

        self.tile3_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile3_label.align(lv.ALIGN.TOP_MID, 0, 5)        
        self.apply_tile_colors(self.tile3, self.tile3_label, False)

        #tidstabell
        self.table = lv.table(self.tile3)

        self.table.set_row_count(11)
        self.table.set_column_count(4)
        self.table.set_column_width(0, 110)
        self.table.set_column_width(1, 65)
        self.table.set_column_width(2, 270)
        self.table.set_column_width(3, 135)
        self.table.set_size(580, 330)
        self.table.align(lv.ALIGN.TOP_MID, 0, 100)

        self.table.set_cell_value(0, 0, "Time")
        self.table.set_cell_value(0, 1, "Line")
        self.table.set_cell_value(0, 2, "Destination")
        self.table.set_cell_value(0, 3, "Status")

    #tile 4
        self.tile4_label = lv.label(self.tile4)

        self.tile4_label.set_text("Settings")
        self.tile4_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile4_label.align(lv.ALIGN.TOP_MID, 0, 12)
        self.apply_tile_colors(self.tile4, self.tile4_label, False)

        self.stop_label = lv.label(self.tile4)
        self.stop_label.set_text("Select Stop:")
        self.stop_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.apply_tile_colors(self.tile4, self.stop_label, False)
        self.stop_label.align(
            lv.ALIGN.TOP_MID,
            0,
            60
        )

        self.stop_dropdown = lv.dropdown(self.tile4)
        self.stop_dropdown.set_width(500)
        self.stop_dropdown.set_height(60)

        self.stop_dropdown.set_options("\n".join(STOPS))
        self.stop_dropdown.set_selected(0)
        self.stop_dropdown.set_style_bg_opa(lv.OPA.COVER, 0)
        self.stop_dropdown.set_style_bg_color(lv.color_hex(0xFFFFFF), 0)
        self.stop_dropdown.set_style_text_color(lv.color_hex(0x000000), 0)
        self.stop_dropdown.set_style_text_font(lv.font_montserrat_28, 0)
        stop_list = self.stop_dropdown.get_list()
        if stop_list is not None:
            stop_list.set_style_text_font(lv.font_montserrat_28, 0)
            stop_list.set_style_text_color(lv.color_hex(0x000000), 0)
            stop_list.set_style_bg_color(lv.color_hex(0xFFFFFF), 0)
            stop_list.set_style_bg_opa(lv.OPA.COVER, 0)
            stop_list.set_style_pad_ver(12, 0)
            stop_list.set_style_text_line_space(12, 0)
        self.stop_dropdown.set_style_border_width(2, 0)
        self.stop_dropdown.set_style_border_color(lv.color_hex(0x333333), 0)
        self.stop_dropdown.align(
            lv.ALIGN.TOP_MID,
            0,
            100
        )

        self.transport_label = lv.label(self.tile4)
        self.transport_label.set_text("Transport type:")
        self.transport_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.apply_tile_colors(self.tile4, self.transport_label, False)
        self.transport_label.align(
            lv.ALIGN.TOP_MID,
            0,
            180
        )
        self.transport_dropdown= lv.dropdown(self.tile4)
        self.transport_dropdown.set_width(500)
        self.transport_dropdown.set_height(60)
        self.transport_dropdown.set_style_text_font(lv.font_montserrat_28, 0)
        #här:
        transport_list = self.transport_dropdown.get_list()
        if transport_list is not None:
            transport_list.set_style_text_font(lv.font_montserrat_28, 0)
            transport_list.set_style_pad_ver(12, 0)
            transport_list.set_style_text_line_space(12, 0)

        self.transport_dropdown.set_options("\n".join(TRANSPORTS))
        self.transport_dropdown.set_selected(0)
        self.transport_dropdown.align(
            lv.ALIGN.TOP_MID,
            0,
            220
        )
        #save button
        self.save_button = lv.button(self.tile4)
        self.save_button.set_width(240)
        self.save_button.set_height(60)
        self.save_button.align(
            lv.ALIGN.TOP_MID,
            -130,
            320
        )
        self.save_button_label = lv.label(self.save_button)
        self.save_button_label.set_text("Save")
        self.save_button_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.save_button_label.center()
        self.save_button.add_event_cb(
            self.on_save_button_clicked, lv.EVENT.CLICKED, None
        )
        #reset button
        self.reset_button = lv.button(self.tile4)
        self.reset_button.set_width(240)
        self.reset_button.set_height(60)
        self.reset_button.align(
            lv.ALIGN.TOP_MID,
            130,
            320
        )
        self.reset_button_label = lv.label(self.reset_button)
        self.reset_button_label.set_text("Reset")
        self.reset_button_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.reset_button_label.center()
        self.reset_button.add_event_cb(
            self.on_reset_button_clicked, lv.EVENT.CLICKED, None
        )


    @staticmethod
    def connect_wifi():
        'Function: Connects to WiFi'
        log("connecting to Wi-Fi SSID: " + WIFI_SSID)

        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(WIFI_SSID, WIFI_PASSWORD)
        started = time.ticks_ms()
        while (not station.isconnected() and
               time.ticks_diff(time.ticks_ms(), started) < 15_000):
            time.sleep_ms(250)
        log("Wi-Fi connected" if station.isconnected()
            else "Wi-Fi could not connect (timeout)")


try:
    app = Application()
except Exception as error:
    log("FATAL: %r" % (error,))
    sys.print_exception(error)
    raise
