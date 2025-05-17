import os
import sys
import json
import subprocess
from pathlib import Path

# 默认编码 utf-8
sys.stdout.reconfigure(encoding="utf-8")

# 获取当前main.py所在路径并设置上级目录为工作目录
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
parent_dir = os.path.dirname(current_dir)
os.chdir(parent_dir)
print(f"设置工作目录为: {parent_dir}")

# 将当前目录添加到路径
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from utils import logger
except ImportError:
    # 如果logger不存在，创建一个简单的logger
    import logging

    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
    )
    logger = logging


def read_pip_config() -> dict:
    """
    读取 pip 配置文件并返回配置字典
    """
    config_dir = Path("./config")
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / "pip_config.json"
    default_config = {
        "enable_pip_update": True,
        "enable_pip_install": True,
        "last_version": "unknown",
        "mirror": "https://mirrors.ustc.edu.cn/pypi/simple",
        "backup_mirrors": [
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://mirrors.cloud.tencent.com/pypi/simple/",
            "https://pypi.org/simple",
        ],
    }

    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return default_config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("读取pip配置失败，使用默认配置")
        return default_config


def get_available_mirror(pip_config: dict) -> str:
    """
    检查镜像源可用性并返回一个可用的镜像源
    """
    mirrors = [pip_config.get("mirror")] + pip_config.get("backup_mirrors", [])
    for mirror in mirrors:
        try:
            logger.info(f"尝试连接镜像源: {mirror}")
            response = subprocess.run(
                [sys.executable, "-m", "pip", "list", "-i", mirror],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            if response.returncode == 0:
                logger.info(f"镜像源可用: {mirror}")
                return mirror
        except Exception:
            logger.warning(f"镜像源不可用: {mirror}")
    logger.error("所有镜像源都不可用")
    return None


def install_requirements(req_file="requirements.txt", pip_config=None) -> bool:
    """
    安装 requirements.txt 中的依赖
    """
    req_path = Path(req_file)
    if not req_path.exists():
        logger.error(f"requirements.txt 不存在")
        return False

    # 获取可用的镜像源
    mirror = get_available_mirror(pip_config)
    if not mirror:
        logger.error("没有可用的镜像源，安装依赖失败")
        return False

    try:
        logger.info("开始安装依赖...")
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            "-r",
            str(req_path),
            "--no-warn-script-location",
            "-i",
            mirror,
        ]

        subprocess.check_call(cmd)
        logger.info("依赖安装完成")
        return True
    except:
        logger.exception("pip 安装依赖时出错")
        return False


def update_pip(pip_config=None):
    """
    更新 pip 到最新版本
    """
    mirror = get_available_mirror(pip_config)
    if not mirror:
        logger.error("没有可用的镜像源，无法更新 pip")
        return False

    try:
        logger.info("正在更新 pip...")
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "--no-warn-script-location",
            "-i",
            mirror,
        ]

        subprocess.check_call(cmd)
        logger.info("pip 更新成功")
        return True
    except Exception:
        logger.exception("更新 pip 时出错")
        return False


def check_and_install_dependencies():
    """
    检查并安装依赖
    """
    pip_config = read_pip_config()
    enable_pip_update = pip_config.get("enable_pip_update", True)
    enable_pip_install = pip_config.get("enable_pip_install", True)

    if enable_pip_update:
        if not update_pip(pip_config=pip_config):
            logger.warning("pip 更新失败，继续尝试安装依赖...")

    current_version = read_interface_version()
    last_version = pip_config.get("last_version", "unknown")

    logger.info(f"启用 pip 安装依赖: {enable_pip_install}")
    logger.info(f"当前版本: {current_version}, 上次运行版本: {last_version}")

    if enable_pip_install and (
        current_version != last_version or current_version == "unknown"
    ):
        if install_requirements(pip_config=pip_config):
            update_pip_config(current_version)
            logger.info("依赖检查完成")
        else:
            logger.warning("依赖安装失败，程序可能无法正常运行")
    else:
        logger.info("跳过依赖安装")


def read_interface_version(interface_file="./interface.json") -> str:
    """
    读取 interface.json 文件中的版本信息
    """
    interface_path = Path(interface_file)

    if not interface_path.exists():
        logger.warning("interface.json不存在")
        return "unknown"

    try:
        with open(interface_path, "r", encoding="utf-8") as f:
            interface_data = json.load(f)
            return interface_data.get("version", "unknown")
    except Exception:
        logger.exception("读取interface.json版本失败")
        return "unknown"


def update_pip_config(version) -> bool:
    """
    更新 pip 配置文件中的版本信息
    """
    config_path = Path("./config/pip_config.json")
    try:
        config = read_pip_config()
        config["last_version"] = version

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception:
        logger.exception("更新pip配置失败")
        return False


def agent():
    try:
        from maa.agent.agent_server import AgentServer
        from maa.toolkit import Toolkit

        import custom
        from utils import logger

        Toolkit.init_option("./")

        socket_id = sys.argv[-1]

        AgentServer.start_up(socket_id)
        logger.info("AgentServer 启动")
        AgentServer.join()
        AgentServer.shut_down()
        logger.info("AgentServer 关闭")
    except Exception as e:
        logger.exception("agent 运行过程中发生异常")
        raise


def main():
    check_and_install_dependencies()
    agent()


if __name__ == "__main__":
    main()
