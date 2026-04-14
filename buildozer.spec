[app]
# (str) Title of your application
title = Zamanai Explorer

# (str) Package name
package.name = zamanaiexplorer

# (str) Package domain (needed for unique ID)
package.domain = org.zamanai

# (list) Application requirements
# Added jnius for file opening and kivymd for the Google look
requirements = python3, kivy==2.3.1, kivymd==1.2.0, pillow, jnius

# (list) Permissions
# These are the "Secure" keys that let you open files
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (bool) Indentify as a file provider (Crucial for "Open With")
android.manifest.xml = 1

# (list) The "Two Icon" trick
# This tells Android to create the second shortcut
android.manifest.intent_filters = [ { "name": "Zamanai File Opener", "action": "android.intent.action.VIEW", "category": "android.intent.category.DEFAULT", "data": { "scheme": "file" } } ]
