import json
import requests
import logging as logger
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Querybox
from ttkbootstrap.dialogs.dialogs import FontDialog
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog
from ttkbootstrap.icons import Emoji

class DiyanetApi:
    BASE_URL = "https://namazvakitleri.diyanet.gov.tr/tr-TR/"

    def _make_request(self, url, params=None):
        try:
            logger.info(f"API isteği yapılıyor: {url}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"API isteği başarısız oldu: {e}")
        except json.JSONDecodeError:
            logger.error("API yanıtı geçerli bir JSON değil.")

    def get_districts(self, city_id):
        url = f"{self.BASE_URL}home/GetRegList"
        params = {'ChangeType': 'state', 'CountryId': '2', 'Culture': 'tr-TR', 'StateId': city_id}
        districts = self._make_request(url, params).json().get('StateRegionList', [])
        return {d.get("IlceAdi"): d.get("IlceID") for d in districts}

    def fetch_prayer_times(self, district_id):
        url = f"{self.BASE_URL}{district_id}"
        response = self._make_request(url)
        return self.parse_times(response.text)

    def parse_times(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        logger.info(f"Soup: {soup.title.string}")
        table = soup.select_one("#tab-1 .vakit-table tbody")

        if not table:
            logger.error("Vakit tablosu bulunamadı")
            return None

        data = {}
        for row in table.find_all("tr"):
            cells = [td.text.strip() for td in row.find_all("td")]
            tarih = cells[0].split()[:3]
            tarih_iso = f"{tarih[2]}-{self.month_to_number(tarih[1])}-{tarih[0]}"
            vakitler = cells[2:]
            data[tarih_iso] = vakitler
        return data

    @staticmethod
    def month_to_number(month_name):
        months = {
            "Ocak": "01", "Şubat": "02", "Mart": "03", "Nisan": "04",
            "Mayıs": "05", "Haziran": "06", "Temmuz": "07", "Ağustos": "08",
            "Eylül": "09", "Ekim": "10", "Kasım": "11", "Aralık": "12"
        }
        return months.get(month_name, None)


class ClockWidget:
    def __init__(self, root):
        self.root = root
        self._settings = Tools.get_settings()  # Ayarları doğrudan Tools'dan al
        self._prayer_times = Tools.get_prayer_times() # {date: [time1, time2, ...]}
        self._next_prayer_time = Tools.find_next_prayer_time(self._prayer_times) # datetime object "%Y-%m-%d %H:%M"

        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)

        logger.debug(f"Ayarlardaki konum: {self._settings['DISPLAY']['position']}")

        colors = self._settings["COLORS"]["standard"]
        font_settings = self._settings["FONTS"]["clock"]

        self.window.configure(bg=colors["background"])
        self.window.attributes('-topmost', self._settings["DISPLAY"]["always_on_top"])

        self.label = tk.Label(
            self.window,
            text="00:00",
            font=(font_settings["family"], font_settings["size"], font_settings["weight"]),
            fg=colors["text"],
            bg=colors["background"]
        )
        self.label.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.initial_geometry_set = False
        self.window.update_idletasks()
        self.set_window_geometry()

        self.is_dragging = False
        self.setup_bindings()
        self.create_context_menu()

        if not Tools.PRAYER_TIMES.exists() or not self._prayer_times:
            logger.info("Vakitler dosyası bulunamadı. Ayarlar penceresi açılıyor...")
            self.root.after(1000, lambda: self.open_settings(None))

        self.update_clock()
        self.keep_on_top()

    def set_window_geometry(self):
        self.window.update_idletasks()
        is_horizontal = self._settings["DISPLAY"]["orientation"] == "horizontal"

        base_width = self.label.winfo_reqwidth()
        base_height = self.label.winfo_reqheight()

        if is_horizontal:
            width = int(base_width * 1.1)
            height = int(base_height * 1.02)
        else:
            width = int(base_height * 1.1)
            height = int(base_width * 1.05)

        x, y = self._settings["DISPLAY"]["position"].values()

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))

        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.update_idletasks()
        return width, height

    def set_window_geometry(self):
        self.window.update_idletasks()
        width = int(self.label.winfo_reqwidth() * 1.1)
        height = int(self.label.winfo_reqheight() * 1.02)
        x, y = self._settings["DISPLAY"]["position"].values()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def update_orientation(self):
        current_width = self.window.winfo_width()
        current_height = self.window.winfo_height()
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        self.window.geometry(f"{current_height}x{current_width}+{x}+{y}")
        self.set_window_geometry()  # Ekran sınırları kontrolü için
        self.update_clock()

    def setup_bindings(self):
        self.window.bind("<Button-1>", self.start_move)
        self.window.bind("<B1-Motion>", self.do_move)
        self.window.bind("<ButtonRelease-1>", self.stop_move)
        self.window.bind("<Double-Button-1>", self.open_settings)
        self.window.bind("<Button-3>", self.show_context_menu)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Ayarları Aç", command=lambda: self.open_settings(None))
        self.context_menu.add_command(label="Programı Kapat", command=self.close_program)

    def start_move(self, event):
        self.is_dragging = True
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        # Yeni konumu hesapla ve geçici olarak pencereye uygula
        if self.is_dragging:
            x = self.window.winfo_x() + (event.x - self.x)
            y = self.window.winfo_y() + (event.y - self.y)
            x, y = self.snap_to_edges(x, y)
            self.window.geometry(f"+{x}+{y}")

    def do_move(self, event):
        if self.is_dragging:
            x = self.window.winfo_x() + (event.x - self.x)
            y = self.window.winfo_y() + (event.y - self.y)
            snap_distance = self._settings["DISPLAY"]["snap_distance"]
            
            # Kenarlara yapışma
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            widget_width = self.window.winfo_width()
            widget_height = self.window.winfo_height()
            if abs(x) < snap_distance: x = 0
            elif abs(x + widget_width - screen_width) < snap_distance:
                x = screen_width - widget_width
            if abs(y) < snap_distance: y = 0
            elif abs(y + widget_height - screen_height) < snap_distance:
                y = screen_height - widget_height
            
            self.window.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        if self.is_dragging:
            self.is_dragging = False
            settings = Tools.get_settings()
            settings["DISPLAY"]["position"].update({
                "x": self.window.winfo_x(),
                "y": self.window.winfo_y()
            })
            Tools.update_settings(settings)
            self._settings = settings

    def snap_to_edges(self, x, y):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        widget_width = self.window.winfo_width()
        widget_height = self.window.winfo_height()
        snap_distance = self._settings["DISPLAY"]["snap_distance"]

        if abs(x) < snap_distance: x = 0
        elif abs(x + widget_width - screen_width) < snap_distance:
            x = screen_width - widget_width

        if abs(y) < snap_distance: y = 0
        elif abs(y + widget_height - screen_height) < snap_distance:
            y = screen_height - widget_height

        return x, y

    def open_settings(self, event=None):
        if (not hasattr(self.root, 'settings_window')
                or not (self.root.settings_window
                        and self.root.settings_window.window.winfo_exists())):
            self.root.settings_window = SettingsWindow(self.root)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def close_program(self):
        self.root.quit()

    def keep_on_top(self):
        self.window.attributes('-topmost', 1)
        self.window.after(5000, self.keep_on_top)

    def update_clock(self):
        if self._next_prayer_time:
            self.update_remaining_time_display()
        else:
            self.label.config(text="00")

        if not self.is_dragging:  # Sürükleme yapılmıyorsa pencere boyutunu güncelle
            self.set_window_geometry() 

        # Güncelleme sıklığını kontrol et
        interval = 1000 if self._settings["DISPLAY"]["show_seconds"] else 60000
        self.root.after(interval, self.update_clock)

    # Kalan süreyi güncelle ve göster
    def update_remaining_time_display(self):
        now = datetime.now()
        if now >= self._next_prayer_time: # Eğer vakit geçtiyse
            # Bir sonraki vakti bul ve güncelle
            self._next_prayer_time = Tools.find_next_prayer_time(self._prayer_times)

        hours, minutes, seconds = Tools.remaining_time(self._next_prayer_time)
        self.update_color_by_time(hours * 60 + minutes) # Renk güncelle
        self.label.config(text=self.format_time(hours, minutes, seconds))

    def format_time(self, hours, minutes, seconds) -> str:
        """Saat metnini ayarlardaki formatlara göre döndür"""
        display = self._settings["DISPLAY"]
        time_parts = []
        separator = "\n" if display["orientation"] == "vertical" else ":"
        
        if hours > 0:
            time_parts.append(str(hours))
            time_parts.append(f"{minutes:02}")
        else:
            time_parts.append(str(minutes))
        
        if display["show_seconds"]:
            time_parts.append(f"{seconds:02}")
            
        return separator.join(time_parts)

    def update_color_by_time(self, minutes):
        if minutes < self._settings["COLORS"]["critical"]["trigger"]:
            self.change_color(self._settings["COLORS"]["critical"])
        elif minutes < self._settings["COLORS"]["warning"]["trigger"]:
            self.change_color(self._settings["COLORS"]["warning"])
        else:
            self.change_color(self._settings["COLORS"]["standard"])

    def change_color(self, color_settings):
        self.label.config(bg=color_settings["background"], fg=color_settings["text"])
        self.window.config(bg=color_settings["background"])

