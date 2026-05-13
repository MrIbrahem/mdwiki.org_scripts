# تحليل: import-history (استيراد التاريخ من enwiki)

## PHP: `php/import-history.php`

### المدخلات (Parameters)

| المتغير | المصدر | النوع | الوصف |
|----------|--------|------|-------------|
| `test` | `$_GET` أو `$_POST` | hidden | وضع الاختبار (value="1") |
| `from` | `$_GET` أو `$_POST` | text | اللغة المصدر (اختياري، مع title فقط) |
| `title` | `$_GET` أو `$_POST` | text | عنوان صفحة واحدة |
| `titlelist` | `$_GET` أو `$_POST` | textarea | قائمة عناوين (بديل عن title) |

### الصلاحيات

- المستخدمون المصرح لهم فقط: `Doc James`, `Mr. Ibrahem`
- غير المصرح لهم يرون رسالة "Access denied"

### سير العمل

1. يعرض نموذج POST مع:
   - حقل `title` أو `titlelist` (textarea)
   - حقل `from` اختياري (للغة المصدر)
2. عند الإرسال والمستخدم مصرح:
   - **إذا كان title غير فارغ:**
     - يبني الأمر: `imp.py -page:urlencoded_title -from:urlencoded_from save`
   - **إذا كان titlelist غير فارغ:**
     - يكتب القائمة لملف `importlist.txt`
     - يبني الأمر: `imp.py -file:path save`
   - ينفذ عبر `do_tfj_sh()`

## Python: `python/imp.py`

### آلية العمل

1. يستورد تاريخ الصفحة من `family="wikipedia"` إلى `family="mdwiki"`
2. إذا نجح الاستيراد (>0 revisions):
   - يحفظ الصفحة مجدداً لاستعادة النص بعد الاستيراد
   - إذا فشل الحفظ → يحفظ في `User:Mr._Ibrahem/title`
3. وسائط CLI المدعومة:
   - `-page:title`, `-page2:title` — عنوان مفرد
   - `-file:path` — ملف قائمة
   - `-from:LANG` — لغة المصدر
   - `-newpages:N`, `-user:NAME`, `-start:X`, `-ns:N`, `search:TERM`
   - `-offset:N`, `-limit:N`

### المعادلات

| PHP | Python CLI |
|-----|-----------|
| `$_GET/POST['title']` | `-page:urlencoded_title` |
| `$_GET/POST['from']` | `-from:urlencoded_value` |
| `$_GET/POST['titlelist']` | `-file:importlist.txt` |
| `test=1` | `test` في `do_tfj_sh` params |

---

## رؤية النقل إلى Flask

### ملف route الحالي: `flask_app/main_app/app_routes/import_history.py`

```
GET  /import-history/  → عرض النموذج
POST /import-history/  → استقبال ومعالجة
```

### ما يحتاج تكملة

1. **استدعاء `imp.py` مباشرة**
   - استيراد `work()` من `imp.py`
   - فصل بناء قائمة الصفحات عن `sys.argv`
2. **نظام الصلاحيات** — دمج مع Flask-Login وصلاحيات المستخدمين
3. **دعم `from`** — إضافة حقل اللغة المصدر مع قائمة منسدلة
4. **التعامل مع الملفات** — استبدال كتابة الملفات بتمرير القائمة مباشرة
