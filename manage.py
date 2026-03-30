#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "as_project.settings")
    try:
        from django.core.management import execute_from_command_line
        
        # 기본 실행 포트를 8001로 고정하여 비디오 매니저(8000번 포트)와 겹치는 문제 원천 차단
        from django.core.management.commands.runserver import Command as runserver
        runserver.default_port = "8001"
        
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