class Tools:
    # BASE_DIR = Path(__file__).parent
    BASE_DIR = Path.cwd()
    LOG_FILE = BASE_DIR / 'app.log'
    SETTINGS = BASE_DIR / 'ayarlar.json'
    PRAYER_TIMES = BASE_DIR / 'vakitler.json'

    _settings = None
    _prayer_times = None
    _cities = [
        {"plaka": "01", "il": "Adana", "id": "500"},
        {"plaka": "02", "il": "Adıyaman", "id": "501"},
        {"plaka": "03", "il": "Afyon", "id": "502"},
        {"plaka": "04", "il": "Ağrı", "id": "503"},
        {"plaka": "05", "il": "Amasya", "id": "505"},
        {"plaka": "06", "il": "Ankara", "id": "506"},
        {"plaka": "07", "il": "Antalya", "id": "507"},
        {"plaka": "08", "il": "Artvin", "id": "509"},
        {"plaka": "09", "il": "Aydın", "id": "510"},
        {"plaka": "10", "il": "Balıkesir", "id": "511"},
        {"plaka": "11", "il": "Bilecik", "id": "515"},
        {"plaka": "12", "il": "Bingöl", "id": "516"},
        {"plaka": "13", "il": "Bitlis", "id": "517"},
        {"plaka": "14", "il": "Bolu", "id": "518"},
        {"plaka": "15", "il": "Burdur", "id": "519"},
        {"plaka": "16", "il": "Bursa", "id": "520"},
        {"plaka": "17", "il": "Çanakkale", "id": "521"},
        {"plaka": "18", "il": "Çankırı", "id": "522"},
        {"plaka": "19", "il": "Çorum", "id": "523"},
        {"plaka": "20", "il": "Denizli", "id": "524"},
        {"plaka": "21", "il": "Diyarbakır", "id": "525"},
        {"plaka": "22", "il": "Edirne", "id": "527"},
        {"plaka": "23", "il": "Elazığ", "id": "528"},
        {"plaka": "24", "il": "Erzincan", "id": "529"},
        {"plaka": "25", "il": "Erzurum", "id": "530"},
        {"plaka": "26", "il": "Eskişehir", "id": "531"},
        {"plaka": "27", "il": "Gaziantep", "id": "532"},
        {"plaka": "28", "il": "Giresun", "id": "533"},
        {"plaka": "29", "il": "Gümüşhane", "id": "534"},
        {"plaka": "30", "il": "Hakkari", "id": "535"},
        {"plaka": "31", "il": "Hatay", "id": "536"},
        {"plaka": "32", "il": "Isparta", "id": "538"},
        {"plaka": "33", "il": "Mersin", "id": "557"},
        {"plaka": "34", "il": "İstanbul", "id": "539"},
        {"plaka": "35", "il": "İzmir", "id": "540"},
        {"plaka": "36", "il": "Kars", "id": "544"},
        {"plaka": "37", "il": "Kastamonu", "id": "545"},
        {"plaka": "38", "il": "Kayseri", "id": "546"},
        {"plaka": "39", "il": "Kırklareli", "id": "549"},
        {"plaka": "40", "il": "Kırşehir", "id": "550"},
        {"plaka": "41", "il": "Kocaeli", "id": "551"},
        {"plaka": "42", "il": "Konya", "id": "552"},
        {"plaka": "43", "il": "Kütahya", "id": "553"},
        {"plaka": "44", "il": "Malatya", "id": "554"},
        {"plaka": "45", "il": "Manisa", "id": "555"},
        {"plaka": "46", "il": "K.Maraş", "id": "541"},
        {"plaka": "47", "il": "Mardin", "id": "556"},
        {"plaka": "48", "il": "Muğla", "id": "558"},
        {"plaka": "49", "il": "Muş", "id": "559"},
        {"plaka": "50", "il": "Nevşehir", "id": "560"},
        {"plaka": "51", "il": "Niğde", "id": "561"},
        {"plaka": "52", "il": "Ordu", "id": "562"},
        {"plaka": "53", "il": "Rize", "id": "564"},
        {"plaka": "54", "il": "Sakarya", "id": "565"},
        {"plaka": "55", "il": "Samsun", "id": "566"},
        {"plaka": "56", "il": "Siirt", "id": "568"},
        {"plaka": "57", "il": "Sinop", "id": "569"},
        {"plaka": "58", "il": "Sivas", "id": "571"},
        {"plaka": "59", "il": "Tekirdağ", "id": "572"},
        {"plaka": "60", "il": "Tokat", "id": "573"},
        {"plaka": "61", "il": "Trabzon", "id": "574"},
        {"plaka": "62", "il": "Tunceli", "id": "575"},
        {"plaka": "63", "il": "Şanlıurfa", "id": "567"},
        {"plaka": "64", "il": "Uşak", "id": "576"},
        {"plaka": "65", "il": "Van", "id": "577"},
        {"plaka": "66", "il": "Yozgat", "id": "579"},
        {"plaka": "67", "il": "Zonguldak", "id": "580"},
        {"plaka": "68", "il": "Aksaray", "id": "504"},
        {"plaka": "69", "il": "Bayburt", "id": "514"},
        {"plaka": "70", "il": "Karaman", "id": "543"},
        {"plaka": "71", "il": "Kırıkkale", "id": "548"},
        {"plaka": "72", "il": "Batman", "id": "513"},
        {"plaka": "73", "il": "Şırnak", "id": "570"},
        {"plaka": "74", "il": "Bartın", "id": "512"},
        {"plaka": "75", "il": "Ardahan", "id": "508"},
        {"plaka": "76", "il": "Iğdır", "id": "537"},
        {"plaka": "77", "il": "Yalova", "id": "578"},
        {"plaka": "78", "il": "Karabük", "id": "542"},
        {"plaka": "79", "il": "Kilis", "id": "547"},
        {"plaka": "80", "il": "Osmaniye", "id": "563"},
        {"plaka": "81", "il": "Düzce", "id": "526"}
    ]

    _default_settings = {
        "LOCATION": {"city": {"name": "İstanbul", "id": "539"}, "district": {"name": "İSTANBUL", "id": "9541"}},
        "COLORS": {"standard": {"background": "#0a1932", "text": "#ffffff"},
                    "warning": {"background": "#540000", "text": "#ffffff", "trigger": 45},
                    "critical": {"background": "#c1121f", "text": "#ffffff", "trigger": 15}},
        "FONTS": {"clock": {"family": "IBM Plex Mono", "size": 14, "weight": "normal"}},
        "DISPLAY": {"position": {"x": 1453, "y": 1050},
                    "always_on_top": True,
                    "snap_distance": 20,
                    "orientation": "horizontal", 
                    "show_seconds": True}
    }

    @staticmethod
    def configure_logging(log_level="INFO"):
        # log_format = "%(asctime)s [%(levelname)s] [%(filename)s:%(funcName)s] - %(message)s"
        log_format = "%(asctime)s [%(levelname)s] [%(filename)-15s:%(funcName)-30s] - %(message)s"
        logger.basicConfig(filename=Tools.LOG_FILE, level=log_level, format=log_format, force=True)

    @classmethod
    def get_settings(cls):
        if cls._settings is None:
            cls._settings = cls.load_json(cls.SETTINGS) or cls.create_default_settings()
        return cls._settings

    @classmethod
    def get_cities(cls):
        return cls._cities

    @classmethod
    def get_prayer_times(cls):
        if cls._prayer_times is None:
            cls._prayer_times = cls.load_json(cls.PRAYER_TIMES) or {}
        return cls._prayer_times

    @classmethod
    def update_prayer_times(cls, new_times):
        cls.save_json(cls.PRAYER_TIMES, new_times)
        cls._prayer_times = new_times

    @classmethod
    def update_settings(cls, new_settings):
        cls.save_json(cls.SETTINGS, new_settings)
        cls._settings = new_settings

    @classmethod
    def create_default_settings(cls):
        cls.save_json(cls.SETTINGS, cls._default_settings)
        return cls._default_settings

    @staticmethod
    def load_json(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                logger.info(f"{file_path.name} dosyası başarıyla yüklendi.")
                return data
        except FileNotFoundError:
            logger.error(f"{file_path.name} dosyası bulunamadı.")
        except json.JSONDecodeError:
            logger.error(f"{file_path.name} dosyasında JSON okuma hatası.")
        return None

    @staticmethod
    def save_json(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, separators=(',', ':'))
            logger.info(f"{file_path} dosyası kaydedildi.")



    @staticmethod
    def find_next_prayer_time2(prayer_times):
        now = datetime.now()
        for day, times in prayer_times.items(): # {"2021-08-01": ["05:00", "13:00", ...]}
            for time_str in times: # "05:00"
                prayer_dt = datetime.strptime(f"{day} {time_str}", "%Y-%m-%d %H:%M")
                if prayer_dt > now: # Eğer bulunan vakit şu andan ileriyse
                    return prayer_dt
        return None  # Eğer uygun vakit bulunamazsa None döner

    @staticmethod
    def find_next_prayer_time(prayer_times):
        now = datetime.now()
        today_str = now.date().isoformat() # "2021-08-01"
        tomorrow_str = (now + timedelta(days=1)).date().isoformat() # "2021-08-02"

        for time_str in prayer_times.get(today_str, []):
            prayer_dt = datetime.strptime(f"{today_str} {time_str}", "%Y-%m-%d %H:%M")
            if prayer_dt > now:
                return prayer_dt

        if prayer_times.get(tomorrow_str):
            return datetime.strptime(f"{tomorrow_str} {prayer_times.get(tomorrow_str)[0]}", "%Y-%m-%d %H:%M")

        return None

    @staticmethod
    def remaining_time(target_time: datetime):
        delta = target_time - datetime.now()
        total_minutes, seconds = divmod(delta.seconds, 60)
        hours, minutes = divmod(total_minutes, 60)
        # return f"{hours}:{minutes:02}:{seconds:02}".split(":")
        return hours, minutes, seconds

    @staticmethod
    def _fill_missing_settings(defaults, current):
        """Yalnızca eksik ayarları varsayılanlarla doldurur, mevcut ayarları değiştirmez."""
        for key, value in defaults.items():
            if isinstance(value, dict):
                # İç içe geçmiş sözlükler için derinlemesine kontrol
                current.setdefault(key, {})
                Tools._fill_missing_settings(value, current[key])
            else:
                # Eğer mevcut bir ayar yoksa varsayılanı ekler
                current.setdefault(key, value)

    def validate_and_fix_settings(self):
        logger.info("Ayarlar kontrol ediliyor...")
        current_settings = self.get_settings() or {}
        modified_settings = current_settings.copy()  # Elle değiştirilmiş ayarları koruyacak kopya

        # Sadece eksik anahtarları doldur
        self._fill_missing_settings(self._default_settings, modified_settings)
        
        if modified_settings != current_settings:
            # Sadece gerekli olduğunda dosyayı güncelle
            self.update_settings(modified_settings)

        return modified_settings

class SettingsWindow:
    def __init__(self, root):
        self.root = root
        self._settings = Tools.get_settings()
        self.district_mapping = {}
        
        # Ana pencere ayarları
        self.window = ttk.Toplevel(self.root)
        self.window.title("Ayarlar")
        
        # Pencere konumu ve boyutu
        screen_x, screen_y = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        self.window.geometry(f"400x600+{screen_x//2-200}+{screen_y//2-300}")
        self.window.resizable(False, False)
        
        # Ana container
        self.main_frame = ttk.Frame(self.window, padding=10)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # Mevcut konum bilgisi
        loc = self._settings['LOCATION']
        ttk.Label(
            self.main_frame,
            text=f"Aktif Konum: {loc['district']['name']} / {loc['city']['name']}",
            # style="primary.TLabel",
            # font=("Segoe Ui", 11, "bold"),
            font=(11)
        ).pack(pady=5)
        
        # LabelFrame'leri oluştur
        self._create_location_frame()
        self._create_display_frame()
        self._create_colors_frame()
        
        # Status bar
        self.status = ttk.Label(
            self.main_frame, 
            text="Hazır",
            # style="primary.TLabel"
        )
        self.status.pack(pady=10)

        # Renklerin var olduğundan emin ol
        if 'COLORS' not in self._settings:
            self._settings['COLORS'] = {
                'standard': {'background': "#0d0338", "text": "#ebebeb"},
                'warning':  {'background': "#530251", "text": "#f4f4f4", "trigger": 45 },
                'critical': {'background': "#1053c2", "text": "#f0f0f0", "trigger": 15 }
            }

    def _create_location_frame(self):
        location_frame = ttk.LabelFrame(
            self.main_frame, 
            text="Konum Ayarları",
            padding=10
        )
        location_frame.pack(fill=X, padx=5, pady=5)
        
        # Sabit genişlik değerleri
        LABEL_WIDTH = 5
        ENTRY_WIDTH = 15
        BUTTON_WIDTH = 15
        
        # İl seçimi
        city_frame = ttk.Frame(location_frame)
        city_frame.pack(fill=X, pady=5)
        
        ttk.Label(
            city_frame, 
            text="Plaka:", 
            width=LABEL_WIDTH
        ).pack(side=LEFT, padx=5)
        
        self.city_entry = ttk.Entry(
            city_frame, 
            width=ENTRY_WIDTH
        )
        self.city_entry.pack(side=LEFT, padx=5)
        
        if current_city := next((c for c in Tools.get_cities() 
                            if c['id'] == self._settings['LOCATION']['city']['id']), None):
            self.city_entry.insert(0, current_city['plaka'])
        
        ttk.Button(
            city_frame,
            text="İlçeleri Getir",
            command=self._fetch_districts,
            style="primary.TButton",
            width=BUTTON_WIDTH
        ).pack(side=RIGHT, padx=5)
        
        # İlçe seçimi
        district_frame = ttk.Frame(location_frame)
        district_frame.pack(fill=X, pady=5)
        
        ttk.Label(
            district_frame, 
            text="İlçe:", 
            width=LABEL_WIDTH
        ).pack(side=LEFT, padx=5)
        
        self.district_combo = ttk.Combobox(
            district_frame,
            state="readonly",
            width=ENTRY_WIDTH,
            values=[]
        )
        self.district_combo.pack(side=LEFT, padx=5, fill=X, expand=YES)
        self.district_combo.set(self._settings['LOCATION']['district']['name'])
        
        ttk.Button(
            district_frame,
            text="Kaydet",
            command=self._save_location,
            style="success.TButton",
            width=BUTTON_WIDTH
        ).pack(side=RIGHT, padx=5)
        
        # Vakitleri güncelle butonu
        ttk.Button(
            location_frame,
            text="Vakitleri Güncelle",
            command=self._update_times,
            style="info.TButton",
            width=BUTTON_WIDTH
        ).pack(pady=10)

    def _create_display_frame(self):
        self.direction_var = ttk.StringVar(value=self._settings['DISPLAY']['orientation'])
        self.seconds_var = ttk.StringVar(
            value="Göster" if self._settings['DISPLAY'].get('show_seconds', True) else "Gizle"
        )
        display_frame = ttk.LabelFrame(
            self.main_frame,
            text="Görünüm Ayarları",
            padding=10
        )
        display_frame.pack(fill=X, padx=5, pady=5)
        
        # Yön seçimi (Yatay/Dikey)
        orientation_frame = ttk.Frame(display_frame)
        orientation_frame.pack(fill=X, pady=5)
        
        ttk.Label(orientation_frame, text="Görünüm:").pack(side=LEFT, padx=5)
        
        for text, val in [("Yatay", "horizontal"), ("Dikey", "vertical")]:
            ttk.Radiobutton(
                orientation_frame,
                text=text,
                variable=self.direction_var,
                value=val,
                command=self._save_display
            ).pack(side=LEFT, padx=10)
        
        # Saniye gösterimi
        seconds_frame = ttk.Frame(display_frame)
        seconds_frame.pack(fill=X, pady=5)
        
        ttk.Label(seconds_frame, text="Saniye:").pack(side=LEFT, padx=5)
        
        for text in ["Göster", "Gizle"]:
            ttk.Radiobutton(
                seconds_frame,
                text=text,
                variable=self.seconds_var,
                value=text,
                command=self._save_display
            ).pack(side=LEFT, padx=10)

    def _create_display_frame(self):
        # Sabit genişlik değerleri
        LABEL_WIDTH = 10
        RADIO_PADDING = 10

        self.direction_var = ttk.StringVar(value=self._settings['DISPLAY']['orientation'])
        self.seconds_var = ttk.StringVar(
            value="Göster" if self._settings['DISPLAY'].get('show_seconds', True) else "Gizle"
        )
        
        display_frame = ttk.LabelFrame(
            self.main_frame,
            text="Görünüm Ayarları",
            padding=10
        )
        display_frame.pack(fill=X, padx=5, pady=5)
        
        # Yön seçimi (Yatay/Dikey)
        orientation_frame = ttk.Frame(display_frame)
        orientation_frame.pack(fill=X, pady=5)
        
        ttk.Label(
            orientation_frame, 
            text="Görünüm:",
            width=LABEL_WIDTH
        ).pack(side=LEFT, padx=5)
        
        radio_frame1 = ttk.Frame(orientation_frame)
        radio_frame1.pack(side=LEFT, fill=X)
        
        for text, val in [("Yatay", "horizontal"), ("Dikey", "vertical")]:
            ttk.Radiobutton(
                radio_frame1,
                text=text,
                variable=self.direction_var,
                value=val,
                command=self._save_display
            ).pack(side=LEFT, padx=RADIO_PADDING)
        
        # Saniye gösterimi
        seconds_frame = ttk.Frame(display_frame)
        seconds_frame.pack(fill=X, pady=5)
        
        ttk.Label(
            seconds_frame, 
            text="Saniye:",
            width=LABEL_WIDTH
        ).pack(side=LEFT, padx=5)
        
        radio_frame2 = ttk.Frame(seconds_frame)
        radio_frame2.pack(side=LEFT, fill=X)
        
        for text in ["Göster", "Gizle"]:
            ttk.Radiobutton(
                radio_frame2,
                text=text,
                variable=self.seconds_var,
                value=text,
                command=self._save_display
            ).pack(side=LEFT, padx=RADIO_PADDING)

    def _create_colors_frame(self):
        colors_frame = ttk.LabelFrame(
            self.main_frame,
            text="Renk Ayarları",
            padding=10
        )
        colors_frame.pack(fill=X, padx=5, pady=5)
        
        # Renk seçimi için grid layout
        # ttk.Label(colors_frame, text="Durum").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(colors_frame, text="Arkaplan").grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(colors_frame, text="Yazı").grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(colors_frame, text="Süre (dk)").grid(row=0, column=3, padx=5, pady=5)  # Yeni sütun başlığı
        
        row = 1
        self.color_patches = {}  # Renk kutularını saklamak için dictionary
        
        # paint_icon = "🎨"  # Emoji kullanımı
        # paint_icon = "🌈"
        paint_icon = "Seç"
        for name, key in [("Normal", "standard"), ("1. Uyarı", "warning"), ("2. Uyarı", "critical")]:
            ttk.Label(colors_frame, text=name).grid(row=row, column=0, padx=5, pady=5)
            
            # Her renk için bir frame oluştur
            for col, color_type in enumerate(['background', 'text'], 1):
                color_frame = ttk.Frame(colors_frame)
                color_frame.grid(row=row, column=col, padx=5, pady=5)
                
                try:
                    color_value = self._settings['COLORS'][key][color_type]
                    
                    patch = tk.Frame(
                        color_frame, 
                        width=40,
                        height=30
                    )
                    patch.configure(bg=color_value)
                    patch.pack(side=LEFT, padx=0)
                    patch.pack_propagate(False)
                    
                    self.color_patches[(key, color_type)] = patch
                    
                    # Renk seçici buton (ikonu ile)
                    btn = ttk.Button(
                        color_frame,
                        text=paint_icon,  # "..." yerine ikonu kullan
                        style="secondary.TButton",
                        cursor="hand2",  # El işaretçisi göster
                        width=3,
                        command=lambda k=key, t=color_type: self._pick_color(k, t)
                    )
                    btn.pack(side=LEFT, padx=2)
                    
                except Exception as e:
                    print(f"Hata: {key} - {color_type}: {e}")
                    logger.error(f"Renk kutusunu oluştururken hata: {e}")
            
            # Trigger input'u (sadece warning ve critical için)
            if key in ['warning', 'critical']:
                trigger_frame = ttk.Frame(colors_frame)
                trigger_frame.grid(row=row, column=3, padx=5, pady=5)
                
                # Trigger değerini COLORS'dan al
                current_trigger = self._settings['COLORS'][key].get('trigger', 45 if key == 'warning' else 15)
                
                trigger_var = tk.StringVar(value=str(current_trigger))
                trigger_entry = ttk.Spinbox(
                    trigger_frame,
                    from_=1,
                    to=120,
                    width=5,
                    textvariable=trigger_var
                )
                trigger_entry.pack(side=LEFT)
                
                # Değer değiştiğinde tetiklenecek fonksiyon
                trigger_entry.configure(
                    command=lambda k=key, v=trigger_var: self._save_trigger(k, v)
                )
                
                # Enter tuşuna basıldığında kaydetme
                trigger_entry.bind(
                    '<Return>',
                    lambda event, k=key, v=trigger_var: self._save_trigger(k, v)
                )
            
            row += 1

    def _pick_color(self, key, color_type):
        """Renk seçici dialog'unu göster ve seçilen rengi kaydet"""
        try:
            current_color = self._settings['COLORS'][key][color_type]
            # ColorChooserDialog'u oluştur
            cd = ColorChooserDialog(
                parent=self.window,
                initialcolor=current_color
            )
            # Dialog'u göster
            cd.show()
            
            # Renk seçimi sonucunu kontrol et
            colors = cd.result
            if colors:  # Eğer bir renk seçildiyse
                selected_color = colors.hex
                # Seçilen rengi ayarlara kaydet
                self._settings['COLORS'][key][color_type] = selected_color
                
                # Renk kutusunu güncelle
                patch = self.color_patches[(key, color_type)]
                patch.configure(bg=selected_color)
                
                # Ayarları kaydet ve widget'ı güncelle
                self._save_settings()
                self._show_status("Renk güncellendi", "success")
                
        except Exception as e:
            error_msg = f"Renk seçiminde hata: {e}"
            print(error_msg)
            self._show_status(error_msg, "danger")
            logger.error(error_msg)

    def _fetch_districts(self):
        """İlçeleri getir ve combo box'ı güncelle"""
        city_code = self.city_entry.get().strip()
        if not city_code:
            return self._show_status("Plaka kodu giriniz!", "danger")
            
        if city := next((c for c in Tools.get_cities() if c['plaka'] == city_code), None):
            if districts := DiyanetApi().get_districts(city['id']):
                self.district_mapping = districts
                district_names = list(districts.keys())
                self.district_combo.configure(values=district_names)
                self.district_combo.set(district_names[0])
                self._show_status(f"{len(districts)} ilçe bulundu", "success")
            else:
                self._show_status("İlçeler alınamadı!", "danger")
        else:
            self._show_status("Geçersiz plaka kodu!", "danger")

    def _save_location(self):
        """Seçilen konum bilgilerini kaydet"""
        city_code = self.city_entry.get().strip()
        district_name = self.district_combo.get()
        
        if not (city_code and district_name in self.district_mapping):
            return self._show_status("Geçerli il ve ilçe seçiniz!", "danger")
            
        if city := next((c for c in Tools.get_cities() if c['plaka'] == city_code), None):
            self._settings['LOCATION'].update({
                'city': {'name': city['il'], 'id': city['id']},
                'district': {'name': district_name, 'id': self.district_mapping[district_name]}
            })
            self._save_settings("Konum kaydedildi")

    def _update_times(self):
        """Namaz vakitlerini güncelle"""
        if times := DiyanetApi().fetch_prayer_times(self._settings['LOCATION']['district']['id']):
            Tools.update_prayer_times(times)
            self._show_status("Vakitler güncellendi", "success")
            if hasattr(self.root, 'clock_widget'):
                self.root.clock_widget._prayer_times = Tools.get_prayer_times()
                self.root.clock_widget._next_prayer_time = Tools.find_next_prayer_time(
                    self.root.clock_widget._prayer_times
                )
                self.root.clock_widget.update_clock()
        else:
            self._show_status("Güncelleme başarısız", "danger")

    def _save_trigger(self, key, trigger_var):
        """Trigger süresini kaydet"""
        try:
            value = int(trigger_var.get())
            if 1 <= value <= 120:  # 1-120 dakika arası değer kontrolü
                # Ayarları güncelle
                self._settings['COLORS'][key]['trigger'] = value
                # Ayarları kaydet
                self._save_settings()
                self._show_status(f"{key} için süre güncellendi: {value} dk", "success")
            else:
                # Geçersiz değer girilirse eski değere geri dön
                old_value = self._settings['COLORS'][key]['trigger']
                trigger_var.set(str(old_value))
                self._show_status("Süre 1-120 dakika arasında olmalı!", "warning")
        except ValueError:
            # Sayısal olmayan değer girilirse eski değere geri dön
            old_value = self._settings['COLORS'][key]['trigger']
            trigger_var.set(str(old_value))
            self._show_status("Geçersiz süre değeri!", "danger")

    def _save_display(self):
        """Görünüm ayarlarını kaydet"""
        self._settings['DISPLAY'].update({
            'orientation': self.direction_var.get(),
            'show_seconds': (self.seconds_var.get() == "Göster")
        })
        self._save_settings()
        if hasattr(self.root, 'clock_widget'):
            self.root.clock_widget.update_orientation()

    def _save_settings(self, msg=None):
        """Ayarları kaydet ve widget'ı güncelle"""
        try:
            Tools.update_settings(self._settings)
            if msg:
                self._show_status(msg, "success")
            if hasattr(self.root, 'clock_widget'):
                self.root.clock_widget.update_clock()
        except Exception as e:
            self._show_status(f"Ayarlar kaydedilemedi: {e}", "danger")

    def _show_status(self, msg, alert_type="primary"):
        """Durum mesajını göster"""
        self.status.configure(
            text=msg,
            bootstyle=alert_type
        )
        # 3 saniye sonra mesajı temizle
        self.window.after(3000, lambda: self.status.configure(text=""))


if __name__ == "__main__":
    try:
        tools = Tools()
        tools.configure_logging("INFO")
        logger.info("-------Program başlatıldı-------")

        # root = tk.Tk() yerine
        root = ttk.Window(themename="darkly")
        root.withdraw()  # Ana pencereyi gizle
        clock_widget = ClockWidget(root)
        root.clock_widget = clock_widget  # ClockWidget'a referans ekle
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Program kapatıldı")
    except Exception as e:
        logger.error(f"Program başlatılırken hata oluştu: {e}")
        raise
