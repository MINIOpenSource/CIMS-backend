#!/bin/bash

# 定义仓库 URL 和目标目录
REPO_URL="https://github.com/MINIOpenSource/CIMS-backend.git"
DEST_DIR="/www/CIMS/backend"

# 获取操作系统信息以确定发行版
OS_RELEASE=$(cat /etc/os-release)
if [[ "$OS_RELEASE" =~ "ubuntu" ]]; then
    DISTRIBUTION="ubuntu"
    PACKAGE_MANAGER="apt-get"
elif [[ "$OS_RELEASE" =~ "centos" ]]; then
    DISTRIBUTION="centos"
    PACKAGE_MANAGER="yum"
elif [[ "$OS_RELEASE" =~ "fedora" ]]; then
    DISTRIBUTION="fedora"
    PACKAGE_MANAGER="dnf"
else
    echo "未检测到受支持的 Linux 发行版 (Ubuntu, CentOS, Fedora)。将尝试使用 apt-get (Debian 系) 作为默认包管理器。"
    DISTRIBUTION="unknown"
    PACKAGE_MANAGER="apt-get"
fi

# 检查是否安装 git
if ! command -v git &> /dev/null
then
    echo "Git 未安装。脚本需要 git 来克隆仓库。"
    echo "请确保 git 已安装后再运行此脚本。"
    exit 1
fi

# 询问用户是否需要自动安装 venv 和 pip
read -p "是否需要在 venv 或 pip 未找到时自动安装它们？ (y/n): " -n 1 -r
echo    # 换行
if [[ $REPLY =~ ^[Yy]$ ]]
then
    AUTO_INSTALL_DEPS="yes"
else
    AUTO_INSTALL_DEPS="no"
fi

# 函数：检查并安装包
check_and_install_package() {
    package_name="$1"
    check_command="$2"
    install_command="$3"

    if ! command -v "$check_command" &> /dev/null; then
        if [[ "$AUTO_INSTALL_DEPS" == "yes" ]]; then
            echo "${package_name} 未找到，尝试自动安装..."
            sudo $PACKAGE_MANAGER update  # 更新包列表
            if sudo $PACKAGE_MANAGER install -y "$install_command"; then
                echo "${package_name} 安装成功。"
            else
                echo "自动安装 ${package_name} 失败。请手动安装 ${package_name} 后重试。"
                exit 1
            fi
        else
            echo "${package_name} 未找到，且您选择不自动安装。脚本需要 ${package_name}。"
            echo "请手动安装 ${package_name} 后重试。"
            exit 1
        fi
    fi
}

# 检查并安装 venv (python3-venv 或 virtualenv)
if ! command -v python3 &> /dev/null; then
    echo "Python 3 未找到。请确保 Python 3 已安装。"
    exit 1
fi

check_and_install_package "venv (python3-venv)" "python3 -m venv" "python3-venv"
check_and_install_package "pip" "pip3" "python3-pip"


# 克隆仓库
echo "克隆仓库到 ${DEST_DIR}..."
mkdir -p "$(dirname "$DEST_DIR")" # 确保父目录存在
git clone "$REPO_URL" "$DEST_DIR"
if [ $? -ne 0 ]; then
    echo "克隆仓库失败，请检查网络连接或仓库地址。"
    exit 1
fi
cd "$DEST_DIR"

# 创建虚拟环境
echo "创建虚拟环境 venv..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "创建虚拟环境失败。"
    exit 1
fi

# 激活虚拟环境并安装依赖
echo "安装依赖..."
source /www/CIMS/backend/venv/bin/activate
pip3 install -r requirements.txt
python3 -m grpc_tools.protoc --proto_path=. --python_out=. --grpc_python_out=. ./Protobuf/Client/ClientCommandDeliverScReq.proto ./Protobuf/Client/ClientRegisterCsReq.proto ./Protobuf/Command/HeartBeat.proto ./Protobuf/Command/SendNotification.proto ./Protobuf/Enum/CommandTypes.proto ./Protobuf/Enum/Retcode.proto ./Protobuf/Server/ClientCommandDeliverScRsp.proto ./Protobuf/Server/ClientRegisterScRsp.proto ./Protobuf/Service/ClientCommandDeliver.proto ./Protobuf/Service/ClientRegister.proto
if [ $? -ne 0 ]; then
    echo "安装依赖失败。请检查 requirements.txt 文件或网络连接。"
    deactivate
    exit 1
fi

deactivate # 退出虚拟环境

echo "仓库克隆、虚拟环境创建和依赖安装完成。"
echo "项目已准备就绪，位于 ${DEST_DIR} 目录。"

exit 0