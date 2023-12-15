import os
from dataclasses import dataclass

import invoke

@dataclass
class Target:
    host: str
    app_id: str
    rh_home_dir: str = "/home/robothub"


LOCAL_APP_DIR = os.path.dirname(os.path.abspath(__file__))
NAME2TARGET = {
    # "ringo": Target(
    #     host="lux-ringo",
    #     app_id="83e6f9af-3d53-4793-980e-c32a8bd9ab28",
    # ),
    #"bob": Target(
    #    host="lux-bob",
    #    app_id="20d719ef-dcfc-4e87-94db-5d31c0acf636",
    #),
    #"qubit": Target(
    #    host="lux-qubit",
    #    app_id="a3e5e835-a63b-46aa-be37-246f13700090",
    #),
    # "matyas": Target(
    #     host="lux-matyas",
    #     app_id="71863b22-5c6d-47b1-8224-c3b93ebf37a8",
    # ),
    #"asample": Target(
    #    host="lux-asample",
    #    app_id="74fac601-0bf2-49ab-9c0f-f5cb184c4104",
    #    rh_home_dir="/data/disk/robothub",
    #),
    #"asample1": Target(
    #    host="root@192.168.24.180",
    #    app_id="0a35006c-791f-43b4-93ac-db91ebcac8d1",
    #    rh_home_dir="/data/disk/robothub",
    #),
    "asample2": Target(
        host="root@192.168.24.155",
        app_id="73b2c580-8f89-48c0-80e3-83333fb2f195"
    ),
    "asample3": Target(
        host="petr@192.168.0.113",
        app_id="77de7d87-69fe-4fc4-a51c-b6064c0f6c9d",
        rh_home_dir="/home/robothub",
    ),
}

RSYNC_EXCLUDE_LIST = [
    "frontend-src/",
    ".git/",
    ".vscode/",
    ".venv/",
    ".idea/"
    ".mypy_cache/",
    "*.pyi",
    ".gitignore",
    ".DS_Store",
    "containerfile",
    "docs/",
    "frontend-dev/",
    "old/",
    "scratches/",
    "tasks.py",
    "**__pycache__"
]
RSYNC_EXCLUDE_STR = " ".join(map(lambda x: f"--exclude {x}", RSYNC_EXCLUDE_LIST))


@invoke.task(iterable=["targets"])
def sync(
    context: invoke.context.Context,
    targets,
    code: bool = True,
    storage: bool = False,
    bags: bool = False,
) -> None:
    print("Running sync")
    if code:
        for name in ["asample3"]:
            target = NAME2TARGET[name]
            dst_dir = os.path.join(target.rh_home_dir, "data/sources", target.app_id)

            context.run(f"echo 'petr' | ssh {target.host} sudo -S chmod -R 770 {dst_dir}")
            context.run(
                f"rsync -a --no-perms --no-group --omit-dir-times --delete -P "
                f"{RSYNC_EXCLUDE_STR} "
                f"{LOCAL_APP_DIR}/ {target.host}:{dst_dir}"
            )
            context.run(f"echo 'petr' | ssh {target.host} sudo -S chown -R robothub:robothub {dst_dir}")
            context.run(f"echo 'petr' | ssh {target.host} sudo -S chmod -R 770 {dst_dir}")

    if storage:
        for name in targets:
            target = NAME2TARGET[name]
            src_dir = os.path.join(
                target.rh_home_dir, "data/container/", target.app_id, "data/"
            )
            dst_dir = os.path.join(LOCAL_APP_DIR, "out/", target.host, "storage/")
            os.makedirs(dst_dir, exist_ok=True)

            context.run(f"rsync -a --delete -P {target.host}:{src_dir} {dst_dir}")

    if bags:
        for name in targets:
            target = NAME2TARGET[name]
            src_dir = os.path.join(
                target.rh_home_dir, "data/container/", target.app_id, "public/bags/"
            )
            dst_dir = os.path.join(LOCAL_APP_DIR, "out/", target.host, "bags/")
            os.makedirs(dst_dir, exist_ok=True)

            context.run(f"rsync -a --delete -P {target.host}:{src_dir} {dst_dir}")


@invoke.task
def build_frontend(context: invoke.context.Context) -> None:
    with context.cd("frontend-dev"):
        context.run("npm install")
        context.run("npm run build")
    context.run("rm -rf frontend")
    context.run("cp -r frontend-dev/dist frontend")


@invoke.task
def build_image(
    context: invoke.context.Context,
    version: str,
    postfix: str,
    repo: str = "docker.io/panekj412/",
) -> None:
    tag = f"{repo}:{version}-{postfix}"
    with context.cd("containerfile"):
        context.run(f"docker build -f containerfile -t {tag} .")
        context.run(f"docker push {tag}")
