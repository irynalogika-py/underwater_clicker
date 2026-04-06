from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.utils import platform
from kivy.animation import Animation
from kivy.core.audio import SoundLoader


# Window.size = (450, 600)
# Встановлює розмір вікна: ширина 450px, висота 600px
# Актуально тільки для ПК, на мобільних пристроях ігнорується


class MenuScreen(Screen):
    # Клас екрана головного меню, успадковує Screen
    # Kivy автоматично знайде правило <MenuScreen> у medium.kv

    def go_game(self):
        self.manager.current = "game"
        # self.manager — це ScreenManager, до якого належить цей екран
        # .current = "game" — перемикає на екран з name="game"
        self.manager.transition.direction = "left"
        # Анімація переходу: екран "виїжджає" вліво

    def go_settings(self):
        self.manager.current = "settings"
        self.manager.transition.direction = "up"
        # Анімація переходу: екран "виїжджає" вгору

    def exit_app(self):
        App.get_running_app().stop()
        # get_running_app() — повертає поточний запущений екземпляр App
        # .stop() — завершує програму


class GameScreen(Screen):
    score = NumericProperty(0)

    # Лічильник очок. NumericProperty — не звичайна змінна Python.
    # Коли score змінюється в Python, Label з text: str(root.score)
    # у kv-файлі оновлюється автоматично без додаткового коду

    def on_pre_enter(self, *args):
        # Вбудований метод Screen.
        # Викликається ПЕРЕД тим, як екран стає видимим (під час анімації переходу).
        # Використовується для скидання стану перед показом екрана.
        self.score = 0
        # Скидає рахунок на 0 при кожному вході в екран гри
        app.LEVEL = 0
        # Скидає поточний рівень на початковий
        self.ids.level_complete.opacity = 0
        # self.ids — словник всіх віджетів з id у kv-файлі для цього екрана
        # level_complete — id Label з текстом "Level Complete!"
        # opacity: 0 — робить його невидимим
        self.ids.fish.fish_index = 0
        # fish — id віджета Fish
        # fish_index = 0 — скидає індекс поточної риби на першу
        return super().on_pre_enter(*args)
        # Викликає оригінальний метод батьківського класу Screen.
        # Завжди потрібно викликати super() у on_pre_enter / on_enter,
        # щоб не зламати внутрішню логіку ScreenManager

    def on_enter(self, *args):
        # Вбудований метод Screen.
        # Викликається ПІСЛЯ того, як екран повністю відобразився.
        self.start_game()
        return super().on_enter(*args)

    def start_game(self):
        self.ids.fish.new_fish()
        # Викликає метод new_fish() у віджеті Fish —
        # завантажує першу рибу і починає гру

    def level_complete(self, *args):
        self.ids.level_complete.opacity = 1
        # Робить Label "Level Complete!" видимим.
        # *args потрібен тому, що цей метод викликається через Clock.schedule_once,
        # який завжди передає аргумент dt (delta time — час з попереднього кадру)

    def go_menu(self):
        self.manager.current = "menu"
        self.manager.transition.direction = "right"


class SettingsScreen(Screen):
    def go_menu(self):
        self.manager.current = "menu"
        self.manager.transition.direction = "down"


# Клас для обертання картинок;
# в класі, який спадковує потрібно дадати властивість angle
class RotatedImage(Image):
    ...  # Порожній клас, який просто додає властивість angle для обертання зображення


