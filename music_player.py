import pygame

class MusicPlayer:
    def __init__(self):
        """ Initialize pygame mixer for music playback """
        pygame.mixer.init()
        self.current_song = None
        self.current_artist = None
        self.current_file = None
        self.volume = 0.7  # Default volume (0.0 to 1.0)
        pygame.mixer.music.set_volume(self.volume)
        

    def play_song(self, file_path, title, artist):
        """ Play a song from the given file path"""
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        self.current_song = title
        self.current_artist = artist
        self.current_file = file_path
        return f"\n▶️  Now Playing: {title} by {artist}"           
            

    def pause(self):
        """ Pause the currently playing song """
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            print("⏸️  Paused")
        else:
            print("⚠️  No song is currently playing")
            

    def resume(self):
        """ Resume the paused song """
        pygame.mixer.music.unpause()
        print("▶️  Resumed")
        

    def stop(self):
        """ Stop playing the current song """
        pygame.mixer.music.stop()
        print("⏹️  Stopped")
        self.current_song = None
        self.current_artist = None
        self.current_file = None
    
        
    def cleanup(self):
        """ Clean up pygame mixer """
        pygame.mixer.quit()