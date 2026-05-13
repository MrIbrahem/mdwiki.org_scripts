# تحليل: replace (بحث واستبدال)

## PHP: `php/replace/index.php`

### المدخلات (Parameters)

| المتغير | المصدر | النوع | الوصف |
|----------|--------|------|-------------|
| `listtype` | `$_GET` أو `$_POST` | radio | `newlist` (API search) أو `oldlist` (كل الصفحات) |
| `test` | `$_GET` أو `$_POST` | radio | وضع الاختبار (value="1") |
| `find` | `$_GET` أو `$_POST` | textarea (required) | النص المراد البحث عنه |
| `replace` | `$_GET` أو `$_POST` | textarea (required) | النص البديل |
| `number` | `$_GET` أو `$_POST` | number | الحد الأقصى لعدد الاستبدالات |

### الصلاحيات

- المستخدمون المصرح لهم فقط: `Doc James`, `Mr. Ibrahem`
- غير المصرح لهم يرون رسالة "Access denied"

### سير العمل — آلية الملفات

1. يعرض نموذج POST يحتوي على:
   - `find` (textarea) — النص المطلوب
   - `replace` (textarea) — النص البديل
   - `number` — حد أقصى للاستبدالات
   - `listtype` — `newlist` أو `oldlist`
2. عند الإرسال والمستخدم مصرح:
   - يولد `$nn` (رقم عشوائي)
   - **يكتب إلى ملفات:**
     - `replace/find/{nn}/find.txt` ← `$find`
     - `replace/find/{nn}/replace.txt` ← `$replace`
     - `replace/find/{nn}/info.json` ← `{find, replace, number, listtype, nn}`
   - يعرض رابط: `replace-log.php?id={nn}`

### ⚠️ ملاحظة هامة

هذا هو الملف الوحيد الذي **يكتب المعطيات إلى ملفات** بدلاً من تمريرها مباشرة إلى البوت. البوت (`find_replace_bot`) يعمل بشكل منفصل ويقرأ من هذه الملفات.

## Python: `python/find_replace_bot/`

### هيكل الملفات

| الملف | الدور |
|-------|-------|
| `bot.py` | يجلب قائمة jobs من المجلدات، يشغل `do_one_job` لكل منها |
| `one_job.py` | ينفذ عملية البحث والاستبدال لمهمة واحدة |

### آلية العمل

1. `bot.py::get_jobs()`:
   - يقرأ المجلدات الفرعية في `replace/find/`
   - يتجاهل المجلدات التي تحتوي على `done.txt`
2. `bot.py::main()`:
   - لكل job: يستدعي `one_job.do_one_job(nn)`
3. `one_job.py::do_one_job(nn)`:
   - يقرأ `info.json`, `find.txt`, `replace.txt` من `replace/find/{nn}/`
   - يحدد العناوين: API search (إذا `newlist`) أو كل الصفحات
   - لكل صفحة: يستبدل النص ويحفظ
   - يكتب `log.txt` و `text.txt` و `done.txt`

### المعادلات

| PHP Form | مكان التخزين | المستهلك |
|----------|-------------|----------|
| `find` | `find/{nn}/find.txt` | `one_job.get_find_and_replace()` |
| `replace` | `find/{nn}/replace.txt` | `one_job.get_find_and_replace()` |
| `number` | `find/{nn}/info.json` | `one_job.do_one_job()` → `max_numbers` |
| `listtype` | `find/{nn}/info.json` | `one_job.get_titles()` |

---

## رؤية النقل إلى Flask

### ملف route الحالي: `flask_app/main_app/app_routes/replace.py`

```
GET  /replace/  → عرض النموذج
POST /replace/  → استقبال ومعالجة
```

### ما يحتاج تكملة — إعادة هيكلة كاملة

1. **تمرير المعطيات مباشرة** بدلاً من نظام الملفات
   - استيراد `do_one_job` أو تفكيكها لاستقبال المعطيات مباشرة:
     ```python
     def do_replace(find, replace, number, listtype):
         # بدلاً من قراءة الملفات
     ```
   - إزالة الاعتماد على `work_dir` والمجلدات المؤقتة

2. **نظام تتبع المهام**
   - استبدال `{nn}` العشوائي بمعرف مهمة (task ID)
   - تخزين الحالة في قاعدة بيانات بدلاً من `done.txt`, `log.txt`

3. **التنفيذ المتزامن وغير المتزامن**
   - المهام الكبيرة (oldlist = كل الصفحات) تحتاج معالجة خلفية (background worker)
   - المهام الصغيرة (newlist مع نتائج قليلة) يمكن تنفيذها مباشرة

4. **نظام الإيقاف**
   - استبدال `stop.txt` بآلية إيقاف عبر API

5. **الصلاحيات**
   - دمج مع نظام مصادقة Flask
