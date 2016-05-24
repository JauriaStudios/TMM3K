#!/usr/bin/env python

'''
    Hey, this is GPLv3 and copyright 2016 TurBoss from Jauria-Studios
'''

from __future__ import division
from __future__ import print_function

from sys import argv

import os
import pyglet
import sqlite3
import markdown
import gi
import ast

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '3.0')

from gi.repository import WebKit2
from gi.repository import Gtk
from gi.repository import Gdk

from gi.repository.GdkPixbuf import Pixbuf, InterpType


# Util for read database info as dictionaries
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# Reads a folder and subdirs an return a dictionary
def read_directory(path):
    data = {}
    for dirname, dirnames, filenames in os.walk(os.path.join("data", path)):
        # print path to all subdirectories first.
        # for subdirname in dirnames:
        #    print(os.path.join(dirname, subdirname))

        # print path to all filenames.

        files = []
        for filename in filenames:
            files.append(filename)
        data[dirname] = files

    return data


# Gets the selected item of a combobox
def get_active_text(combobox):
    tree_iter = combobox.get_active_iter()
    active = combobox.get_active()

    if tree_iter:
        model = combobox.get_model()
        path = model[active][0]
        name = model[tree_iter][0]
        return path, name


# Set the info in a sound combobox
def set_sound_model(widget, data):
    print("loading files..")

    temp_data = {}

    model = widget.get_model()
    widget.set_model(None)
    model.clear()

    for key, value in data.items():
        piter = model.append(None, [key])
        for name in value:
            model.append(piter, [name])
            temp_data[name] = pyglet.media.load(os.path.join(key, name), streaming=False)
            print("%s..." % name)

    widget.set_model(model)
    return temp_data


# sets the info in the rules combobox
def set_rules_model(widget, con):

    categories = get_rule_categories(con)

    model = widget.get_model()
    widget.set_model(None)
    model.clear()

    for category in categories:
        for key, value in category.items():
            piter = model.append(None, [value])

            names = get_rule_names(con, value)
            for name in names:
                for key, value in name.items():
                    model.append(piter, [value])

    widget.set_model(model)


# sets maps in the maps combobox
def set_maps_model(widget, data):

    model = widget.get_model()
    widget.set_model(None)
    model.clear()

    for key, value in data.items():
        piter = model.append(None, [key])
        for maps in value:
            model.append(piter, [maps])


    widget.set_model(model)


# Obtains the categories of the rules
def get_rule_categories(con):

    with con:
        con.row_factory = dict_factory
        cur = con.cursor()
        cur.execute('SELECT DISTINCT category FROM rules')
        categories = cur.fetchall()

    return categories


# Obtains the names of the rules
def get_rule_names(con, category):

    with con:
        con.row_factory = dict_factory
        cur = con.cursor()
        cur.execute('SELECT name FROM rules WHERE category == "%s"' % category)
        names = cur.fetchall()

    return names


# Obtains the description of the rules
def get_rule_descriptions(con, category, rule):

    with con:
        cur = con.cursor()
        cur.execute('SELECT description FROM rules WHERE category == "%s" AND name == "%s"' % (category, rule))
        description = cur.fetchone()

    return description["description"]


def set_pixbuf(widget, maps):
    path, image = get_active_text(widget)
    file = os.path.join(path, image)

    width = 320
    height = 240

    pixbuf = Pixbuf.new_from_file(file)
    #pixbuf = pixbuf.scale_simple(width, height, InterpType.BILINEAR)
    maps.set_from_pixbuf(pixbuf)


# Get monsters in stock
def get_monster_stock_genre(con):
    
    with con:
        con.row_factory = dict_factory
        cur = con.cursor()
        cur.execute('SELECT DISTINCT genre FROM monster_stock')
        genre = cur.fetchall()

    return genre


# Get monsters in stock by genre
def get_monster_stock_by_genre(con, genre):

    monster = {}

    with con:
        con.row_factory = dict_factory
        cur = con.cursor()
        for data in genre:
            for key, value in data.items():

                cur.execute('SELECT name FROM monster_stock WHERE genre == "%s"' % value)
                monster[value] = (cur.fetchall())

    return monster


# sets monster names in the treestore
def set_monster_model(widget, data):

    model = widget.get_model()
    widget.set_model(None)
    model.clear()
    for key, val in data.items():
        piter = model.append(None, [key])
        for data in val:
            for key, val in data.items():
                model.append(piter, [val])

    widget.set_model(model)

def get_monster_info(con, name):

    with con:
        cur = con.cursor()
        cur.execute('SELECT * FROM monster_stock WHERE name == "%s"' % name)
        monster_info = cur.fetchone()

    return monster_info


# sets stats model
def set_stats_model(widget, skill, skills):

    model = widget.get_model()
    widget.set_model(None)
    model.clear()

    skills_dict = ast.literal_eval(skills)

    for key, value in skills_dict.items():
        for actions in value:
            itr = model.append([actions["name"], int(actions["points"])])

    widget.set_model(model)

