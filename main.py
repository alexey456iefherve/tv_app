import os
import sys
import threading

# Принудительно задаем движок видео до импорта Kivy
os.environ["KIVY_VIDEO"] = "ffpyplayer"

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.video import Video
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock

def load_playlist(filename):
    channels = []
    if not os.path.exists(filename):
        return [("Файл playlist.m3u не найден!", "")]
    
    current_name = "Без названия"
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#EXTINF:"):
                if "," in line:
                    current_name = line.split(",", 1)[1].strip()
            elif line.startswith("http://") or line.startswith("https://"):
                channels.append((current_name, line))
                current_name = "Без названия"
                
    return channels if channels else [("Плейлист пуст", "")]


class IPTVPlayerApp(App):
    def build(self):
        self.title = "Мой Kivy IPTV Плеер"
        Window.size = (1280, 720)
        
        # Корневой контейнер
        self.root_layout = FloatLayout()
        
        # Основной горизонтальный контейнер
        self.main_layout = BoxLayout(orientation='horizontal', spacing=0, padding=0)
        self.root_layout.add_widget(self.main_layout)
        
        # ЛЕВАЯ ЧАСТЬ: Панель со списком каналов
        self.left_panel = BoxLayout(orientation='vertical', size_hint_x=0.35, spacing=5, padding=10)
        self.left_panel.add_widget(Label(text="СПИСОК КАНАЛОВ", font_size=24, size_hint_y=0.1, color=(0, 0.8, 1, 1)))
        
        scroll = ScrollView(size_hint_y=0.9, do_scroll_x=False, do_scroll_y=True)
        
        self.left_menu = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.left_menu.bind(minimum_height=self.left_menu.setter('height'))
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        playlist_path = os.path.join(current_dir, "playlist.m3u")
        
        if not os.path.exists(playlist_path):
            with open(playlist_path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write("#EXTINF:-1, Первый Тестовый Канал\nhttps://cinerama.uz\n")
                f.write("#EXTINF:-1, Второй Тестовый Канал\nhttps://cdnvideo.ru\n")
                f.write("#EXTINF:-1, Новости Космоса\nhttp://teletarget.ru\n")

        self.channels = load_playlist(playlist_path)
        
        self.buttons = []
        self.current_selection = 0
        
        # Переменная для отмены таймера авто-скрытия при быстром перелистывании
        self.auto_hide_trigger = None
        
        for index, channel in enumerate(self.channels):
            channel_name = channel[0]
            btn = Button(
                text=channel_name,
                font_size=18,
                size_hint_y=None,
                height=65,
                background_color=(0.2, 0.3, 0.4, 1)
            )
            self.left_menu.add_widget(btn)
            self.buttons.append(btn)
            
        scroll.add_widget(self.left_menu)
        self.left_panel.add_widget(scroll)
        self.main_layout.add_widget(self.left_panel)
        
        # ПРАВАЯ ЧАСТЬ: Плеер
        self.right_player = BoxLayout(orientation='vertical', size_hint_x=0.65)
        self.video_widget = Video(source='', state='stop', options={'eos': 'loop'})
        self.right_player.add_widget(self.video_widget)
        
        self.main_layout.add_widget(self.right_player)
        
        # КНОПКА ВОЗВРАТА МЕНЮ (Появляется поверх видео)
        self.menu_trigger_btn = Button(
            text="◀ Меню каналов",
            font_size=16,
            size_hint=(None, None),
            size=(180, 50),
            pos_hint={'x': 0.02, 'top': 0.95},
            background_color=(0.1, 0.1, 0.1, 0.6),
            opacity=0,
            disabled=True
        )
        self.menu_trigger_btn.bind(on_release=lambda instance: self.toggle_menu(show=True))
        self.root_layout.add_widget(self.menu_trigger_btn)
        
        # Состояние интерфейса: 'list' или 'fullscreen'
        self.current_state = 'list'
        
        Window.bind(on_key_down=self.on_keyboard_down)
        
        # Запускаем первоначальный выбор и воспроизведение первого канала
        Clock.schedule_once(lambda dt: self.update_selection(trigger_playback=True), 0.5)
        
        return self.root_layout

    def update_selection(self, trigger_playback=True):
        """Обновляет подсветку, делает скролл и автоматически запускает видео с развертыванием"""
        if self.current_state == 'list':
            for index, btn in enumerate(self.buttons):
                if index == self.current_selection:
                    btn.background_color = (1, 0.8, 0, 1)  # Золотой фокус
                    if self.left_menu.parent:
                        self.left_menu.parent.scroll_to(btn)
                else:
                    btn.background_color = (0.2, 0.3, 0.4, 1)

            # Если включен триггер воспроизведения, запускаем видео поток автоматически при наведении
            if trigger_playback and self.buttons:
                channel_name, channel_url = self.channels[self.current_selection]
                if channel_url and not channel_url.startswith("Файл") and not channel_url.startswith("Плейлист"):
                    # Сбрасываем старый таймер авто-скрытия, если пользователь листает дальше
                    if self.auto_hide_trigger:
                        self.auto_hide_trigger.cancel()
                    
                    threading.Thread(target=self.play_video_async, args=(channel_url,), daemon=True).start()

    def play_video_async(self, url):
        try:
            self.video_widget.unload()
            Clock.schedule_once(lambda dt: self._start_playback(url))
        except Exception as e:
            print(f"Ошибка буферизации: {e}")

    def _start_playback(self, url):
        self.video_widget.source = url
        self.video_widget.state = 'play'
        
        # Планируем автоматическое скрытие списка каналов через 1.2 секунды после наведения
        if self.auto_hide_trigger:
            self.auto_hide_trigger.cancel()
        self.auto_hide_trigger = Clock.schedule_once(lambda dt: self.toggle_menu(show=False), 1.2)

    def toggle_menu(self, show=True):
        if show:
            self.current_state = 'list'
            self.menu_trigger_btn.opacity = 0
            self.menu_trigger_btn.disabled = True
            
            self.main_layout.clear_widgets()
            self.left_panel.size_hint_x = 0.35
            self.right_player.size_hint_x = 0.65
            
            self.main_layout.add_widget(self.left_panel)
            self.main_layout.add_widget(self.right_player)
            # При возврате в меню просто подсвечиваем кнопку, но не перезапускаем видео заново
            self.update_selection(trigger_playback=False)
        else:
            if self.video_widget.state == 'play':
                self.current_state = 'fullscreen'
                self.main_layout.remove_widget(self.left_panel)
                self.right_player.size_hint_x = 1.0
                
                self.menu_trigger_btn.opacity = 1
                self.menu_trigger_btn.disabled = False
                
                for btn in self.buttons:
                    btn.background_color = (0.2, 0.3, 0.4, 1)

    def on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        KEY_UP = 273    
        KEY_DOWN = 274  
        KEY_LEFT = 276  
        KEY_RIGHT = 275 
        KEY_ENTER = 13  
        KEY_BACK = 27   

        if self.current_state == 'list':
            if not self.buttons:
                return False
                
            if key == KEY_UP:
                self.current_selection = (self.current_selection - 1) % len(self.channels)
                # Передаем True, чтобы канал сразу включился и развернулся при скролле вверх
                self.update_selection(trigger_playback=True)
                return True
                
            elif key == KEY_DOWN:
                self.current_selection = (self.current_selection + 1) % len(self.channels)
                # Передаем True, чтобы канал сразу включился и развернулся при скролле вниз
                self.update_selection(trigger_playback=True)
                return True
                
            elif key == KEY_RIGHT:
                self.toggle_menu(show=False)
                return True
                
            elif key == KEY_ENTER:
                # Если пользователь нажал ENTER, принудительно скрываем меню прямо сейчас
                self.toggle_menu(show=False)
                return True
                
            elif key == KEY_BACK:
                App.get_running_app().stop()
                return True

        elif self.current_state == 'fullscreen':
            if key in (KEY_BACK, KEY_LEFT):
                self.toggle_menu(show=True)
                return True
                
            elif key == KEY_ENTER:
                if self.video_widget.state == 'play':
                    self.video_widget.state = 'pause'
                else:
                    self.video_widget.state = 'play'
                return True
                
        return False

if __name__ == '__main__':
    IPTVPlayerApp().run()
