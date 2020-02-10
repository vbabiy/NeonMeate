from gi.repository import Gtk, GObject


class ControlButton(Gtk.Button):
    def __init__(self, icon_name):
        super(ControlButton, self).__init__()
        self.icon_size = Gtk.IconSize.MENU
        self.icon = Gtk.Image.new_from_icon_name(icon_name, self.icon_size)
        self.add(self.icon)


class PlayPauseButton(ControlButton):
    __gsignals__ = {
        'neonmeate_playpause_toggled': (GObject.SignalFlags.RUN_FIRST, None, (bool,))
    }

    def __init__(self):
        super(PlayPauseButton, self).__init__('media-playback-start')
        self.pause_icon = Gtk.Image.new_from_icon_name('media-playback-pause', self.icon_size)
        self.play_icon = self.icon
        self.paused = False
        self.set_paused(False)
        self.connect('clicked', self._toggle_pause_state)

    def set_play_icon(self):
        child = self.get_child()
        if not child == self.play_icon:
            self._swap_icons()

    def set_paused(self, paused):
        child = self.get_child()
        if child == self.play_icon and not paused:
            self._swap_icons()
        elif child == self.pause_icon and paused:
            self._swap_icons()

    def _toggle_pause_state(self, button):
        self.set_paused(not self.paused)
        self.emit('neonmeate_playpause_toggled', self.paused)

    def _swap_icons(self):
        child = self.get_child()
        self.remove(child)
        new_icon = self.play_icon if child == self.pause_icon else self.pause_icon
        self.add(new_icon)
        self.get_child().show()
        self.paused = not self.paused


# noinspection PyUnresolvedReferences
class ControlButtons(Gtk.ButtonBox):
    __gsignals__ = {
        'neonmeate_stop_playing': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'neonmeate_start_playing': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'neonmeate_toggle_pause': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'neonmeate_prev_song': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'neonmeate_next_song': (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self):
        super(ControlButtons, self).__init__(Gtk.Orientation.HORIZONTAL)
        self.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        self._play_pause_button = PlayPauseButton()
        self._stop_button = ControlButton('media-playback-stop')
        self._prev_song_button = ControlButton('media-skip-backward')
        self._next_song_button = ControlButton('media-skip-forward')

        for btn in [
            self._play_pause_button,
            self._stop_button,
            self._prev_song_button,
            self._next_song_button
        ]:
            self.add(btn)

        button_signals = {
            'neonmeate_next_song': self._next_song_button,
            'neonmeate_prev_song': self._prev_song_button,
            'neonmeate_stop_playing': self._stop_button
        }

        for signal_name, btn in button_signals.items():
            self._emit_on_click(btn, signal_name)

        self._play_pause_button.connect('neonmeate_playpause_toggled', self._on_playpause)

    def _emit_on_click(self, button, signal_name):
        def click_handler(_):
            self.emit(signal_name)
        button.connect('clicked', click_handler)

    def set_paused(self, paused, stopped):
        if stopped:
            self._play_pause_button.set_play_icon()
        else:
            self._play_pause_button.set_paused(paused)

    def _on_playpause(self, btn, is_paused):
        if is_paused:
            self.emit('neonmeate_toggle_pause')
        else:
            self.emit('neonmeate_start_playing')
        return True
