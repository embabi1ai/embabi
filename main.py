import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
import sqlite3
from datetime import datetime

DB_NAME = "poultry.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            initial_count INTEGER,
            start_date TEXT,
            target_temp TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mortality (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            count INTEGER,
            notes TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            bags INTEGER,
            weight_per_bag REAL,
            total_kg REAL,
            shift TEXT,
            responsible TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS litter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            carts INTEGER,
            worker TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empty_bags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            count INTEGER,
            responsible TEXT,
            notes TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            worker_name TEXT,
            status TEXT,
            wage REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            start_date TEXT,
            duration INTEGER,
            reminder_time TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            due_date TEXT,
            responsible TEXT,
            status TEXT
        )
    """)
    cursor.execute('SELECT COUNT(*) FROM flock')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO flock (initial_count, start_date, target_temp) VALUES (4500, ?, ?)', 
                       (datetime.now().strftime("%Y-%m-%d"), "32°C"))
    conn.commit()
    conn.close()

init_db()

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        header = Label(text="مساعد العنبر - Poultry Assistant", font_size='22sp', bold=True, size_hint_y=None, height=50)
        layout.add_widget(header)
        
        self.stats_label = Label(text="جاري تحميل الإحصائيات...", font_size='16sp', halign='center', valign='middle')
        self.stats_label.bind(size=self.stats_label.setter('text_size'))
        layout.add_widget(self.stats_label)
        
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=350)
        
        btn_flock = Button(text="دورة التربية", background_color=get_color_from_hex('#1b4d3e'))
        btn_flock.bind(on_press=lambda x: setattr(self.manager, 'current', 'flock'))
        
        btn_mortality = Button(text="قسم النافق", background_color=get_color_from_hex('#1b4d3e'))
        btn_mortality.bind(on_press=lambda x: setattr(self.manager, 'current', 'mortality'))
        
        btn_feed = Button(text="قسم العلف", background_color=get_color_from_hex('#1b4d3e'))
        btn_feed.bind(on_press=lambda x: setattr(self.manager, 'current', 'feed'))
        
        btn_litter = Button(text="قسم السبلة", background_color=get_color_from_hex('#1b4d3e'))
        btn_litter.bind(on_press=lambda x: setattr(self.manager, 'current', 'litter'))
        
        btn_workers = Button(text="العمال والأجور", background_color=get_color_from_hex('#1b4d3e'))
        btn_workers.bind(on_press=lambda x: setattr(self.manager, 'current', 'workers'))
        
        btn_tasks = Button(text="قسم المهام", background_color=get_color_from_hex('#1b4d3e'))
        btn_tasks.bind(on_press=lambda x: setattr(self.manager, 'current', 'tasks'))

        grid.add_widget(btn_flock)
        grid.add_widget(btn_mortality)
        grid.add_widget(btn_feed)
        grid.add_widget(btn_litter)
        grid.add_widget(btn_workers)
        grid.add_widget(btn_tasks)
        
        layout.add_widget(grid)
        
        refresh_btn = Button(text="تحديث البيانات", size_hint_y=None, height=45, background_color=get_color_from_hex('#2e7d32'))
        refresh_btn.bind(on_press=lambda x: self.update_stats())
        layout.add_widget(refresh_btn)
        
        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self.update_stats(), 0.5)
        
    def update_stats(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT initial_count, start_date, target_temp FROM flock LIMIT 1")
        flock = cursor.fetchone()
        initial = flock[0] if flock else 4500
        start_date = datetime.strptime(flock[1], "%Y-%m-%d") if flock else datetime.now()
        age = (datetime.now() - start_date).days + 1
        
        cursor.execute("SELECT SUM(count) FROM mortality")
        total_mort = cursor.fetchone()[0] or 0
        remaining = initial - total_mort
        
        cursor.execute("SELECT SUM(total_kg) FROM feed")
        total_feed = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(carts) FROM litter")
        total_litter = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(wage) FROM workers")
        total_wages = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        self.stats_label.text = (f"عمر الدورة: {age} يوم\n"
                                 f"الفراخ الحالية: {remaining} | البداية: {initial}\n"
                                 f"إجمالي النافق: {total_mort}\n"
                                 f"إجمالي العلف: {total_feed:.1f} كجم\n"
                                 f"إجمالي السبلة: {total_litter} عربية\n"
                                 f"إجمالي أجور العمال: {total_wages:.1f} جنيه")

class FlockScreen(Screen):
    def __init__(self, **kwargs):
        super(FlockScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="إدارة دورة التربية", font_size='20sp', size_hint_y=None, height=40))
        
        self.count_input = TextInput(hint_text="عدد الكتاكيت للبداية", multiline=False, size_hint_y=None, height=45)
        self.temp_input = TextInput(hint_text="درجة الحرارة المستهدفة", multiline=False, size_hint_y=None, height=45)
        
        layout.add_widget(self.count_input)
        layout.add_widget(self.temp_input)
        
        save_btn = Button(text="حفظ التعديلات", size_hint_y=None, height=45, background_color=get_color_from_hex('#1b4d3e'))
        save_btn.bind(on_press=self.save_flock)
        layout.add_widget(save_btn)
        
        back_btn = Button(text="العودة للرئيسية", size_hint_y=None, height=45)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def save_flock(self, instance):
        try:
            count = int(self.count_input.text)
            temp = self.temp_input.text
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE flock SET initial_count=?, target_temp=? WHERE id=1", (count, temp))
            conn.commit()
            conn.close()
            self.manager.current = 'main'
        except Exception as e:
            print("Error:", e)

class MortalityScreen(Screen):
    def __init__(self, **kwargs):
        super(MortalityScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="تسجيل النافق اليومي", font_size='20sp', size_hint_y=None, height=40))
        
        self.mort_input = TextInput(hint_text="عدد النافق اليوم", multiline=False, size_hint_y=None, height=45)
        self.notes_input = TextInput(hint_text="ملاحظات اختيارية", multiline=False, size_hint_y=None, height=45)
        
        layout.add_widget(self.mort_input)
        layout.add_widget(self.notes_input)
        
        save_btn = Button(text="تسجيل النافق", size_hint_y=None, height=45, background_color=get_color_from_hex('#1b4d3e'))
        save_btn.bind(on_press=self.save_mortality)
        layout.add_widget(save_btn)
        
        back_btn = Button(text="العودة للرئيسية", size_hint_y=None, height=45)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def save_mortality(self, instance):
        try:
            count = int(self.mort_input.text)
            notes = self.notes_input.text
            date = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO mortality (date, count, notes) VALUES (?, ?, ?)", (date, count, notes))
            conn.commit()
            conn.close()
            self.manager.current = 'main'
        except Exception as e:
            print("Error:", e)

class FeedScreen(Screen):
    def __init__(self, **kwargs):
        super(FeedScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="قسم العلف والاستهلاك", font_size='20sp', size_hint_y=None, height=40))
        
        self.bags_input = TextInput(hint_text="عدد الشكاير", multiline=False, size_hint_y=None, height=45)
        self.weight_input = TextInput(hint_text="وزن الشيكارة (كجم)", multiline=False, size_hint_y=None, height=45)
        self.resp_input = TextInput(hint_text="اسم المسؤول", multiline=False, size_hint_y=None, height=45)
        
        layout.add_widget(self.bags_input)
        layout.add_widget(self.weight_input)
        layout.add_widget(self.resp_input)
        
        save_btn = Button(text="تسجيل العلف", size_hint_y=None, height=45, background_color=get_color_from_hex('#1b4d3e'))
        save_btn.bind(on_press=self.save_feed)
        layout.add_widget(save_btn)
        
        back_btn = Button(text="العودة للرئيسية", size_hint_y=None, height=45)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def save_feed(self, instance):
        try:
            bags = int(self.bags_input.text)
            weight = float(self.weight_input.text)
            total_kg = bags * weight
            resp = self.resp_input.text
            date = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feed (date, bags, weight_per_bag, total_kg, shift, responsible) VALUES (?, ?, ?, ?, ?, ?)",
                           (date, bags, weight, total_kg, "نهار", resp))
            conn.commit()
            conn.close()
            self.manager.current = 'main'
        except Exception as e:
            print("Error:", e)

class LitterScreen(Screen):
    def __init__(self, **kwargs):
        super(LitterScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="قسم السبلة والعربيات", font_size='20sp', size_hint_y=None, height=40))
        
        self.carts_input = TextInput(hint_text="عدد العربيات", multiline=False, size_hint_y=None, height=45)
        self.worker_input = TextInput(hint_text="اسم العامل المسؤول (ريعو، ربيع، علي)", multiline=False, size_hint_y=None, height=45)
        
        layout.add_widget(self.carts_input)
        layout.add_widget(self.worker_input)
        
        save_btn = Button(text="تسجيل السبلة", size_hint_y=None, height=45, background_color=get_color_from_hex('#1b4d3e'))
        save_btn.bind(on_press=self.save_litter)
        layout.add_widget(save_btn)
        
        back_btn = Button(text="العودة للرئيسية", size_hint_y=None, height=45)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def save_litter(self, instance):
        try:
            carts = int(self.carts_input.text)
            worker = self.worker_input.text
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO litter (date, carts, worker) VALUES (?, ?, ?)", (date, carts, worker))
            conn.commit()
            conn.close()
            self.manager.current = 'main'
        except Exception as e:
            print("Error:", e)

class WorkersScreen(Screen):
    def __init__(self, **kwargs):
        super(WorkersScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="أجور وحضور العمال", font_size='20sp', size_hint_y=None, height=40))
        
        self.worker_name = TextInput(hint_text="اسم العامل (ريعو، ربيع، علي، محمد أبو إسماعيل)", multiline=False, size_hint_y=None, height=45)
        self.status_input = TextInput(hint_text="الحالة (حضور / نصف / غياب)", multiline=False, size_hint_y=None, height=45)
        
        layout.add_widget(self.worker_name)
        layout.add_widget(self.status_input)
        
        save_btn = Button(text="تسجيل الحضور والأجر", size_hint_y=None, height=45, background_color=get_color_from_hex('#1b4d3e'))
        save_btn.bind(on_press=self.save_worker)
        layout.add_widget(save_btn)
        
        back_btn = Button(text="العودة للرئيسية", size_hint_y=None, height=45)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def save_worker(self, instance):
        try:
            name = self.worker_name.text
            status = self.status_input.text
            wage = 200.0 if "حضور" in status else (100.0 if "نصف" in status else 0.0)
            date = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO workers (date, worker_name, status, wage) VALUES (?, ?, ?, ?)", (date, name, status, wage))
            conn.commit()
            conn.close()
            self.manager.current = 'main'
        except Exception as e:
            print("Error:", e)

class TasksScreen(Screen):
    def __init__(self, **kwargs):
        super(TasksScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="قسم المهام", font_size='20sp', size_hint_y=None, height=40))
        
        self.title_input = TextInput(hint_text="عنوان المهمة", multiline=False, size_hint_y=None, height=45)
        self.resp_input = TextInput(hint_text="المسؤول", multiline=False, size_hint_y=None, height=45)
        
        layout.add_widget(self.title_input)
        layout.add_widget(self.resp_input)
        
        save_btn = Button(text="إضافة مهمة", size_hint_y=None, height=45, background_color=get_color_from_hex('#1b4d3e'))
        save_btn.bind(on_press=self.save_task)
        layout.add_widget(save_btn)
        
        back_btn = Button(text="العودة للرئيسية", size_hint_y=None, height=45)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def save_task(self, instance):
        try:
            title = self.title_input.text
            resp = self.resp_input.text
            date = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tasks (title, due_date, responsible, status) VALUES (?, ?, ?, ?)", (title, date, resp, "قيد التنفيذ"))
            conn.commit()
            conn.close()
            self.manager.current = 'main'
        except Exception as e:
            print("Error:", e)

class PoultryApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(FlockScreen(name='flock'))
        sm.add_widget(MortalityScreen(name='mortality'))
        sm.add_widget(FeedScreen(name='feed'))
        sm.add_widget(LitterScreen(name='litter'))
        sm.add_widget(WorkersScreen(name='workers'))
        sm.add_widget(TasksScreen(name='tasks'))
        return sm

if __name__ == '__main__':
    PoultryApp().run()
