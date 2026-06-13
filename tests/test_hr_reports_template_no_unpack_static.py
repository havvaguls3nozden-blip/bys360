from pathlib import Path


def test_hr_reports_template_no_two_value_unpack_for_dict_stats():
    text = Path('app/templates/hr_reports.html').read_text(encoding='utf-8')
    assert '{% for unit_name, count in unit_stats %}' not in text
    assert '{% for item, count in leave_type_stats %}' not in text
    assert '{% for item, count in attendance_type_stats %}' not in text
    assert '{% for row in unit_stats %}' in text
    assert '{% for row in leave_type_stats %}' in text
    assert '{% for row in attendance_type_stats %}' in text