# Fish успадковує Image — тобто сам є зображенням.
# Додає до Image логіку кліків і зміни риби.
class Fish(RotatedImage):
    fish_current = None  # Назва поточної риби (ключ зі словника FISHES), наприклад "fish1"
    fish_index = 0  # Індекс поточної риби у списку рівня LEVELS[LEVEL].
    hp_current = None  # Поточна кількість HP риби. Зменшується при кожному кліку.

    anim_play = False
    interaction_block = True  # Блокування взаємодії під час анімації. True — взаємодія заблокована, False — дозволена.
    COEF_MULT = 1.5  # Коефіцієнт для збільшення розміру риби під час анімації плавання. 1.5 — збільшує на 50%.
    angle = NumericProperty(
        0)  # Властивість для зберігання кута повороту. NumericProperty, щоб можна було анімувати через Animation.

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.GAME_SCREEN = None
        self.click_music = None

    def on_kv_post(self, base_widget):
        # Вбудований метод Kivy.
        # Викликається після того, як kv-файл повністю побудував цей віджет
        # і всі його дочірні елементи готові.
        # Безпечне місце для збереження посилань на батьківські віджети.
        self.GAME_SCREEN = self.parent.parent.parent
        # self.parent — BoxLayout (безпосередній батько Fish у kv)
        # self.parent.parent — GameScreen (батько BoxLayout)
        # Зберігаємо посилання, щоб потім звертатися до self.GAME_SCREEN.score
        self.click_music = SoundLoader.load("assets/sound.mp3")
        if self.click_music:
            self.click_music.volume = 1.0  # від 0.0 до 1.0
        return super().on_kv_post(base_widget)

    def new_fish(self, *args):
        # Завантажує нову рибу: встановлює зображення і HP
        self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
        # app.LEVELS[app.LEVEL] — список риб поточного рівня, наприклад ['fish1', 'fish2']
        # [self.fish_index] — бере рибу за індексом, наприклад 'fish1'
        self.source = app.FISHES[self.fish_current]["source"]
        # Встановлює шлях до зображення риби
        self.hp_current = app.FISHES[self.fish_current]["hp"]
        # Встановлює кількість HP риби
        # self.opacity = 1   # Робить рибу видимою (після defeated() вона була прихована)

        self.swim()  # Запускає анімацію плавання риби

    def swim(self):  # Анімація появи риби: зліва, з збільшенням розміру і поверненням до нормального
        self.pos = (self.GAME_SCREEN.x - self.width, self.GAME_SCREEN.height / 2)
        self.opacity = 1
        swim = Animation(x=self.GAME_SCREEN.width / 2 - self.width / 2, duration=1)
        swim.start(self)

        swim.bind(on_complete=lambda w, a: setattr(self, "interaction_block",
                                                   False))  # Розблоковує взаємодію після завершення анімації плавання. on_complete — подія, яка викликається після закінчення анімації. lambda w, a: setattr(self, "interaction_block", False) — анонімна функція, яка встановлює interaction_block в False.

    def defeated(self):
        self.interaction_block = True
        # Анімація обертання
        anim = Animation(angle=self.angle + 360, d=1, t='in_cubic')

        # Запам'ятовуємо старі розмір і позицію для анімації зменшення
        old_size = self.size.copy()
        old_pos = self.pos.copy()
        # Новий розмір
        new_size = (self.size[0] * self.COEF_MULT * 3, self.size[1] * self.COEF_MULT * 3)
        # Нова позиція риби при збільшенні
        new_pos = (self.pos[0] - (new_size[0] - self.size[0]) / 2, self.pos[1] - (new_size[0] - self.size[1]) / 2)
        # АНІМАЦІЯ ЗБІЛЬШЕННЯ/ЗМЕНШЕННЯ
        anim &= Animation(size=new_size, t='in_out_bounce') + Animation(size=old_size, duration=0)
        anim &= Animation(pos=new_pos, t='in_out_bounce') + Animation(pos=old_pos, duration=0)

        # anim = Animation(size=(self.size[0] * self.COEF_MULT * 2, self.size[1] * self.COEF_MULT * 2)) + Animation(size=old_size)
        anim &= Animation(opacity=0)  # + Animation(opacity = 1)
        anim.start(self)

    def on_touch_down(self, touch):
        # Вбудований метод Kivy. Викликається при будь-якому дотику/кліку на екран.
        # touch — об'єкт з координатами кліку

        if not self.collide_point(*touch.pos) or not self.opacity:
            return
        # self.collide_point(*touch.pos) — перевіряє, чи потрапив клік
        # у межі прямокутника віджета Fish.
        # *touch.pos розпаковує (x, y) з об'єкта touch.
        # Якщо клік поза рибою АБО риба невидима — ігноруємо клік.
        if not self.anim_play and not self.interaction_block:
            self.hp_current -= 1
            self.GAME_SCREEN.score += 1
            if app.click_music:
                # app.click_music.stop()
                app.click_music.play()

            # Клік призвів до змеьшення hp риби
            if self.hp_current > 0:
                # Запам'ятовуємо старі розмір і позицію для анімації зменьшення
                old_size = self.size.copy()
                old_pos = self.pos.copy()

                # Новий розмір
                new_size = (self.size[0] * self.COEF_MULT, self.size[1] * self.COEF_MULT)
                # Нова позиція риби при збільшенні
                new_pos = (self.pos[0] - (new_size[0] - self.size[0]) / 2,
                           self.pos[1] - (new_size[0] - self.size[1]) / 2)

                # АНІМАЦІЯ ЗБІЛЬШЕННЯ/ЗМЕНЬШЕННЯ
                zoom_anim = Animation(size=(new_size), duration=0.05) + Animation(size=(old_size), duration=0.05)
                zoom_anim &= Animation(pos=(new_pos), duration=0.05) + Animation(pos=(old_pos), duration=0.05)

                zoom_anim.start(self)
                self.anim_play = True

                zoom_anim.bind(on_complete=lambda *args: setattr(self, "anim_play",
                                                                 False))  # Після завершення анімації зменшення розміру, встановлюємо anim_play в False, щоб дозволити наступну анімацію при наступному кліку.

            # Клік призвів до знищення риби
            else:
                self.defeated()

                # Запуск нової риби або анымації завершення рівня після 1 секунди програвання зникнення риби
                if len(app.LEVELS[app.LEVEL]) > self.fish_index + 1:
                    self.fish_index += 1
                    Clock.schedule_once(self.new_fish, 1.2)
                else:
                    Clock.schedule_once(self.GAME_SCREEN.level_complete, 1.2)
                    self.fish_index = 0  # додати для скидання індексу риби після завершення рівня, щоб при повторному вході в рівень починати з першої риби

        return super().on_touch_down(touch)


class UnderwaterClickerApp(App):
    LEVEL = 0
    # Поточний рівень гри. Індекс у списку LEVELS.

    FISHES = {
        "fish1": {"source": "assets/images/fish_01.png", "hp": 10},
        "fish2": {"source": "assets/images/fish_02.png", "hp": 20},
    }
    # Словник з даними всіх риб.
    # Ключ — назва риби, значення — словник з шляхом до зображення і кількістю HP.

    LEVELS = [["fish1", "fish2"]]

    # Список рівнів. Кожен рівень — список риб у порядку появи.
    # Зараз один рівень: спочатку fish1, потім fish2.

    def build(self):
        self.click_music = SoundLoader.load("assets/sound.mp3")
        if self.click_music:
            self.click_music.volume = 1.0
        # Вбудований метод App. Викликається один раз при запуску програми.
        # Повертає кореневий віджет — те, що відображається у вікні.
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(SettingsScreen(name="settings"))
        # name= — рядковий ідентифікатор екрана.
        # Саме це значення використовується у self.manager.current = "game"
        return sm


if platform != 'android':
    Window.size = (450, 600)

app = UnderwaterClickerApp()
# Створює екземпляр застосунку. Змінна app використовується у коді
# для доступу до FISHES, LEVELS, LEVEL через app.FISHES тощо.

app.run()
# Запускає головний цикл Kivy — відкриває вікно і починає обробку подій.
