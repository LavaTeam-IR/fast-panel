import os
import uuid
import json
import time
import string
import random
import threading
import requests
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fast-gateway-secret-key-2026")

# File Paths
DATA_FILE = "data.json"

# Default Data Structure
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "config": {
                "password": "admin",
                "clean_ips": []
            },
            "inbounds": {},
            "traffic": {
                "total_usage": 0,
                "history": []
            }
        }
        save_data(default_data)
        return default_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "config": {"password": "admin", "clean_ips": []},
            "inbounds": {},
            "traffic": {"total_usage": 0, "history": []}
        }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Keep Alive Thread to prevent sleep on free hosting
def keep_alive():
    while True:
        try:
            # Self ping
            app_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("RAILWAY_STATIC_URL")
            if app_url:
                requests.get(app_url, timeout=5)
        except:
            pass
        time.sleep(600) # Every 10 minutes

threading.Thread(target=keep_alive, daemon=True).start()

# Generate VLESS Link Components
def generate_uuid():
    return str(uuid.uuid4())

# Base HTML Template with Blue Theme and Fast Identity
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fast Gateway | پنل مدیریت</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#eff6ff',
                            100: '#dbeafe',
                            200: '#bfdbfe',
                            300: '#93c5fd',
                            400: '#60a5fa',
                            500: '#3b82f6',
                            600: '#2563eb',
                            700: '#1d4ed8',
                            800: '#1e40af',
                            900: '#1e3a8a',
                        }
                    }
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;700&display=swap');
        body { font-family: 'Vazirmatn', sans-serif; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 dark:bg-slate-900 dark:text-slate-100 h-full transition-colors duration-200">
    <div class="flex h-full overflow-hidden">
        <!-- Sidebar -->
        <div class="w-64 bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 flex flex-col justify-between hidden md:flex z-20">
            <div>
                <div class="p-6 flex items-center gap-3 border-b border-slate-100 dark:border-slate-700">
                    <div class="bg-brand-600 text-white p-2 rounded-xl shadow-lg shadow-brand-500/30">
                        <i class="fas fa-bolt text-xl animate-pulse"></i>
                    </div>
                    <div>
                        <h1 class="text-lg font-bold text-slate-900 dark:text-white">Fast Gateway</h1>
                        <span class="text-xs text-brand-600 dark:text-brand-400 font-medium">تونل هوشمند وب‌ساکت</span>
                    </div>
                </div>
                <nav class="p-4 space-y-1">
                    <a href="{{ url_for('dashboard') }}" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all {% if active_page == 'dashboard' %} bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-400 font-bold {% else %} text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 {% endif %}">
                        <i class="fas fa-chart-pie w-5 text-center"></i> <span>داشبورد</span>
                    </a>
                    <a href="{{ url_for('inbounds') }}" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all {% if active_page == 'inbounds' %} bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-400 font-bold {% else %} text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 {% endif %}">
                        <i class="fas fa-link w-5 text-center"></i> <span>مدیریت اتصال‌ها</span>
                    </a>
                    <a href="{{ url_for('clean_ips') }}" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all {% if active_page == 'clean_ips' %} bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-400 font-bold {% else %} text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 {% endif %}">
                        <i class="fas fa-globe w-5 text-center"></i> <span>آی‌پی‌های تمیز</span>
                    </a>
                    <a href="{{ url_for('security') }}" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all {% if active_page == 'security' %} bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-400 font-bold {% else %} text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 {% endif %}">
                        <i class="fas fa-shield-alt w-5 text-center"></i> <span>امنیت پنل</span>
                    </a>
                </nav>
            </div>
            <div class="p-4 border-t border-slate-100 dark:border-slate-700 space-y-2">
                <button onclick="toggleDarkMode()" class="w-full flex items-center justify-between px-4 py-2.5 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-all text-sm">
                    <span>حالت شب / روز</span>
                    <i class="fas fa-moon dark:hidden"></i>
                    <i class="fas fa-sun hidden dark:block text-amber-500"></i>
                </button>
                <a href="{{ url_for('logout') }}" class="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-all text-sm font-medium">
                    <i class="fas fa-sign-out-alt"></i> <span>خروج از پنل</span>
                </a>
            </div>
        </div>

        <!-- Main Content Area -->
        <div class="flex-1 flex flex-col h-full overflow-hidden">
            <!-- Top Header -->
            <header class="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4 flex justify-between items-center z-10">
                <div class="flex items-center gap-4">
                    <button class="md:hidden text-slate-600 dark:text-slate-400 text-xl" onclick="toggleMobileMenu()">
                        <i class="fas fa-bars"></i>
                    </button>
                    <h2 class="text-xl font-bold text-slate-800 dark:text-white">{% block page_title %}{% endblock %}</h2>
                </div>
                <div class="flex items-center gap-4">
                    <div class="text-left hidden sm:block">
                        <p class="text-xs text-slate-400 dark:text-slate-500">وضعیت سرور</p>
                        <p class="text-sm font-semibold text-emerald-500 flex items-center gap-1.5 justify-end">
                            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span> آنلاین
                        </p>
                    </div>
                </div>
            </header>

            <!-- Main Scrollable Area -->
            <main class="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-slate-900">
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>

    <!-- Mobile Menu Overlay -->
    <div id="mobileMenu" class="fixed inset-0 bg-slate-950/50 backdrop-blur-sm z-50 hidden transition-all" onclick="toggleMobileMenu()">
        <div class="w-64 bg-white dark:bg-slate-800 h-full p-6 flex flex-col justify-between" onclick="event.stopPropagation()">
            <div>
                <div class="flex items-center justify-between mb-8">
                    <div class="flex items-center gap-2">
                        <i class="fas fa-bolt text-brand-600 text-2xl"></i>
                        <span class="text-lg font-bold dark:text-white">Fast Gateway</span>
                    </div>
                    <button onclick="toggleMobileMenu()"><i class="fas fa-times text-xl"></i></button>
                </div>
                <nav class="space-y-2">
                    <a href="{{ url_for('dashboard') }}" class="flex items-center gap-3 px-4 py-3 rounded-xl {% if active_page == 'dashboard' %} bg-brand-50 text-brand-600 dark:bg-brand-950/50 {% endif %}">
                        <i class="fas fa-chart-pie"></i> <span>داشبورد</span>
                    </a>
                    <a href="{{ url_for('inbounds') }}" class="flex items-center gap-3 px-4 py-3 rounded-xl {% if active_page == 'inbounds' %} bg-brand-50 text-brand-600 dark:bg-brand-950/50 {% endif %}">
                        <i class="fas fa-link"></i> <span>اتصال‌ها</span>
                    </a>
                    <a href="{{ url_for('clean_ips') }}" class="flex items-center gap-3 px-4 py-3 rounded-xl {% if active_page == 'clean_ips' %} bg-brand-50 text-brand-600 dark:bg-brand-950/50 {% endif %}">
                        <i class="fas fa-globe"></i> <span>آی‌پی‌های تمیز</span>
                    </a>
                    <a href="{{ url_for('security') }}" class="flex items-center gap-3 px-4 py-3 rounded-xl {% if active_page == 'security' %} bg-brand-50 text-brand-600 dark:bg-brand-950/50 {% endif %}">
                        <i class="fas fa-shield-alt"></i> <span>امنیت</span>
                    </a>
                </nav>
            </div>
            <div class="space-y-4">
                <button onclick="toggleDarkMode()" class="w-full flex items-center justify-between px-4 py-2 border rounded-xl dark:text-white">
                    <span>پوسته شب</span> <i class="fas fa-moon"></i>
                </button>
                <a href="{{ url_for('logout') }}" class="block text-center py-2.5 bg-rose-600 text-white rounded-xl">خروج</a>
            </div>
        </div>
    </div>

    <script>
        if (localStorage.getItem('darkMode') === 'true' || (!('darkMode' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }

        function toggleDarkMode() {
            const isDark = document.documentElement.classList.toggle('dark');
            localStorage.setItem('darkMode', isDark);
        }

        function toggleMobileMenu() {
            document.getElementById('mobileMenu').classList.toggle('hidden');
        }
    </script>
</body>
</html>
"""

# LOGIN PAGE
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>ورود به پنل Fast Gateway</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap'); body{font-family:'Vazirmatn',sans-serif;}</style>
</head>
<body class="bg-slate-900 flex items-center justify-center min-h-screen p-4">
    <div class="w-full max-w-md bg-slate-800 rounded-3xl p-8 border border-slate-700 shadow-2xl relative overflow-hidden">
        <div class="absolute -top-10 -right-10 w-40 h-40 bg-blue-600/10 rounded-full blur-2xl"></div>
        <div class="absolute -bottom-10 -left-10 w-40 h-40 bg-blue-500/10 rounded-full blur-2xl"></div>
        
        <div class="text-center mb-8">
            <div class="inline-flex bg-blue-600 text-white p-4 rounded-2xl shadow-xl shadow-blue-600/20 mb-4">
                <i class="fas fa-bolt text-3xl"></i>
            </div>
            <h1 class="text-2xl font-bold text-white">خوش آمدید</h1>
            <p class="text-slate-400 text-sm mt-1">مدیریت تونل هوشمند Fast Gateway</p>
        </div>

        {% if error %}
        <div class="bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl p-3 text-sm text-center mb-4">
            {{ error }}
        </div>
        {% endif %}

        <form method="POST" class="space-y-5">
            <div>
                <label class="block text-slate-300 text-sm mb-2 font-medium">رمز عبور پنل</label>
                <div class="relative">
                    <input type="password" name="password" required placeholder="••••••••" class="w-full bg-slate-900 border border-slate-700 text-white rounded-xl py-3 px-4 pr-11 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-center placeholder-slate-600">
                    <i class="fas fa-lock absolute right-4 top-4 text-slate-500"></i>
                </div>
            </div>
            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-blue-600/20 transition-all">ورود به حساب</button>
        </form>
    </div>
</body>
</html>
"""

# DASHBOARD PAGE
DASHBOARD_CONTENT = """
{% extends "base" %}
{% block page_title %}داشبورد سیستم{% endblock %}
{% block content %}
<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
    <div class="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 flex items-center justify-between shadow-sm">
        <div>
            <p class="text-slate-400 text-sm font-medium">کل کاربران</p>
            <h3 class="text-2xl font-bold dark:text-white mt-1">{{ total_users }}</h3>
        </div>
        <div class="bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 p-4 rounded-xl text-xl"><i class="fas fa-users"></i></div>
    </div>
    <div class="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 flex items-center justify-between shadow-sm">
        <div>
            <p class="text-slate-400 text-sm font-medium">ترافیک کل مصرفی</p>
            <h3 class="text-2xl font-bold dark:text-white mt-1">{{ total_traffic }} GB</h3>
        </div>
        <div class="bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 p-4 rounded-xl text-xl"><i class="fas fa-chart-line"></i></div>
    </div>
    <div class="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 flex items-center justify-between shadow-sm">
        <div>
            <p class="text-slate-400 text-sm font-medium">آی‌پی‌های تمیز فعال</p>
            <h3 class="text-2xl font-bold dark:text-white mt-1">{{ clean_ips_count }}</h3>
        </div>
        <div class="bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 p-4 rounded-xl text-xl"><i class="fas fa-server"></i></div>
    </div>
    <div class="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 flex items-center justify-between shadow-sm">
        <div>
            <p class="text-slate-400 text-sm font-medium">نوع اتصال</p>
            <h3 class="text-lg font-bold text-blue-600 dark:text-blue-400 mt-1">VLESS + WS</h3>
        </div>
        <div class="bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 p-4 rounded-xl text-xl"><i class="fas fa-network-wired"></i></div>
    </div>
</div>

<div class="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
    <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
        <i class="fas fa-chart-area text-blue-600"></i> نمودار مصرف ترافیک سیستم
    </h3>
    <div class="h-80 w-full">
        <canvas id="trafficChart"></canvas>
    </div>
</div>

<script>
    const ctx = document.getElementById('trafficChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: {{ chart_labels | tojson }},
            datasets: [{
                label: 'مصرف (گیگابایت)',
                data: {{ chart_data | tojson }},
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.05)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                x: { grid: { display: false } }
            }
        }
    });
</script>
{% endblock %}
"""

# INBOUNDS (USERS) PAGE
INBOUNDS_CONTENT = """
{% extends "base" %}
{% block page_title %}مدیریت اتصال‌های VLESS{% endblock %}
{% block content %}
<div class="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm mb-6">
    <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-4"><i class="fas fa-user-plus text-blue-600 ml-2"></i>ساخت کاربر جدید</h3>
    <form action="{{ url_for('create_inbound') }}" method="POST" class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
        <div>
            <label class="block text-sm font-medium text-slate-400 mb-2">نام یا شناسه کاربر</label>
            <input type="text" name="remark" required placeholder="مثال: Ali-Laptop" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 focus:outline-none focus:border-blue-500 dark:text-white">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-400 mb-2">حجم محدودیت (گیگابایت)</label>
            <input type="number" name="total_gb" required value="50" min="1" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 focus:outline-none focus:border-blue-500 dark:text-white">
        </div>
        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-xl transition-all shadow-md shadow-blue-600/10"><i class="fas fa-plus ml-2"></i>ایجاد اتصال</button>
    </form>
</div>

<div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
    <div class="p-6 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
        <h3 class="text-lg font-bold text-slate-800 dark:text-white">لیست اکانت‌ها</h3>
        <span class="bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 text-xs px-3 py-1.5 rounded-lg font-bold">{{ inbounds|length }} اکانت</span>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full text-right border-collapse">
            <thead>
                <tr class="bg-slate-50 dark:bg-slate-900/50 text-slate-400 text-sm font-medium border-b border-slate-100 dark:border-slate-700">
                    <th class="p-4">کاربر</th>
                    <th class="p-4">شناسه یکتا (UUID)</th>
                    <th class="p-4">میزان مصرف / سقف</th>
                    <th class="p-4">وضعیت</th>
                    <th class="p-4 text-left">عملیات مدیریت</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-700/50">
                {% for id, item in inbounds.items() %}
                <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                    <td class="p-4 font-bold text-slate-800 dark:text-white">{{ item.remark }}</td>
                    <td class="p-4 text-xs font-mono text-slate-500 select-all">{{ item.uuid }}</td>
                    <td class="p-4">
                        <div class="flex items-center gap-2">
                            <span class="text-sm font-bold">{{ item.used_gb | round(2) }}</span>
                            <span class="text-slate-400 text-xs">/ {{ item.total_gb }} GB</span>
                        </div>
                    </td>
                    <td class="p-4">
                        {% if item.enable %}
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">✅ فعال</span>
                        {% else %}
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400">❌ غیرفعال</span>
                        {% endif %}
                    </td>
                    <td class="p-4 text-left space-x-1 space-x-reverse">
                        <button onclick="copyConfig('{{ item.uuid }}', '{{ item.remark }}')" class="bg-blue-50 hover:bg-blue-100 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400 p-2 rounded-lg text-sm" title="کپی کانفیگ"><i class="fas fa-copy"></i></button>
                        <a href="{{ url_for('toggle_inbound', id=id) }}" class="inline-block bg-amber-50 hover:bg-amber-100 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400 p-2 rounded-lg text-sm" title="تغییر وضعیت"><i class="fas fa-power-off"></i></a>
                        <a href="{{ url_for('delete_inbound', id=id) }}" onclick="return confirm('آیا از حذف این کاربر مطمئن هستید؟')" class="inline-block bg-rose-50 hover:bg-rose-100 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 p-2 rounded-lg text-sm" title="حذف"><i class="fas fa-trash-alt"></i></a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<script>
    function copyConfig(uuid, remark) {
        const host = window.location.hostname;
        const config = `vless://${uuid}@${host}:443?path=%2Ffast-ws&security=tls&encryption=none&type=ws#Fast-${remark}`;
        navigator.clipboard.writeText(config);
        alert('کانفیگ VLESS با موفقیت کپی شد.');
    }
</script>
{% endblock %}
"""

# CLEAN IP PAGE
CLEAN_IP_CONTENT = """
{% extends "base" %}
{% block page_title %}مدیریت آی‌پی‌های تمیز Cloudflare{% endblock %}
{% block content %}
<div class="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm mb-6">
    <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-4"><i class="fas fa-plus-circle text-blue-600 ml-2"></i>افزودن آی‌پی یا دامنه تمیز</h3>
    <form action="{{ url_for('add_clean_ip') }}" method="POST" class="flex gap-4">
        <input type="text" name="ip" required placeholder="مثال: 104.21.43.5 یا clean.domain.com" class="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 focus:outline-none focus:border-blue-500 dark:text-white">
        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-6 py-2.5 rounded-xl transition-all shadow-md shadow-blue-600/10">ثبت آی‌پی</button>
    </form>
</div>

<div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
    <div class="p-6 border-b border-slate-100 dark:border-slate-700">
        <h3 class="text-lg font-bold text-slate-800 dark:text-white">آی‌پی‌های ثبت شده</h3>
    </div>
    {% if ips %}
    <div class="divide-y divide-slate-100 dark:divide-slate-700/50">
        {% for ip in ips %}
        <div class="p-4 flex justify-between items-center hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-all">
            <span class="font-mono font-bold text-slate-700 dark:text-slate-300">{{ ip }}</span>
            <a href="{{ url_for('delete_clean_ip', ip=ip) }}" class="bg-rose-50 hover:bg-rose-100 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 p-2 rounded-lg text-sm"><i class="fas fa-trash-alt"></i></a>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="p-8 text-center text-slate-400">هیچ آی‌پی تمیزی تعریف نشده است. سیستم به صورت پیش‌فرض از دامنه اصلی استفاده می‌کند.</div>
    {% endif %}
</div>
{% endblock %}
"""

# SECURITY PAGE
SECURITY_CONTENT = """
{% extends "base" %}
{% block page_title %}تنظیمات امنیت و رمز عبور پنل{% endblock %}
{% block content %}
<div class="max-w-xl mx-auto bg-white dark:bg-slate-800 p-8 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
    <div class="text-center mb-6">
        <div class="bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 p-4 inline-block rounded-full text-2xl mb-2"><i class="fas fa-user-lock"></i></div>
        <h3 class="text-lg font-bold dark:text-white">تغییر پسورد مدیریت</h3>
        <p class="text-sm text-slate-400 mt-1">برای امنیت بیشتر رمز عبور پیش‌فرض ادمین را عوض کنید.</p>
    </div>

    {% if success %}
    <div class="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl p-3 text-sm text-center mb-4">رمز عبور با موفقیت تغییر یافت.</div>
    {% endif %}

    <form method="POST" class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-slate-400 mb-2">رمز عبور جدید</label>
            <input type="password" name="new_password" required placeholder="••••••••" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 focus:outline-none focus:border-blue-500 text-center dark:text-white">
        </div>
        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-all shadow-md shadow-blue-600/10">بروزرسانی کلمه عبور</button>
    </form>
</div>
{% endblock %}
"""

# Context processor for Jinja templates
@app.context_processor
def inject_global_template():
    return dict(render_template_string=render_template_string)

# HELPER ROUTES & MIDDLEWARE
def is_logged_in():
    return session.get("auth") === True

@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        data = load_data()
        if request.form.get("password") == data["config"]["password"]:
            session["auth"] = True
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_TEMPLATE, error="رمز عبور وارد شده اشتباه است.")
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route("/logout")
def logout():
    session.pop("auth", None)
    return redirect(url_for("login"))

@app.route("/")
@app.route("/dashboard")
def dashboard():
    if not is_logged_in(): return redirect(url_for("login"))
    data = load_data()
    
    # Calculate mock history data for the chart layout
    chart_labels = [(datetime.now() - timedelta(days=i)).strftime("%m/%d") for i in range(6, -1, -1)]
    chart_data = [random.randint(5, 25) for _ in range(7)]
    
    return render_template_string(
        BASE_TEMPLATE, 
        active_page="dashboard", 
        content=render_template_string(
            DASHBOARD_CONTENT, 
            total_users=len(data["inbounds"]),
            total_traffic=round(data["traffic"]["total_usage"], 2),
            clean_ips_count=len(data["config"]["clean_ips"]),
            chart_labels=chart_labels,
            chart_data=chart_data
        )
    )

@app.route("/inbounds")
def inbounds():
    if not is_logged_in(): return redirect(url_for("login"))
    data = load_data()
    return render_template_string(BASE_TEMPLATE, active_page="inbounds", content=render_template_string(INBOUNDS_CONTENT, inbounds=data["inbounds"]))

@app.route("/inbounds/create", methods=["POST"])
def create_inbound():
    if not is_logged_in(): return redirect(url_for("login"))
    remark = request.form.get("remark")
    total_gb = int(request.form.get("total_gb", 50))
    
    data = load_data()
    user_id = str(int(time.time()))
    data["inbounds"][user_id] = {
        "remark": remark,
        "uuid": generate_uuid(),
        "total_gb": total_gb,
        "used_gb": 0.0,
        "enable": True
    }
    save_data(data)
    return redirect(url_for("inbounds"))

@app.route("/inbounds/toggle/<id>")
def toggle_inbound(id):
    if not is_logged_in(): return redirect(url_for("login"))
    data = load_data()
    if id in data["inbounds"]:
        data["inbounds"][id]["enable"] = not data["inbounds"][id]["enable"]
        save_data(data)
    return redirect(url_for("inbounds"))

@app.route("/inbounds/delete/<id>")
def delete_inbound(id):
    if not is_logged_in(): return redirect(url_for("login"))
    data = load_data()
    if id in data["inbounds"]:
        del data["inbounds"][id]
        save_data(data)
    return redirect(url_for("inbounds"))

@app.route("/clean-ips", methods=["GET", "POST"])
def clean_ips():
    if not is_logged_in(): return redirect(url_for("login"))
    data = load_data()
    return render_template_string(BASE_TEMPLATE, active_page="clean_ips", content=render_template_string(CLEAN_IP_CONTENT, ips=data["config"]["clean_ips"]))

@app.route("/clean-ips/add", methods=["POST"])
def add_clean_ip():
    if not is_logged_in(): return redirect(url_for("login"))
    ip = request.form.get("ip").strip()
    data = load_data()
    if ip and ip not in data["config"]["clean_ips"]:
        data["config"]["clean_ips"].append(ip)
        save_data(data)
    return redirect(url_for("clean_ips"))

@app.route("/clean-ips/delete/<ip>")
def delete_clean_ip(ip):
    if not is_logged_in(): return redirect(url_for("login"))
    data = load_data()
    if ip in data["config"]["clean_ips"]:
        data["config"]["clean_ips"].remove(ip)
        save_data(data)
    return redirect(url_for("clean_ips"))

@app.route("/security", methods=["GET", "POST"])
def security():
    if not is_logged_in(): return redirect(url_for("login"))
    success = False
    if request.method == "POST":
        new_password = request.form.get("new_password")
        data = load_data()
        data["config"]["password"] = new_password
        save_data(data)
        success = True
    return render_template_string(BASE_TEMPLATE, active_page="security", content=render_template_string(SECURITY_CONTENT, success=success))

# WebSocket / Tunnel Mock Connection Path
@app.route("/fast-ws")
def ws_tunnel():
    # This route simulates the WebSocket tunnel communication endpoint
    return "Fast Gateway WebSocket Active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

