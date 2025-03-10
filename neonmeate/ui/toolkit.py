from gi.repository import GdkPixbuf, GObject, Gtk, Pango, GLib, Gdk

import cairo


def glib_main(func):
    """
    Decorator for a function that will not run it synchronously, but
    instead run it on the main GLib thread.

    Example:
    
    @glib_main
    def callback_when_done(obj):
        pass

    # A service will call the callback when the object has been
    # obtained, but the callback will be run on the GLib thread.
    service.fetch_obj(callback_when_done)

    """

    def f(*args):
        GLib.idle_add(func, *args)

    return f


class TimedInfoBar(Gtk.InfoBar):
    """
    An InfoBar that briefly shows a message and then hides itself.
    """

    def __init__(self):
        super(TimedInfoBar, self).__init__()
        self.set_revealed(False)
        self._source_id = None

    def temp_reveal(self, message):
        content_box = self.get_content_area()
        content_box.set_hexpand(True)
        for child in content_box.get_children():
            child.destroy()
        label_container = Gtk.Grid()
        label_container.set_hexpand(True)
        label = Gtk.Label()
        label.set_text(GLib.markup_escape_text(message))
        label.set_padding(5, 5)
        label_container.add(label)
        label_container.show_all()
        content_box.add(label_container)
        self.set_revealed(True)

        def unreveal():
            self.set_revealed(False)
            return False

        self._source_id = GLib.timeout_add_seconds(1, unreveal)


class AlbumArt:
    """
    Asynchronously resolved album artwork. This will initially be a
    pixbuf that is the placeholder image, but will change to the album
    artwork once that has been loaded.
    """
    ScaleMode = GdkPixbuf.InterpType.BILINEAR

    def __init__(self, artcache, album, placeholder_pixbuf):
        self._art = artcache
        self._album = album
        self._resolved = None
        self._placeholder = placeholder_pixbuf

    def is_resolved(self):
        return self._resolved is not None

    def get_scaled_pixbuf(self, edge_size):
        pixbuf = self._resolved if self.is_resolved() else self._placeholder
        return pixbuf.scale_simple(edge_size, edge_size, AlbumArt.ScaleMode)

    def resolve(self, on_done, user_data):
        """
        Asychronously resolves and loads the cover artwork file into a
        pixbuf.  Calls the user-supplied callback with the new pixbuf
        when done. The user_data is arbitrary data that will be passed
        along to the callback.

        """

        @glib_main
        def _on_art_ready(pixbuf, data):
            self._resolved = pixbuf
            on_done(pixbuf, data)

        @glib_main
        def _on_cover_path(cover_path):
            if cover_path:
                self._art.fetch(cover_path, _on_art_ready, user_data)

        self._art.async_resolve_cover_file(self._album.dirpath, _on_cover_path)


class Scrollable(Gtk.ScrolledWindow):
    def __init__(self):
        super(Scrollable, self).__init__()
        self._vp = Gtk.Viewport()
        self.add(self._vp)

    def add_content(self, widget):
        self._vp.add(widget)


class Column(Gtk.ListBox):
    """
    Renders items in a column using a Gtk.ListBox.
    """
    SIG_VALUE_SELECTED = 'value-selected'

    __gsignals__ = {
        SIG_VALUE_SELECTED: (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }

    def __init__(self, vmargin=10, selectable_rows=True, multiselect=False):
        super(Column, self).__init__()
        self._vmargin = vmargin
        if selectable_rows:
            if multiselect:
                self.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
            else:
                self.set_selection_mode(Gtk.SelectionMode.SINGLE)
            super(Column, self).connect('row-selected', self._on_row_selected)
        else:
            self.set_selection_mode(Gtk.SelectionMode.NONE)

    def clear(self):
        children = self.get_children()
        for child in children:
            child.destroy()

    def add_row(self, text):
        label = Gtk.Label()
        label.set_text(text)
        label.set_xalign(0)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_margin_top(self._vmargin)
        label.set_margin_bottom(self._vmargin)
        label.set_margin_start(self._vmargin)
        label.show()
        self.add(label)

    def _on_row_selected(self, box, row):
        if row is None:
            return
        child = row.get_child()
        if child and isinstance(child, Gtk.Label):
            self.emit(Column.SIG_VALUE_SELECTED, child.get_text())
        return True


class Table:
    def __init__(self, column_names, column_types, view_columns, expand_flags):
        self._model_columns = column_names
        self._column_types = column_types
        self._view_columns = view_columns
        self._model = Gtk.ListStore(*column_types)
        self._tree = None
        self._selection_handler = None
        self._selection_changed_id = None
        self._expand = expand_flags

    def clear(self):
        self._model.clear()

    def add(self, col_values):
        self._model.append(col_values)

    def as_widget(self):
        self._tree = Gtk.TreeView.new_with_model(self._model)

        for i, header in enumerate(self._view_columns):
            renderer = Gtk.CellRendererText()
            renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
            column = Gtk.TreeViewColumn(header, renderer, text=i)
            column.set_resizable(True)
            column.set_expand(self._expand[i])
            header_label = Gtk.Label()
            header_label.set_text(header)
            header_label.show()
            column.set_widget(header_label)
            self._tree.append_column(column)

        select = self._tree.get_selection()
        select.set_mode(Gtk.SelectionMode.MULTIPLE)
        self._tree.set_property('fixed_height_mode', True)
        self._tree.columns_autosize()
        return self._tree

    def _disable_selection_signal(self):
        sel = self._tree.get_selection()
        sel.handler_block(self._selection_changed_id)

    def _enable_selection_signal(self):
        sel = self._tree.get_selection()
        sel.handler_unblock(self._selection_changed_id)

    def set_selection_handler(self, handler):
        self._selection_handler = handler


class BooleanRef:
    def __init__(self):
        self._value = False

    def current(self):
        return self._value

    def update(self, new_value):
        changed = new_value != self._value
        self._value = new_value
        return changed


def add_pixbuf_border(pixbuf, color, border_width=4):
    w, h = pixbuf.get_width(), pixbuf.get_height()
    w += border_width * 2
    h += border_width * 2
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surface)
    ctx.new_path()
    ctx.rectangle(0, 0, w, h)
    ctx.close_path()
    Gdk.cairo_set_source_pixbuf(ctx, pixbuf, border_width, border_width)
    ctx.clip_preserve()
    ctx.paint()
    ctx.set_source_rgba(color.red, color.green, color.blue, color.alpha)
    ctx.set_line_width(border_width * 2)
    ctx.stroke()
    return Gdk.pixbuf_get_from_surface(surface, 0, 0, w, h)
