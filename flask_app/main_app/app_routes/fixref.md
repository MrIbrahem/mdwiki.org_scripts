# تحليل: fixref (تطبيع المراجع)

## PHP: `php/fixref.php`

### المدخلات (Parameters)

| المتغير | المصدر | النوع | الوصف |
|----------|--------|------|-------------|
| `titlelist` | `$_GET` أو `$_POST` | textarea | قائمة عناوين (سطر لكل عنوان) |
| `number` | `$_GET` أو `$_POST` | number | عدد الصفحات للمعالجة (لـ allpages) |
| `test` | `$_GET` أو `$_POST` | hidden | وضع الاختبار (value="1") |

### سير العمل

1. يعرض نموذج POST مع:
   - حقل `number` (عدد الصفحات)
   - أو `titlelist` (textarea لقائمة العناوين)
2. عند الإرسال والمستخدم مسجل:
   - **إذا كان titlelist غير فارغ:**
     - عنوان واحد → `-title:escaped_title`
     - عدة عناوين → يكتبها لملف مؤقت ويستخدم `-file:path`
   - **إذا كان number غير فارغ:** → `allpages -number:N`
   - ينفذ عبر `do_tfj_sh()`: `fixref/start.py command save`

## Python: `python/fixref/start.py`

### آلية العمل

1. يقرأ وسائط CLI:
   - `-number:N` — عدد الصفحات
   - `-file:path` — ملف بقائمة العناوين
   - `allpages` — كل الصفحات
   - `-cat:Category` — صفحة تصنيف
   - `-page:title` أو `-title:title` — عنوان واحد
2. لكل صفحة:
   - يجلب النص
   - يستدعي `fix_ref_template()` لتطبيع المراجع
   - إذا تغير النص → يحفظ الصفحة
3. حد أقصى: `thenumbers[1]` (افتراضي 20000)

### المعادلات

| PHP | Python CLI |
|-----|-----------|
| `$_GET/POST['titlelist']` (سطر واحد) | `-title:escaped_title` |
| `$_GET/POST['titlelist']` (متعدد) | `-file:temp_file_path` |
| `$_GET/POST['number']` | `allpages -number:N` |
| `test=1` | `test` في `do_tfj_sh` params |

---

## رؤية النقل إلى Flask

### ملف route الحالي: `flask_app/main_app/app_routes/fixref.py`

```
GET  /fixref/  → عرض النموذج
POST /fixref/  → استقبال ومعالجة
```

### ما يحتاج تكملة

1. **استدعاء `fixref/start.py` مباشرة**
   - استيراد `work()` من `start.py`
   - فصل بناء قائمة العناوين عن `sys.argv`
2. **التعامل مع الملفات المؤقتة** — بدلاً من كتابة ملف، تمرير القائمة مباشرة
3. **دعم التصنيفات (`-cat`)** — إضافة حقل اختياري في النموذج
