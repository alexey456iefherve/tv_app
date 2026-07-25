[app]
title = My TV App
package.name = tvapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,m3u
version = 0.1
requirements = python3,kivy==2.3.0

orientation = landscape
fullscreen = 1

# Явно задаем стабильные версии для сборщика
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = armeabi-v7a, arm64-v8a
android.allow_backup = True

# Ключевой интент для Android TV
android.manifest.intent_filters = [ {"name": "android.intent.action.MAIN", "category": ["android.intent.category.LEANBACK_LAUNCHER", "android.intent.category.LAUNCHER"]} ]

[buildozer]
log_level = 2
warn_on_root = 1

