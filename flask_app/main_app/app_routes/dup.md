# تحليل: dup (إصلاح التحويلات المزدوجة)

## PHP: `php/dup.php`

### المدخلات (Parameters)

| المتغير | المصدر              | النوع         | الوصف                                        |
| ------- | ------------------- | ------------- | -------------------------------------------- |
| `start` | `$_POST`            | submit button | زر بدء العملية (name="start", value="start") |
| `test`  | `$_GET` أو `$_POST` | hidden        | وضع الاختبار (value="1")                     |

### سير العمل

1. يعرض نموذج HTML مع زر "start" فقط
2. إذا كان المستخدم غير مسجل الدخول → رابط تسجيل الدخول بدلاً من الزر
3. عند الضغط على start (POST) والمستخدم مسجل:
    - ينفذ أمر shell: `toolforge jobs run fixduplict --image python3.9 --command "python3 fix_duplicate.py save"`
    - إذا كان test=1: يعرض الأمر فقط دون تنفيذ فعلي (أظهر الكود على الصفحة)

## Python: `python/fix_duplicate.py`

### آلية العمل

1. يستعلم API ميدياويكي لجلب قائمة `DoubleRedirects` (التحويلات المزدوجة)
2. لكل تحويلة مزدوجة:
    - يتحقق من وجود الصفحة
    - يقارن النص الحالي بالنص الجديد
    - يحفظ الصفحة مع ملخص "fix duplicate redirect to [[target]]"
3. وسائط سطر الأوامر:
    - `save` — حفظ فعلي
    - بدون `save` — وضع تجريبي
    - `-offset:N` — البدء من رقم معين

### المعادلات

| PHP                    | Python CLI                   |
| ---------------------- | ---------------------------- |
| `$_POST['start']` (زر) | يشغل `fix_duplicate.py save` |
| `test=1`               | لا يمرر — فقط يظهر الأمر     |

---

## رؤية النقل إلى Flask

### ملف route الحالي: `flask_app/main_app/app_routes/dup.py`

```
GET  /dup/  → عرض النموذج
POST /dup/  → استقبال start + test
```

### ما يحتاج تكملة

1. **استدعاء `fix_duplicate.py` مباشرة** بدلاً من `shell_exec`
    - استيراد دالة `main()` أو `fix_dup()` من `fix_duplicate.py`
    - تمرير المعطيات مباشرة دون الحاجة لـ CLI args
2. **التحقق من تسجيل الدخول** (Flask-Login / session)
    - حالياً: `request.values.get("global_username")` كبديل مؤقت
3. **عرض النتائج بشكل حي** (WebSocket أو polling للحالة)
