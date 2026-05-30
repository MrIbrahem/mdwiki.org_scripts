حلل `$_GET` `$_POST` في ملفات `php`

خيث أن لكل ملف `php` يوجد ملف بايثون يستقبل منه المعطيات هذه

-   `php/dup.php` > `python/fix_duplicate.py`
-   `php/fixred.php` > `python/fixred.py`
-   `php/fixref.php` > `python/fixref/start.py`
-   `php/replace/index.php` > `python/find_replace_bot/*.py`
-   `php/import-history.php` > `python/imp.py`
-   `php/redirect.php` > `python/red.py`
-   `php/newupdater.php` > `python/newupdater.py`

يوجد لدينا أيضًا قوالب `templates` تعكس حالة ملفات php قبل التعامل مع اي بيانات وهي بحاجة لتطوير وتحديث:

-   `flask_app/templates/dup.html`
-   `flask_app/templates/fixred.html`
-   `flask_app/templates/fixref.html`
-   `flask_app/templates/import-history.html`
-   `flask_app/templates/newupdater.html`
-   `flask_app/templates/redirect.html`
-   `flask_app/templates/replace.html`

الاختلاف فقط في `find_replace_bot` حيث يقوم بكتابة المعطيات الى ملفات ويحتاج لتعديل ليتلقى المعطيات مباشرة

لكل قالب templates يوجد ملف route python

مثال `flask_app/main_app/app_routes/dup.py` لـ `dup.html`

```python
from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

bp_dup = Blueprint("main", __name__, url_prefix="/dup")
logger = logging.getLogger(__name__)


@bp_dup.route("/", methods=["GET"])
def dup():
    return render_template("dup.html", )


__all__ = ["bp_dup"]

```

المطلوب كالتالي:

-   كل route بحاجة لتعديل لتقبل المعطيات المرسلة مثل ما تفعل ملفات php التي ذكرت اعلاه:

    -   التعامل مع $\_GET
    -   التعامل مع <form
    -   اضافة route مع methods=["POST"] اذا كانت ملفات PHP تتعامل مع POST ايضًا

-   لكل route كتابة ملف `.md` تحليلي لكود الphp و الـ python يتضمن تحليل لطريقة عملهما ورؤية لكيفية نقل العملية الى تطبيق فلاسك الجديد
