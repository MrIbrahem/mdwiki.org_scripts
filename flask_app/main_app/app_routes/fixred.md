# تحليل: fixred (إصلاح التحويلات في النصوص)

## PHP: `php/fixred.php`

### المدخلات (Parameters)

| المتغير | المصدر | النوع | الوصف |
|----------|--------|------|-------------|
| `title` | `$_GET` | text (required) | عنوان الصفحة المراد إصلاح تحويلاتها |
| `test` | `$_GET` | hidden | وضع الاختبار (value="1") |

### سير العمل

1. يعرض نموذج GET بحقل `title` مطلوب
2. المستخدم يدخل عنوان صفحة (أو "all" لكل الصفحات)
3. عند الإرسال والمستخدم مسجل:
   - يعالج العنوان: يستبدل `+` ومسافات بـ `_`، ثم `rawurlencode`
   - يبني الأمر: `fixred.py -page2:title save`
   - ينفذ عبر `do_tfj_sh()` (تنفيذ أوامر Toolforge)
4. يعرض النتيجة

### دالة `get_results($title)`

- تستدعي `do_tfj_sh()` مع params:
  ```
  dir="c9", localdir="c9", pyfile="pwb.py", other="fixred.py -page2:title save", test=test
  ```

## Python: `python/fixred.py`

### آلية العمل

1. يقرأ وسائط CLI:
   - `-page2:title` (مشفرة URL) — عنوان واحد
   - `-page:title` — عنوان واحد
2. إذا كانت القائمة فارغة أو "all" → يجلب كل الصفحات غير التحويلية
3. لكل صفحة:
   - يجلب روابط الصفحة (`Get_page_links`)
   - يبحث عن التحويلات لكل رابط (`find_redirects`)
   - يستبدل الروابط القديمة بالروابط الصحيحة (`replace_links2`)
   - يحفظ الصفحة مع ملخص "Fix redirects"

### المعادلات

| PHP | Python CLI |
|-----|-----------|
| `$_GET['title']` | `-page2:urlencoded_title` |
| `test=1` | `test` في `sys.argv` |

---

## رؤية النقل إلى Flask

### ملف route الحالي: `flask_app/main_app/app_routes/fixred.py`

```
GET /fixred/?title=X&test=1  → معالجة وعرض نتيجة
GET /fixred/                 → عرض النموذج فارغاً
```

### ما يحتاج تكملة

1. **استدعاء `fixred.py` مباشرة**
   - استيراد `treat_page()` من `fixred.py`
   - تمرير `title` مباشرة بدلاً من CLI args
2. **التعامل مع "all"** — جلب كل الصفحات غير التحويلية
3. **إعادة هيكلة `replace_links2`** لتعمل بشكل مستقل عن `sys.argv`
