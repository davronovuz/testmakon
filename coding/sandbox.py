"""
TestMakon.uz — Docker Sandbox for Code Execution
Xavfsiz konteynerda kod ishlatish
"""

import docker
import tempfile
import os
import time
import logging

logger = logging.getLogger(__name__)

# Defaults — settings.py dan override qilinadi
DEFAULT_TIME_LIMIT = 5  # seconds
DEFAULT_MEMORY_LIMIT = '256m'
DEFAULT_CPU_PERIOD = 100000
DEFAULT_CPU_QUOTA = 50000  # 50% CPU
DEFAULT_PIDS_LIMIT = 64
MAX_OUTPUT_SIZE = 5000  # chars


class DockerSandbox:
    """Docker konteynerda xavfsiz kod ishlatish"""

    def __init__(self):
        self.client = docker.from_env()

    def execute(self, language, code, input_data='', time_limit=None, memory_limit=None):
        """
        Kodni Docker konteynerda ishlatadi.

        Returns:
            dict: {
                'stdout': str,
                'stderr': str,
                'exit_code': int,
                'execution_time': float (ms),
                'timed_out': bool,
                'error': str or None,
            }
        """
        from django.conf import settings as django_settings

        time_limit = time_limit or getattr(django_settings, 'SANDBOX_TIME_LIMIT', DEFAULT_TIME_LIMIT)
        mem_limit = memory_limit or getattr(django_settings, 'SANDBOX_MEMORY_LIMIT', DEFAULT_MEMORY_LIMIT)

        container = None
        tmpdir = None

        try:
            # Vaqtinchalik papka
            tmpdir = tempfile.mkdtemp(prefix='testmakon_')

            # Java uchun fayl nomi — public class nomi bilan mos bo'lishi SHART
            if language.slug == 'java':
                code_file = f"Solution{language.file_extension}"
            else:
                code_file = f"solution{language.file_extension}"

            # Kod faylini yozish
            code_path = os.path.join(tmpdir, code_file)
            with open(code_path, 'w') as f:
                f.write(code)

            # Input file
            input_path = os.path.join(tmpdir, 'input.txt')
            with open(input_path, 'w') as f:
                f.write(input_data)

            # Command — compile + run yoki faqat run
            if language.compile_cmd:
                compile_cmd = language.compile_cmd.replace('{file}', f'/sandbox/{code_file}')
                run_cmd = language.run_cmd.replace('{file}', f'/sandbox/{code_file}')
                cmd = f"sh -c '{compile_cmd} && {run_cmd} < /sandbox/input.txt'"
            else:
                run_cmd = language.run_cmd.replace('{file}', f'/sandbox/{code_file}')
                cmd = f"sh -c '{run_cmd} < /sandbox/input.txt'"

            # /tmp — kompilatsiya uchun yozish + ishga tushirish ruxsati (exec)
            # /sandbox — faqat o'qish (foydalanuvchi kodi)
            container = self.client.containers.run(
                image=language.docker_image,
                command=cmd,
                volumes={tmpdir: {'bind': '/sandbox', 'mode': 'ro'}},
                working_dir='/sandbox',
                network_mode='none',          # Tarmoq yo'q
                read_only=True,               # Faqat o'qish
                mem_limit=mem_limit,
                memswap_limit=mem_limit,       # Swap yo'q
                cpu_period=DEFAULT_CPU_PERIOD,
                cpu_quota=DEFAULT_CPU_QUOTA,
                pids_limit=DEFAULT_PIDS_LIMIT, # Fork bomb himoyasi
                security_opt=['no-new-privileges'],
                user='nobody',
                tmpfs={'/tmp': 'size=50M,exec'},  # Yozish + ishga tushirish (kompilatsiya uchun)
                detach=True,
                stdout=True,
                stderr=True,
            )

            # Kutish — timeout bilan
            start_time = time.time()
            try:
                result = container.wait(timeout=time_limit)
                execution_time = (time.time() - start_time) * 1000  # ms
                exit_code = result.get('StatusCode', -1)
                timed_out = False
            except Exception:
                # Timeout
                execution_time = time_limit * 1000
                exit_code = -1
                timed_out = True
                try:
                    container.kill()
                except Exception:
                    pass

            # Output olish
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')

            # Output limitlash
            stdout = stdout[:MAX_OUTPUT_SIZE]
            stderr = stderr[:MAX_OUTPUT_SIZE]

            return {
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exit_code,
                'execution_time': round(execution_time, 2),
                'timed_out': timed_out,
                'error': None,
            }

        except docker.errors.ImageNotFound:
            return {
                'stdout': '',
                'stderr': '',
                'exit_code': -1,
                'execution_time': 0,
                'timed_out': False,
                'error': f"Docker image topilmadi: {language.docker_image}",
            }
        except Exception as e:
            logger.exception(f"Sandbox xato: {e}")
            return {
                'stdout': '',
                'stderr': '',
                'exit_code': -1,
                'execution_time': 0,
                'timed_out': False,
                'error': str(e),
            }
        finally:
            # Cleanup
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            if tmpdir:
                try:
                    import shutil
                    shutil.rmtree(tmpdir, ignore_errors=True)
                except Exception:
                    pass

    def cleanup_old_containers(self, label='testmakon'):
        """Eski konteynerlarni tozalash"""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={'status': 'exited'}
            )
            removed = 0
            for c in containers:
                try:
                    if c.image.tags and any('python' in t or 'gcc' in t or 'node' in t or 'openjdk' in t for t in c.image.tags):
                        c.remove(force=True)
                        removed += 1
                except Exception:
                    pass
            return removed
        except Exception as e:
            logger.error(f"Cleanup xato: {e}")
            return 0
