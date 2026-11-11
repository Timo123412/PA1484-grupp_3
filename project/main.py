import sys
import time
import json

import lvgl as lv
import network

from board_lvgl import start_board
from debug_log import log

from secrets import WIFI_SSID, WIFI_PASSWORD


class Application:
    def __init__(self):
        self.display, self.touch, self.handler = start_board()
        self.tile2_dark = False
        self.create_ui()
        self.connect_wifi()
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
        try:
            # LVGL writes into a supplied buffer; it does not return a string.
            # 128 bytes accommodates every current option, including UTF-8.
            buffer = bytearray(128)
            self.stop_dropdown.get_selected_str(buffer, len(buffer))
            selected_stop = buffer.split(b"\0", 1)[0].decode("utf-8")
            self.transport_dropdown.get_selected_str(buffer, len(buffer))
            selected_transport = buffer.split(b"\0", 1)[0].decode("utf-8")
            settings = {
                "stop": selected_stop,
                "transport": selected_transport
            }
            with open("settings.json", "w") as stream:
                json.dump(settings, stream)
        except Exception as error:
            # Keep callback errors from interrupting the LVGL task handler.
            self.save_button_label.set_text("Save failed")
            log("Settings save failed: %r" % (error,))
            sys.print_exception(error)
            return

        self.save_button_label.set_text("Saved")
        log("Settings saved to settings.json")


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

        self.tile3_label.set_text("Tabellsida test")

        self.tile3_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile3_label.center()
        self.apply_tile_colors(self.tile3, self.tile3_label, False)

        #tidstabell
        table = lv.table(self.tile3)


        table.set_row_count(5)
        table.set_column_count(5)

        table.set_cell_value(0, 0, "Transport type:")
        table.set_cell_value(0, 1, "Bus")
        table.set_cell_value(0, 2, "Train")
        table.set_cell_value(0, 3, "Ferry")
        table.set_cell_value(0, 4, "All")

        table.set_cell_value(1, 0, "Departure time:")
        table.set_cell_value(1, 1, "16:44")

        table.set_cell_value(2, 0, "Line:")
        table.set_cell_value(2, 1, "1")

        table.set_cell_value(3, 0, "Destination:")
        table.set_cell_value(4, 0, "Status:")
        table.set_cell_value(3, 1, "Karlskrona Centralstation")
        table.set_cell_value(4, 1, "cancelled")

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

        self.stop_dropdown.set_options(
            "Campus Gräsvik\n"
            "Karlskrona Centralstation\n"
            "Bergåsa"
        )
        self.stop_dropdown.set_selected(0)
        self.stop_dropdown.set_style_bg_opa(lv.OPA.COVER, 0)
        self.stop_dropdown.set_style_bg_color(lv.color_hex(0xFFFFFF), 0)
        self.stop_dropdown.set_style_text_color(lv.color_hex(0x000000), 0)
        self.stop_dropdown.set_style_text_font(lv.font_montserrat_28, 0)
        # The popup is a separate LVGL object, not a dropdown part.
        stop_list = self.stop_dropdown.get_list()
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
        transport_list = self.transport_dropdown.get_list()
        transport_list.set_style_text_font(lv.font_montserrat_28, 0)
        transport_list.set_style_pad_ver(12, 0)
        transport_list.set_style_text_line_space(12, 0)

        self.transport_dropdown.set_options(
            "Bus\n"
            "Train\n"
            "Ferry\n"
            "All"
        )
        self.transport_dropdown.set_selected(0)
        self.transport_dropdown.align(
            lv.ALIGN.TOP_MID,
            0,
            220
        )

        self.save_button = lv.button(self.tile4)
        self.save_button.set_width(240)
        self.save_button.set_height(60)
        self.save_button.align(
            lv.ALIGN.TOP_MID,
            0,
            320
        )
        self.save_button_label = lv.label(self.save_button)
        self.save_button_label.set_text("Save")
        self.save_button_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.save_button_label.center()
        self.save_button.add_event_cb(
            self.on_save_button_clicked, lv.EVENT.CLICKED, None
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
