import os
from pathlib import Path


def generate_domain_test_placeholders(src_root, test_root):
    """ """
    src_path = Path(src_root)
    test_base_unit = Path(test_root) / "unit"
    test_base_integration = Path(test_root) / "integration"

    for root, _dirs, files in os.walk(src_path):
        current_path = Path(root)

        # if "domain" not in current_path.parts: continue

        # استخراج المسار النسبي من بعد مجلد المشروع (مثلاً: admin/domain/db)
        # نستخدم current_path.relative_to(src_path) للحصول على المسار داخل flask_app/x
        rel_path = current_path.relative_to(src_path)

        for file in files:
            target_dir = test_base_unit / rel_path
            if file.endswith(".py"):
                parent_name = current_path.stem

                file_stem = Path(file).stem
                if "routes" in current_path.parts or file_stem == "routes":
                    target_dir = test_base_integration / rel_path

                to_re = [
                    "worker",
                    "utils",
                    "objects",
                    "routes",
                ]
                if file_stem in to_re:
                    test_filename = f"test_{parent_name}_{file_stem}.py"

                else:
                    test_filename = f"test_{file_stem}.py"

                if file == "__init__.py":
                    file_path = current_path / file
                    file_content = file_path.read_text(encoding="utf-8")
                    if "def " not in file_content:
                        continue
                    else:
                        test_filename = f"test_{parent_name}_init.py"

                # إنشاء المجلد إذا لم يكن موجوداً
                target_dir.mkdir(parents=True, exist_ok=True)
                test_file_path = target_dir / test_filename

                # المسار الذي سيظهر في النص الوصفي (مثلاً domain/models/user.py)
                # نبحث عن موقع word "domain" وما بعدها
                parts = current_path.parts
                internal_path = "/".join(parts[parts.index("flask_app") :])

                _new = [
                    r'"""',
                    f'Unit tests for {internal_path}/{file} module.',
                    'TODO: write tests',
                    r'\n"""'
                ]
                content_new = "\n".join(_new)

                if not test_file_path.exists():
                    with open(test_file_path, "w", encoding="utf-8") as f:
                        f.write(content_new)


if __name__ == "__main__":
    main_path = Path(__file__).parent.parent

    SOURCE_DIR = main_path / "flask_app/main_app"
    TEST_DIR = main_path / "tests"

    print(f"SOURCE_DIR: {SOURCE_DIR}")
    print(f"TEST_DIR: {TEST_DIR}")

    generate_domain_test_placeholders(SOURCE_DIR, TEST_DIR)
