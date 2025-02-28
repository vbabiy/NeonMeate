from gi.repository import Gtk, GObject

from .songprogress import SongProgress
from .times import format_elapsed_time


class ControlButton(Gtk.Button):
    def __init__(self, icon_name):
        super(ControlButton, self).__init__()
        self.icon_size = Gtk.IconSize.MENU
        self.icon = Gtk.Image.new_from_icon_name(icon_name, self.icon_size)
        self.add(self.icon)
        self.set_can_focus(False)


class PlayModeButton(Gtk.ToggleButton):
    def __init__(self, icon_name, label=None):
        super(PlayModeButton, self).__init__()
        self.set_can_focus(False)
        if icon_name is not None:
            self._icon_size = Gtk.IconSize.MENU
            self._icon = Gtk.Image.new_from_icon_name(
                icon_name,
                self._icon_size
            )
            self.add(self._icon)
        else:
            lbl = Gtk.Label()
            lbl.set_label(label)
            self.add()


class VolumeControl(Gtk.VolumeButton):
    def __init__(self):
        super(VolumeControl, self).__init__()
        self.set_property('use-symbolic', True)


class PlayPauseButton(ControlButton):
    SIG_PLAYPAUSE_TOGGLED = 'neonmeate_playpause_toggled'

    __gsignals__ = {
        SIG_PLAYPAUSE_TOGGLED: (GObject.SignalFlags.RUN_FIRST, None, (bool,))
    }

    def __init__(self):
        super(PlayPauseButton, self).__init__('media-playback-start')
        self.pause_icon = Gtk.Image.new_from_icon_name(
            'media-playback-pause',
            self.icon_size
        )
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
        self.emit(PlayPauseButton.SIG_PLAYPAUSE_TOGGLED, self.paused)

    def _swap_icons(self):
        child = self.get_child()
        self.remove(child)
        new_icon = self._switch_icon(child)
        self.add(new_icon)
        self.get_child().show()
        self.paused = not self.paused

    def _switch_icon(self, child):
        if child == self.pause_icon:
            return self.play_icon
        return self.pause_icon


class NeonMeateButtonBox(Gtk.ButtonBox):
    def __init__(self):
        super(NeonMeateButtonBox, self).__init__(Gtk.Orientation.HORIZONTAL)
        self.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        self._buttons = []
        self._byname = {}

    def add_button(self, button, name, click_signal_name):
        self._buttons.append(button)
        self._byname[name] = button
        self.add(button)
        if click_signal_name is not None:
            self._emit_on_click(button, click_signal_name)
        return button

    def _emit_on_click(self, button, signal_name):
        def click_handler(_):
            self.emit(signal_name)

        button.connect('clicked', click_handler)


