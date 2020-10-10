import os.path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this
from gi.repository import Gdk  # noqa: E402 # need to call require_version before we can call this
from gi.repository import GdkPixbuf  # noqa: E402 # need to call require_version before we can call this
gi.require_version('Pango', '1.0')
from gi.repository import Pango  # noqa: E402 # need to call require_version before we can call this

import jsonrpc  # noqa: E402 # libraries before local imports


MAX_IMAGE_SIZE = 300


def load_local_image(icon_name, icon_size):
    leafname = icon_name
    if icon_size:
        leafname += '_%u' % icon_size
    leafname += '.png'
    icon_filename = os.path.join(os.path.dirname(__file__), leafname)
    return Gtk.Image.new_from_file(icon_filename)


def set_font(label, weight, font_size, colour):
    context = label.create_pango_context()
    font_desc = context.get_font_description()
    font_desc.set_family('sans')
    font_desc.set_weight(weight)
    font_desc.set_size(font_size * Pango.SCALE)
    label.override_font(font_desc)
    label.modify_fg(Gtk.StateType.NORMAL, colour)


class MainWindow(Gtk.ApplicationWindow):
    """
    Main application window
    """

    def __init__(self, show_close_button, hide_mouse_pointer):
        Gtk.Window.__init__(self, title="PiJu")
        self.connect("destroy", self.on_quit)
        self.fullscreen()

        self.play_icon = None
        self.pause_icon = None

        self.artwork = Gtk.Image()
        self.artwork.set_hexpand(False)
        self.artwork.set_vexpand(False)
        self.artwork.set_size_request(MAX_IMAGE_SIZE, MAX_IMAGE_SIZE)
        self.artist_label = Gtk.Label()
        self.track_name_label = Gtk.Label()
        for label in (self.artist_label, self.track_name_label):
            label.set_hexpand(True)
            label.set_vexpand(True)
            label.set_line_wrap(True)
            label.set_justify(Gtk.Justification.LEFT)
        self.prev_button = Gtk.Button()
        self.prev_button.connect('clicked', self.on_previous)
        self.play_pause_button = Gtk.Button()
        self.next_button = Gtk.Button()
        self.next_button.connect('clicked', self.on_next)
        for button in (self.prev_button, self.play_pause_button, self.next_button):
            button.set_halign(Gtk.Align.END)
            button.set_valign(Gtk.Align.CENTER)

        set_font(self.track_name_label, Pango.Weight.BOLD, 32, Gdk.Color.from_floats(0.0, 0.0, 0.0))
        set_font(self.artist_label, Pango.Weight.NORMAL, 24, Gdk.Color.from_floats(0.3, 0.3, 0.3))

        self.play_pause_button.connect('clicked', self.on_play_pause)

        self.play_pause_action = None

        # image          track
        #  ..            artist
        #  prev  play/pause   next
        layout_grid = Gtk.Grid()
        layout_grid.attach(self.artwork, left=0, top=0, width=1, height=2)
        layout_grid.attach(self.track_name_label, left=1, top=0, width=2, height=1)
        layout_grid.attach(self.artist_label, left=1, top=1, width=2, height=1)
        layout_grid.attach(self.prev_button, left=0, top=2, width=1, height=1)
        layout_grid.attach(self.play_pause_button, left=1, top=2, width=1, height=1)
        layout_grid.attach(self.next_button, left=2, top=2, width=1, height=1)
        layout_grid.set_column_spacing(4)
        layout_grid.set_margin_start(20)
        layout_grid.set_margin_end(20)

        overlay = Gtk.Overlay()
        overlay.add(layout_grid)

        if show_close_button:
            close_icon = load_local_image('window-close-solid.png', 0)
            close = Gtk.Button()
            close.set_image(close_icon)
            close.connect('clicked', self.on_quit)
            top_right = Gtk.Alignment.new(1, 0, 0, 0)
            top_right.add(close)
            overlay.add_overlay(top_right)
            overlay.set_overlay_pass_through(top_right, True)

        self.add(overlay)

        self.hide_mouse_pointer = hide_mouse_pointer
        self.connect('realize', self.on_realized)

    def on_next(self, *args):
        jsonrpc.jsonrpc('core.playback.next')

    def on_play_pause(self, *args):
        if self.play_pause_action:
            jsonrpc.jsonrpc(self.play_pause_action)

    def on_previous(self, *args):
        jsonrpc.jsonrpc('core.playback.previous')

    def on_quit(self, *args):
        Gtk.main_quit()

    def on_realized(self, *args):
        if self.hide_mouse_pointer:
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR))
        icon_size = 200 if (self.get_allocated_width() > 1000) else 100
        self.pause_icon = load_local_image('pause-solid', icon_size)
        self.play_icon = load_local_image('play-solid', icon_size)
        prev_icon = load_local_image('backward-solid', icon_size)
        self.prev_button.set_image(prev_icon)
        next_icon = load_local_image('forward-solid', icon_size)
        self.next_button.set_image(next_icon)

    def show_now_playing(self, now_playing):
        self.artist_label.set_label(now_playing.artist_name if now_playing.artist_name else '<Unknown artist>')
        self.track_name_label.set_label(now_playing.track_name if now_playing.track_name else '<Unknown track>')
        if now_playing.image:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(now_playing.image)
            pixbuf = loader.get_pixbuf()
            loader.close()
            if (now_playing.image_width > MAX_IMAGE_SIZE) or (now_playing.image_height > MAX_IMAGE_SIZE):
                if now_playing.image_width > now_playing.image_height:
                    dest_width = MAX_IMAGE_SIZE
                    dest_height = now_playing.image_height * dest_width / now_playing.image_width
                else:
                    dest_height = MAX_IMAGE_SIZE
                    dest_width = now_playing.image_width * dest_height / now_playing.image_height
                pixbuf = pixbuf.scale_simple(MAX_IMAGE_SIZE, MAX_IMAGE_SIZE, GdkPixbuf.InterpType.BILINEAR)
            self.artwork.set_from_pixbuf(pixbuf)
            self.artwork.show()
        else:
            self.artwork.hide()

        if now_playing.current_state == 'playing':
            self.play_pause_button.set_image(self.pause_icon)
            self.play_pause_action = 'core.playback.pause'
        else:
            self.play_pause_button.set_image(self.play_icon)
            self.play_pause_action = 'core.playback.play'
