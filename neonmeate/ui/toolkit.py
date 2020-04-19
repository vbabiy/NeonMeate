import functools
from gi.repository import GObject, Gtk, Pango, GLib


def gtk_main(func):
    """
    Wraps a function so that it will run on the main GTK
    thread. Intended for use as a decorator with the
    @ syntax.
    """

    def f(*args):
        GLib.idle_add(func, *args)

    return f


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
    __gsignals__ = {
        'value-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }

    def __init__(self, vmargin=10, selectable_rows=True):
        super(Column, self).__init__()
        self._vmargin = vmargin
        if selectable_rows:
            self.set_selection_mode(Gtk.SelectionMode.SINGLE)
            super(Column, self).connect('row-selected', self._on_row_selected)
        else:
            self.set_selection_mode(Gtk.SelectionMode.NONE)

    def add_row(self, text):
        label = Gtk.Label(text, xalign=0)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_margin_top(self._vmargin)
        label.set_margin_bottom(self._vmargin)
        label.show()
        self.add(label)

    def _on_row_selected(self, box, row):
        child = row.get_child()
        if child and isinstance(child, Gtk.Label):
            self.emit('value-selected', child.get_text())
        return True


class Table:
    def __init__(self, column_names, column_types):
        self.column_names = column_names
        self.column_types = column_types
        self.model = Gtk.ListStore(*column_types)
        self.tree = None
        self.selection_handler = None

    def clear(self):
        self.model.clear()

    def add(self, col_values):
        self.model.append(col_values)

    def as_widget(self):
        self.tree = Gtk.TreeView.new_with_model(self.model)

        for i, col_header in enumerate(self.column_names):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(col_header, renderer, text=i)
            # column.set_sort_column_id(i)
            column.set_resizable(True)
            self.tree.append_column(column)

        select = self.tree.get_selection()
        select.connect('changed', self._on_selection_changed)
        self.tree.set_property('fixed_height_mode', True)
        return self.tree

    def _on_selection_changed(self, select):
        model, treeiter = select.get_selected()
        if self.selection_handler:
            self.selection_handler(model[treeiter])

    def set_selection_handler(self, handler):
        self.selection_handler = handler


if __name__ == "__main__":
    l = [True]
    t = Table(['foo', 'bar'], [str, str])

    t.add(['1', '2'])
    t.add(['3', '4'])
    t.add(['5', '6'])

    win = Gtk.Window()
    box = Gtk.FlowBox()
    win.add(box)
    win.connect('destroy', Gtk.main_quit)
    box.add(t.as_widget())
    button = Gtk.Button(label="clear")


    def toggle(x):
        if l[0]:
            l[0] = False
            t.clear()
        else:
            l[0] = True
            t.add(['1', '2'])


    button.connect('clicked', toggle)
    box.add(button)


    def on_select(row):
        print(f"You selected {row[0]} {row[1]}")


    t.set_selection_handler(on_select)
    win.show_all()
    Gtk.main()
