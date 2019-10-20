import mpd as mpd2
import neonmeate.cache

from gi.repository import GObject, GLib


class Mpd:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        c = mpd2.MPDClient()
        c.timeout = 10
        c.idletimeout = None
        self.client = c

    def connect(self):
        self.client.connect(self.host, self.port)

    def close(self):
        self.client.close()
        self.client.disconnect()

    def stop_playing(self):
        self.client.stop()

    def find_artists(self):
        return self.client.list('artist')

    def find_albums(self, artist):
        return self.client.list('album', 'albumartist', artist)

    def status(self):
        return self.client.status()

    def playlistinfo(self):
        return self.client.playlistinfo()

    def populate_cache(self, albumcache):
        artists = self.client.list('artist')
        for artist in artists:
            albums = self.find_albums(artist)
            for album in albums:
                albumcache.add(artist, album)


class MpdState:
    def __init__(self):
        self.playing = False
        self.stopped = False
        self.repeat = False
        self.random = False
        self.consume = False
        self.song_id = -1
        self.elapsed = 0
        self.duration = 0

    def update(self, attrs):
        state_ = attrs['state']
        if state_ == 'pause':
            self.playing = False
            self.stopped = False
            self.song_id = attrs['songid']
        elif state_ == 'stop':
            self.elapsed = 0
        elif state_ == 'play':
            self.elapsed = attrs['elapsed']
            self.duration = attrs['duration']
            self.song_id = attrs['songid']

    def __str__(self):
        return f'songid={self.song_id}, elapsed={self.elapsed}, duration={self.duration}'


class MpdHeartbeat(GObject.GObject):
    __gsignals__ = {
        'song_elapsed_changed': (GObject.SignalFlags.RUN_FIRST, None, (float,))
    }

    def __init__(self, client, millis_interval):
        GObject.GObject.__init__(self)
        self.millis_interval = millis_interval
        self.client = client
        self.source_id = -1
        self.state = MpdState()

    def start(self):
        self.source_id = GLib.timeout_add(self.millis_interval, self.on_sync)

    def stop(self):
        if self.source_id != -1:
            GLib.source_remove(self.source_id)

    def on_sync(self):
        status = self.client.status()
        print(status)
        self.state.update(status)
        return True


if __name__ == '__main__':
    client = Mpd('localhost', 6600)
    client.connect()
    album_cache = neonmeate.cache.AlbumCache()
    client.populate_cache(album_cache)
    print(album_cache)
