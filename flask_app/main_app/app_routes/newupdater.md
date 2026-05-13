# تحليل: newupdater (مُحدِّث المحتوى الطبي)

## PHP: `php/newupdater.php`

### المدخلات (Parameters)

| المتغير | المصدر | النوع | الوصف |
|----------|--------|------|-------------|
| `test` | `$_GET` | hidden | وضع الاختبار (value="1") |
| `title` | `$_GET` | text (required) | عنوان الصفحة |
| `save` | `$_GET` | checkbox | حفظ تلقائي (value="1") |

### سير العمل

1. يعرض نموذج GET مع:
   - حقل `title` (نص، مطلوب)
   - checkbox `save` (حفظ تلقائي)
2. عند الإرسال والمستخدم مسجل:
   - يعالج العنوان (يستبدل المسافات والـ +)
   - يستدعي `do_py_new()` لتشغيل `newupdater/med.py -page:title from_toolforge [save]`
   - يعالج النتيجة:
     - `"no changes"` → رسالة "no changes" + رابط التحرير
     - `"save ok"` → رسالة نجاح
     - `"notext"` → النص فارغ
     - `.txt` → يعرض نموذج تحرير محمّي مسبقاً بالنص الجديد
     - غير ذلك → يعرض النتيجة كما هي

### دالة `generateEditForm()`

- تنشئ نموذج POST إلى `mdwiki.org/w/index.php` (تحرير مباشر على الويكي)
- تعرض النص القديم والجديد للمقارنة

### دالة `do_py_new()`

- تنفذ أمر Python محلياً بدلاً من Toolforge:
  ```
  python3 path/to/newupdater/med.py -page:title from_toolforge [save]
  ```

## Python: `python/newupdater/med.py`

### آلية العمل

1. `work_on_title(title)`:
   - يجلب النص الحالي للصفحة
   - يستدعي `work_on_text(title, text)` من `new_updater` module
   - يقارن النص القديم بالجديد
   - يرجع: `"notext"`, `"no changes"`, أو النص الجديد
2. `work(title)`:
   - إذا كان `save` في `sys.argv` → يحفظ الصفحة مباشرة ويرجع `"save ok"`
   - وإلا → يخزن النص الجديد في ملف cash ويرجع اسم الملف
3. `save_cash(title, new_text)`:
   - يكتب النص الجديد لملف في مجلد `updatercash/`

### المعادلات

| PHP | Python CLI |
|-----|-----------|
| `$_GET['title']` | `-page:title` (مع استبدال `_` بمسافة) |
| `$_GET['save']` | `save` في `sys.argv` |
| `test=1` | يظهر الأمر فقط |

---

## رؤية النقل إلى Flask

### ملف route الحالي: `flask_app/main_app/app_routes/newupdater.py`

```
GET /newupdater/?title=X&save=1  → معالجة وعرض نتيجة
GET /newupdater/                 → عرض النموذج فارغاً
```

### ما يحتاج تكملة

1. **استدعاء `med.py` مباشرة**
   - استيراد `get_new_text()` و `work()` من `med.py`
   - تمرير `title` و `save` مباشرة
2. **عرض نموذج التحرير المسبق** — بدلاً من Form action إلى mdwiki.org
   - عرض مقارنة diff بين القديم والجديد
   - زر حفظ داخل التطبيق
3. **الاستغناء عن نظام cash بالملفات** — تخزين النتائج في الذاكرة أو قاعدة بيانات
4. **دعم المعاينة** — Preview قبل الحفظ