class Handler:
    def __init__(self):

        self.info_view = WebKit2.WebView()

        self.effects_player = pyglet.media.Player()
        self.music_player = pyglet.media.Player()

        self.statusBar = builder.get_object("statusbar1")

        self.panel_general = builder.get_object("panel_general")
        self.panel_general.set_has_window(True)

        self.con = sqlite3.connect(os.path.join("data", "TurBoMasterManager3000.sqlite"))

        # Main tab widgets
        self.amenaza_display = builder.get_object("amenaza_display")
        self.combobox_rules = builder.get_object("combobox_rules")
        self.combobox_music = builder.get_object("combobox_music")
        self.combobox_effects = builder.get_object("combobox_effects")

        self.viewport_info = builder.get_object("viewport_info")

        self.viewport_info.add(self.info_view)

        self.amenaza_display.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse("Green"))

        set_rules_model(self.combobox_rules,self.con)

        self.effects = read_directory("effects")
        self.music = read_directory("music")

        self.selected_effect = ""
        self.selected_music = ""

        self.current_playing_effect = ""
        self.current_playing_music = ""

        self.effects_sounds = set_sound_model(self.combobox_effects, self.effects)
        # self.music_sounds = set_sound_model(self.combobox_music, self.music)

        self.amenaza = 0

        # Maps tab widgets

        self.maps_combobox = ["" for _ in range(4)]
        self.map_images = ["" for _ in range(4)]
        self.maps = read_directory("maps")

        self.maps_combobox[0] = builder.get_object("combobox1")
        self.maps_combobox[1] = builder.get_object("combobox2")
        self.maps_combobox[2] = builder.get_object("combobox3")
        self.maps_combobox[3] = builder.get_object("combobox4")

        self.map_images[0] = builder.get_object("maps1")
        self.map_images[1] = builder.get_object("maps2")
        self.map_images[2] = builder.get_object("maps3")
        self.map_images[3] = builder.get_object("maps4")

        for i in range(4):
            set_maps_model(self.maps_combobox[i], self.maps)

        # Monster tab
        
        self.treeview_monster = builder.get_object("treeview_monster")

        self.entry_monster_name = builder.get_object("entry_monster_name")
        self.entry_monster_concept = builder.get_object("entry_monster_concept")

        self.treeview_monster_actions = builder.get_object("treeview_monster_actions")
        self.treeview_monster_insteractions = builder.get_object("treeview_monster_interactions")
        self.treeview_monster_cognitions = builder.get_object("treeview_monster_cognitions")


        self.monster_stock_genre = get_monster_stock_genre(self.con)
        self.monster_stock = get_monster_stock_by_genre(self.con, self.monster_stock_genre)

        set_monster_model(self.treeview_monster, self.monster_stock)

        # All done
        print("Loading done.")

    def on_window1_delete_event(self, *args):
        print("Bye bye..")
        Gtk.main_quit(*args)

    def on_imagemenuitem5_activate(self, *args):
        print("Bye bye..")
        Gtk.main_quit(*args)

    def on_spinbutton_amenaza_value_changed(self, widget, data=None):
        self.amenaza = widget.get_value_as_int()

        self.amenaza_display.set_label(str(self.amenaza))

        if (self.amenaza >= 0) and (self.amenaza <= 3):
            self.amenaza_display.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse("Green"))

        elif (self.amenaza >= 4) and (self.amenaza <= 7):
            self.amenaza_display.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse("Orange"))

        elif self.amenaza >= 8:
            self.amenaza_display.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse("Red"))

    def on_combobox_rules_changed(self, widget, data=None):
        category, rule = get_active_text(widget)

        description = get_rule_descriptions(self.con, category, rule)
        mdtext = markdown.markdown(description)
        self.info_view.load_html(mdtext)

    def on_combobox_music_changed(self, widget, data=None):
        path, music = get_active_text(widget)
        self.selected_music = music

    def on_combobox_effects_changed(self, widget, data=None):
        path, effect = get_active_text(widget)
        self.selected_effect = effect

    def on_button_music_stop_clicked(self, widget, data=None):
        print("Stop")

    def on_button_music_pause_clicked(self, widget, data=None):
        print("Pause")

    def on_button_music_play_clicked(self, widget, data=None):
        if self.selected_music != "":
            self.effects_musics[self.selected_music].play()
            self.current_playing_music = self.selected_music

    def on_button_effect_stop_clicked(self, widget, data=None):
        print("stop")

    def on_button_effect_pause_clicked(self, widget, data=None):
        print("Pause")

    def on_button_effect_play_clicked(self, widget, data=None):
        if self.selected_effect != "":
            self.effects_sounds[self.selected_effect].play()
            self.current_playing_effect = self.selected_effect

    def on_combobox1_changed(self, widget, data=None):
        set_pixbuf(widget, self.map_images[0])

    def on_combobox2_changed(self, widget, data=None):
        set_pixbuf(widget, self.map_images[1])

    def on_combobox3_changed(self, widget, data=None):
        set_pixbuf(widget, self.map_images[2])

    def on_combobox4_changed(self, widget, data=None):
        set_pixbuf(widget, self.map_images[3])

    def on_treeview_selection_monster_changed(self, widget, data=None):
        (model, pathlist) = widget.get_selected_rows()
        for path in pathlist:
            tree_iter = model.get_iter(path)
            name = model.get_value(tree_iter, 0)
            monster_info = get_monster_info(self.con, name)
            if monster_info != None:

                self.entry_monster_name.set_text(monster_info["name"])
                self.entry_monster_concept.set_text(monster_info["concept"])

                set_stats_model(self.treeview_monster_actions, monster_info["action"], monster_info["actions"])
                set_stats_model(self.treeview_monster_insteractions, monster_info["interaction"], monster_info["interactions"])
                set_stats_model(self.treeview_monster_cognitions, monster_info["cognition"], monster_info["cognitions"])



builder = Gtk.Builder()
builder.add_from_file(os.path.join("data", "TurBoMasterManager3000.glade"))

builder.connect_signals(Handler())

style_provider = Gtk.CssProvider()

css = open(os.path.join("data", "TurBoMasterManager3000.css"), 'rb')
css_data = css.read()
css.close()

style_provider.load_from_data(css_data)

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(), style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

win = builder.get_object("window1")
win.show_all()

Gtk.main()
