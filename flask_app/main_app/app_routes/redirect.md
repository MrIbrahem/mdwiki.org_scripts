# تحليل: redirect (إنشاء التحويلات)

## PHP: `php/redirect.php`

### المدخلات (Parameters)

| المتغير | المصدر | النوع | الوصف |
|----------|--------|------|-------------|
| `test` | `$_GET` أو `$_POST` | hidden | وضع الاختبار (value="1") |
| `title` | `$_GET` أو `$_POST` | text | عنوان صفحة واحدة |
| `titlelist` | `$_GET` أو `$_POST` | textarea | قائمة عناوين (بديل عن title) |

### سير العمل

1. يعرض نموذج POST مع:
   - حقل `title` (نص)
   - أو `titlelist` (textarea)
2. عند الإرسال والمستخدم مسجل:
   - **إذا كان title غير فارغ:**
     - يبني الأمر: `red.py -page2:urlencoded_title save`
   - **إذا كان titlelist غير فارغ:**
     - يكتب القائمة لملف `redirectlist.txt`
     - يبني الأمر: `red.py -file:path save`
   - ينفذ عبر `do_tfj_sh()`

## Python: `python/red.py`

### آلية العمل

1. لكل صفحة يستدعي `work(title, num, length)`:
   - يتحقق من وجود الصفحة في mdwiki
   - يستدعي `get_red(title)` لجلب التحويلات من enwiki
   - لكل تحويلة غير موجودة في mdwiki:
     - يتحقق من صلاحية العنوان (`valid_title`)
     - ينشئ صفحة تحويل `#redirect [[title]]`
2. `get_red(title)`:
   - يستعلم API الإنجليزية لجلب قائمة التحويلات لصفحة معينة
   - يرجع العناوين التي في namespace 0 فقط

### وسائط CLI المدعومة

- `-page2:title`, `-page:title` — عنوان مفرد
- `-file:path` — ملف قائمة
- `-newpages:N`, `-user:NAME`, `-start:X`, `-ns:N`, `search:TERM`

### المعادلات

| PHP | Python CLI |
|-----|-----------|
| `$_GET/POST['title']` | `-page2:urlencoded_title` |
| `$_GET/POST['titlelist']` | `-file:redirectlist.txt` |
| `test=1` | `test` في `do_tfj_sh` params |

---

## رؤية النقل إلى Flask

### ملف route الحالي: `flask_app/main_app/app_routes/redirect.py`

```
GET  /redirect/  → عرض النموذج
POST /redirect/  → استقبال ومعالجة
```

### ما يحتاج تكملة

1. **استدعاء `red.py` مباشرة**
   - استيراد `work()` و `get_red()` من `red.py`
   - تمرير العنوان مباشرة دون CLI
2. **التعامل مع الملفات** — استبدال `redirectlist.txt` بتمرير القائمة مباشرة
3. **إضافة دعم الصفحات الجديدة** — `-newpages` و `-usercontribs`