class ControlButtons(NeonMeateButtonBox):
    SIG_STOP_PLAYING = 'neonmeate_stop_playing'
    SIG_START_PLAYING = 'neonmeate_start_playing'
    SIG_TOGGLE_PAUSE = 'neonmeate_toggle_pause'
    SIG_PREV_SONG = 'neonmeate_prev_song'
    SIG_NEXT_SONG = 'neonmeate_next_song'

    __gsignals__ = {
        SIG_STOP_PLAYING: (GObject.SignalFlags.RUN_FIRST, None, ()),
        SIG_START_PLAYING: (GObject.SignalFlags.RUN_FIRST, None, ()),
        SIG_TOGGLE_PAUSE: (GObject.SignalFlags.RUN_FIRST, None, ()),
        SIG_PREV_SONG: (GObject.SignalFlags.RUN_FIRST, None, ()),
        SIG_NEXT_SONG: (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self):
        super(ControlButtons, self).__init__()

        self._prev = self.add_button(
            ControlButton('media-skip-backward'),
            'prev',
            ControlButtons.SIG_PREV_SONG
        )
        self._stop = self.add_button(
            ControlButton('media-playback-stop'),
            'stop',
            ControlButtons.SIG_STOP_PLAYING
        )
        self._play_pause_button = self.add_button(
            PlayPauseButton(),
            'play_pause',
            None
        )
        self._next = self.add_button(
            ControlButton('media-skip-forward'),
            'next',
            ControlButtons.SIG_NEXT_SONG
        )
        self._play_pause_button.connect(
            'neonmeate_playpause_toggled',
            self._on_playpause
        )

    def set_paused(self, paused, stopped):
        if stopped:
            self._play_pause_button.set_play_icon()
        else:
            self._play_pause_button.set_paused(paused)

    def _on_playpause(self, btn, is_paused):
        if is_paused:
            self.emit(ControlButtons.SIG_TOGGLE_PAUSE)
        else:
            self.emit(ControlButtons.SIG_START_PLAYING)
        return True


class PlayModeButtons(NeonMeateButtonBox):
    SIG_PLAYMODE_TOGGLE = 'neonmeate_playmode_toggle'

    __gsignals__ = {
        SIG_PLAYMODE_TOGGLE: (GObject.SignalFlags.RUN_FIRST, None, (str, bool))
    }

    def __init__(self):
        super(PlayModeButtons, self).__init__()
        self._consume = self.add_button(
            PlayModeButton('view-refresh'),
            'consume',
            None
        )
        self._single = self.add_button(
            PlayModeButton('zoom-original', '1'),
            'single',
            None
        )
        self._random = self.add_button(
            PlayModeButton('media-playlist-shuffle-symbolic'),
            'random',
            None
        )
        self._repeat = self.add_button(
            PlayModeButton('media-playlist-repeat-symbolic'),
            'repeat',
            None
        )
        # self._vol_control = self.add_button(
        #     VolumeControl(),
        #     'volume',
        #     None
        # )
        self._consume.set_tooltip_text('Consume mode')
        self._single.set_tooltip_text('Single mode')
        self._random.set_tooltip_text('Random mode')
        self._repeat.set_tooltip_text('Repeat mode')
        self._subscribers_by_signal = {}
        for name, btn in self._byname.items():
            btn.connect('clicked', self._on_click(name, btn))

    def subscribe_to_signal(self, signal, handler):
        handler_id = self.connect(signal, handler)
        handlers = self._subscribers_by_signal.get(signal, [])
        handlers.append(handler_id)
        self._subscribers_by_signal[signal] = handlers

    def _on_click(self, name, btn):
        def handler(_):
            self.emit(
                PlayModeButtons.SIG_PLAYMODE_TOGGLE,
                name,
                btn.get_active()
            )

        return handler

    def _disable_emission(self, signal_name):
        for handler_id in self._subscribers_by_signal.get(signal_name, []):
            self.handler_block(handler_id)

    def _enable_emission(self, signal_name):
        for handler_id in self._subscribers_by_signal.get(signal_name, []):
            self.handler_unblock(handler_id)

    def on_mode_change(self, name, active):
        btn = self._byname.get(name, None)
        if btn and btn.get_active() != active:
            signal_name = PlayModeButtons.SIG_PLAYMODE_TOGGLE
            try:
                self._disable_emission(signal_name)
                btn.set_active(active)
            finally:
                self._enable_emission(signal_name)


class ControlsBar(Gtk.ActionBar):
    __gsignals__ = {
        ControlButtons.SIG_STOP_PLAYING:
            (GObject.SignalFlags.RUN_FIRST, None, ()),
        ControlButtons.SIG_START_PLAYING:
            (GObject.SignalFlags.RUN_FIRST, None, ()),
        ControlButtons.SIG_TOGGLE_PAUSE:
            (GObject.SignalFlags.RUN_FIRST, None, ()),
        ControlButtons.SIG_PREV_SONG: (GObject.SignalFlags.RUN_FIRST, None, ()),
        ControlButtons.SIG_NEXT_SONG: (GObject.SignalFlags.RUN_FIRST, None, ()),
        PlayModeButtons.SIG_PLAYMODE_TOGGLE:
            (GObject.SignalFlags.RUN_FIRST, None, (str, bool))
    }

    def __init__(self):
        super(ControlsBar, self).__init__()
        self._ctrl_btns = ControlButtons()
        self._mode_btns = PlayModeButtons()
        self._progress = SongProgress()
        self._time_label = Gtk.Label()
        self._time_label.set_margin_start(6)
        self._time_label.set_margin_end(6)
        self.pack_start(self._ctrl_btns)
        self.pack_start(self._progress)
        self.pack_start(self._time_label)
        self.pack_start(self._mode_btns)

        for signame in [ControlButtons.SIG_STOP_PLAYING,
                        ControlButtons.SIG_START_PLAYING,
                        ControlButtons.SIG_TOGGLE_PAUSE,
                        ControlButtons.SIG_PREV_SONG,
                        ControlButtons.SIG_NEXT_SONG]:
            self._reemit(self._ctrl_btns, signame)

        self._mode_btns.subscribe_to_signal(
            PlayModeButtons.SIG_PLAYMODE_TOGGLE,
            self._on_user_mode_toggle
        )

    def _reemit(self, object, signame):
        def _emit(_):
            self.emit(signame)

        object.connect(signame, _emit)

    def set_paused(self, paused, stopped):
        self._ctrl_btns.set_paused(paused, stopped)

    def _on_user_mode_toggle(self, widget, mode, enabled):
        self.emit(PlayModeButtons.SIG_PLAYMODE_TOGGLE, mode, enabled)

    def set_mode(self, name, is_active):
        self._mode_btns.on_mode_change(name, is_active)

    def set_song_progress(self, elapsed, total):
        self._progress.set_elapsed(elapsed, total)
        self._time_label.set_text(format_elapsed_time(int(elapsed), int(total)))
