__all__ = ["enable", "disable"]

import getpass
import pathlib
import subprocess
import sys
import tempfile

import appdirs

from ._cache import add_config, read_daemon_cache

service_template = """
[Unit]
Description=yaqd-{kind}

[Service]
Type=simple
User={user}
ExecStart={executable} --config={config_path}

[Install]
WantedBy=multi-user.target
"""

if sys.platform.startswith("win32"):
    try:
        nssm_exe = (
            subprocess.run(["where", "nssm.exe"], capture_output=True, check=True)
            .stdout.decode()
            .strip()
        )
    except Exception:
        nssm_exe = pathlib.Path(__file__).parent / "bin" / "nssm.exe"
    nssm_exe = str(nssm_exe)


def enable(kind):
    user = getpass.getuser()
    known_daemons = read_daemon_cache()
    try:
        daemon_data = next(d for d in known_daemons if d.kind == kind)
        config_path = daemon_data.config_filepath
    except:
        config_path = pathlib.Path(appdirs.user_config_dir("yaqd", "yaq")) / kind / "config.toml"
        add_config(config_path)
    if sys.platform.startswith("win32"):
        executable = (
            subprocess.run(["where", f"yaqd-{kind}"], capture_output=True, check=True)
            .stdout.decode()
            .strip()
        )
        subprocess.run([nssm_exe, "install", f"yaqd-{kind}", executable, f"--config={config_path}"], check=True)
    elif sys.platform.startswith("linux"):
        executable = (
            subprocess.run(["which", f"yaqd-{kind}"], capture_output=True, check=True)
            .stdout.decode()
            .strip()
        )
        with tempfile.NamedTemporaryFile() as tf:
            tf.write(
                service_template.format(
                    kind=kind, executable=executable, config_path=config_path, user=user
                ).encode()
            )
            tf.flush()
            subprocess.run(["sudo", "cp", tf.name, f"/etc/systemd/system/yaqd-{kind}.service"], check=True)
            subprocess.run(["sudo", "chmod", "+r", f"/etc/systemd/system/yaqd-{kind}.service"], check=True)

        subprocess.run(["systemctl", "enable", f"yaqd-{kind}"])

    else:
        raise NotImplementedError


def disable(kind):
    if sys.platform.startswith("win32"):
        subprocess.run([nssm_exe, "remove", f"yaqd-{kind}"])
    elif sys.platform.startswith("linux"):
        subprocess.run(["systemctl", "disable", f"yaqd-{kind}"])
    else:
        raise NotImplementedError