#!/bin/bash
# scripts/start_simulator_device.sh
# AgriNex 模拟设备容器管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_DEVICE_TYPE="soil_sensor"
DEFAULT_MQTT_HOST="mosquitto"
DEFAULT_DATA_INTERVAL=30
DEFAULT_PORT_START=30001

# 帮助信息
show_help() {
    cat << EOF
AgriNex 模拟设备容器管理脚本

用法: $0 [命令] [选项]

命令 (不提供命令时默认为创建新设备):
    list, ls            列出所有模拟设备
    stop <device-id>    停止指定设备
    start <device-id>   启动指定设备
    remove <device-id>  删除指定设备容器
    logs <device-id>    查看设备日志
    health <device-id>  检查设备健康状态
    stop-all           停止所有模拟设备
    clean              清理所有停止的设备容器
    status             显示设备和端口使用情况

创建新设备选项:
    -i, --device-id     设备ID (必需，如: SIM_001)
    -t, --type          设备类型 (默认: soil_sensor)
                        可选: soil_sensor, weather_station, irrigation_controller
    -p, --port          HTTP端口号 (默认: 自动分配从30001开始)
    -m, --mqtt-host     MQTT主机地址 (默认: mosquitto)
    -n, --interval      数据发送间隔秒数 (默认: 30)
    -h, --help          显示此帮助信息

创建设备示例:
    $0 --device-id SIM_001 --type soil_sensor
    $0 -i SIM_002 -t weather_station -p 30002
    $0 -i SIM_003 -t irrigation_controller -n 15

管理设备示例:
    $0 list                    # 列出所有设备
    $0 stop SIM_001           # 停止设备SIM_001
    $0 logs SIM_001           # 查看设备日志
    $0 health SIM_001         # 检查设备健康状态
    $0 stop-all               # 停止所有设备
    $0 clean                  # 清理停止的容器

注意:
    - 设备ID必须唯一
    - 端口号必须未被使用
    - 确保AgriNex主系统已启动
EOF
}

# 列出所有模拟设备
list_devices() {
    echo -e "${BLUE}正在查找AgriNex模拟设备...${NC}"
    echo ""
    
    devices=$(docker ps -a --filter "name=sensor-sim-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true)
    
    if [[ -z "$devices" || "$devices" == "NAMES"* ]]; then
        echo -e "${YELLOW}没有找到任何模拟设备容器${NC}"
        return 0
    fi
    
    echo -e "${GREEN}模拟设备列表:${NC}"
    echo "$devices"
    echo ""
    
    # 统计运行状态
    running=$(docker ps --filter "name=sensor-sim-" --format "{{.Names}}" | wc -l)
    total=$(docker ps -a --filter "name=sensor-sim-" --format "{{.Names}}" | wc -l)
    
    echo -e "${BLUE}状态统计: $running/$total 设备正在运行${NC}"
}

# 停止指定设备
stop_device() {
    local device_id="$1"
    if [[ -z "$device_id" ]]; then
        echo -e "${RED}错误: 请指定设备ID${NC}"
        echo "用法: $0 stop <device-id>"
        exit 1
    fi
    
    local container_name="sensor-sim-${device_id}"
    
    if ! docker ps -a --format "{{.Names}}" | grep -q "^$container_name$"; then
        echo -e "${RED}错误: 设备 $device_id 不存在${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}正在停止设备 $device_id...${NC}"
    docker stop "$container_name" >/dev/null 2>&1
    echo -e "${GREEN}✅ 设备 $device_id 已停止${NC}"
}

# 启动指定设备
start_existing_device() {
    local device_id="$1"
    if [[ -z "$device_id" ]]; then
        echo -e "${RED}错误: 请指定设备ID${NC}"
        echo "用法: $0 start <device-id>"
        exit 1
    fi
    
    local container_name="sensor-sim-${device_id}"
    
    if ! docker ps -a --format "{{.Names}}" | grep -q "^$container_name$"; then
        echo -e "${RED}错误: 设备 $device_id 不存在${NC}"
        echo "请使用以下命令创建新设备:"
        echo "  $0 --device-id $device_id --type soil_sensor"
        exit 1
    fi
    
    echo -e "${YELLOW}正在启动设备 $device_id...${NC}"
    docker start "$container_name" >/dev/null 2>&1
    echo -e "${GREEN}✅ 设备 $device_id 已启动${NC}"
}

# 删除指定设备
remove_device() {
    local device_id="$1"
    if [[ -z "$device_id" ]]; then
        echo -e "${RED}错误: 请指定设备ID${NC}"
        echo "用法: $0 remove <device-id>"
        exit 1
    fi
    
    local container_name="sensor-sim-${device_id}"
    
    if ! docker ps -a --format "{{.Names}}" | grep -q "^$container_name$"; then
        echo -e "${RED}错误: 设备 $device_id 不存在${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}正在删除设备 $device_id...${NC}"
    docker rm -f "$container_name" >/dev/null 2>&1
    echo -e "${GREEN}✅ 设备 $device_id 已删除${NC}"
}

# 查看设备日志
show_logs() {
    local device_id="$1"
    if [[ -z "$device_id" ]]; then
        echo -e "${RED}错误: 请指定设备ID${NC}"
        echo "用法: $0 logs <device-id>"
        exit 1
    fi
    
    local container_name="sensor-sim-${device_id}"
    
    if ! docker ps -a --format "{{.Names}}" | grep -q "^$container_name$"; then
        echo -e "${RED}错误: 设备 $device_id 不存在${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}设备 $device_id 的日志:${NC}"
    echo "----------------------------------------"
    docker logs --tail=50 -f "$container_name"
}

# 检查设备健康状态
check_health() {
    local device_id="$1"
    if [[ -z "$device_id" ]]; then
        echo -e "${RED}错误: 请指定设备ID${NC}"
        echo "用法: $0 health <device-id>"
        exit 1
    fi
    
    local container_name="sensor-sim-${device_id}"
    
    if ! docker ps --format "{{.Names}}" | grep -q "^$container_name$"; then
        echo -e "${RED}❌ 设备 $device_id 未运行${NC}"
        exit 1
    fi
    
    # 获取容器端口
    local port=$(docker port "$container_name" 8080 2>/dev/null | cut -d: -f2)
    
    if [[ -z "$port" ]]; then
        echo -e "${RED}❌ 无法获取设备端口${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}正在检查设备 $device_id 健康状态...${NC}"
    
    if curl -s -f "http://localhost:$port/health" >/dev/null; then
        echo -e "${GREEN}✅ 设备 $device_id 健康状态正常${NC}"
        echo -e "${BLUE}访问地址: http://localhost:$port${NC}"
    else
        echo -e "${RED}❌ 设备 $device_id 健康检查失败${NC}"
        exit 1
    fi
}

# 停止所有设备
stop_all_devices() {
    local devices=$(docker ps --filter "name=sensor-sim-" --format "{{.Names}}" 2>/dev/null || true)
    
    if [[ -z "$devices" ]]; then
        echo -e "${YELLOW}没有正在运行的模拟设备${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}正在停止所有模拟设备...${NC}"
    
    while IFS= read -r container_name; do
        if [[ -n "$container_name" ]]; then
            local device_id=${container_name#sensor-sim-}
            echo "  停止设备: $device_id"
            docker stop "$container_name" >/dev/null 2>&1
        fi
    done <<< "$devices"
    
    echo -e "${GREEN}✅ 所有模拟设备已停止${NC}"
}

# 清理停止的容器
clean_containers() {
    local stopped_devices=$(docker ps -a --filter "name=sensor-sim-" --filter "status=exited" --format "{{.Names}}" 2>/dev/null || true)
    
    if [[ -z "$stopped_devices" ]]; then
        echo -e "${YELLOW}没有需要清理的停止设备${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}正在清理停止的设备容器...${NC}"
    
    while IFS= read -r container_name; do
        if [[ -n "$container_name" ]]; then
            local device_id=${container_name#sensor-sim-}
            echo "  删除设备: $device_id"
            docker rm "$container_name" >/dev/null 2>&1
        fi
    done <<< "$stopped_devices"
    
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 显示系统状态
show_status() {
    echo -e "${BLUE}=== AgriNex 模拟设备系统状态 ===${NC}"
    echo ""
    
    # 设备状态
    list_devices
    echo ""
    
    # 端口使用情况
    echo -e "${BLUE}端口使用情况 (30001-30020):${NC}"
    for port in {30001..30020}; do
        if netstat -ln 2>/dev/null | grep -q ":$port "; then
            # 查找使用此端口的容器
            container=$(docker ps --filter "publish=$port" --format "{{.Names}}" 2>/dev/null | head -1)
            if [[ -n "$container" ]]; then
                echo -e "  端口 $port: ${GREEN}已使用${NC} ($container)"
            else
                echo -e "  端口 $port: ${RED}已占用${NC} (非Docker)"
            fi
        fi
    done
    echo ""
    
    # 网络状态
    echo -e "${BLUE}Docker网络状态:${NC}"
    if docker network ls | grep -q "agrinex_agrinex-network"; then
        echo -e "  AgriNex网络: ${GREEN}可用${NC}"
    else
        echo -e "  AgriNex网络: ${RED}不可用${NC} (请启动主系统)"
    fi
}

# 创建新设备的函数
create_new_device() {
    # 解析命令行参数
    DEVICE_ID=""
    DEVICE_TYPE="$DEFAULT_DEVICE_TYPE"
    PORT=""
    MQTT_HOST="$DEFAULT_MQTT_HOST"
    DATA_INTERVAL="$DEFAULT_DATA_INTERVAL"

    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--device-id)
                DEVICE_ID="$2"
                shift 2
                ;;
            -t|--type)
                DEVICE_TYPE="$2"
                shift 2
                ;;
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -m|--mqtt-host)
                MQTT_HOST="$2"
                shift 2
                ;;
            -n|--interval)
                DATA_INTERVAL="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}未知选项: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done

    # 验证必需参数
    if [[ -z "$DEVICE_ID" ]]; then
        echo -e "${RED}错误: 设备ID是必需的${NC}"
        show_help
        exit 1
    fi

    # 验证设备类型
    case "$DEVICE_TYPE" in
        soil_sensor|weather_station|irrigation_controller)
            ;;
        *)
            echo -e "${RED}错误: 不支持的设备类型: $DEVICE_TYPE${NC}"
            echo "支持的类型: soil_sensor, weather_station, irrigation_controller"
            exit 1
            ;;
    esac

    # 自动分配端口
    if [[ -z "$PORT" ]]; then
        PORT="$DEFAULT_PORT_START"
        while netstat -ln | grep -q ":$PORT "; do
            ((PORT++))
        done
        echo -e "${BLUE}自动分配端口: $PORT${NC}"
    fi

    # 检查端口是否可用
    if netstat -ln | grep -q ":$PORT "; then
        echo -e "${RED}错误: 端口 $PORT 已被使用${NC}"
        exit 1
    fi

    # 检查容器名是否已存在
    CONTAINER_NAME="sensor-sim-${DEVICE_ID}"
    if docker ps -a --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        echo -e "${RED}错误: 容器名 $CONTAINER_NAME 已存在${NC}"
        echo "请使用不同的设备ID或先删除现有容器:"
        echo "  $0 remove $DEVICE_ID"
        exit 1
    fi

    # 检查AgriNex网络是否存在
    NETWORK_NAME="agrinex_agrinex-network"
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        echo -e "${YELLOW}警告: Docker网络 $NETWORK_NAME 不存在${NC}"
        echo "请确保AgriNex主系统已启动:"
        echo "  cd /path/to/AgriNex && docker-compose up -d"
        echo ""
        echo "是否继续使用默认网络? (y/N)"
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                NETWORK_NAME="bridge"
                ;;
            *)
                echo "操作已取消"
                exit 1
                ;;
        esac
    fi

    # 构建Docker运行命令
    echo -e "${BLUE}启动模拟设备容器...${NC}"
    echo "设备ID: $DEVICE_ID"
    echo "设备类型: $DEVICE_TYPE"
    echo "HTTP端口: $PORT"
    echo "MQTT主机: $MQTT_HOST"
    echo "数据间隔: ${DATA_INTERVAL}秒"
    echo "容器名: $CONTAINER_NAME"
    echo ""

    # 启动容器
    docker run -d \
        --name "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        -p "${PORT}:8080" \
        -e DEVICE_ID="$DEVICE_ID" \
        -e DEVICE_TYPE="$DEVICE_TYPE" \
        -e MQTT_HOST="$MQTT_HOST" \
        -e DATA_INTERVAL="$DATA_INTERVAL" \
        -e HTTP_PORT=8080 \
        --restart unless-stopped \
        agrinex-sensor-simulator:latest

    # 检查容器是否启动成功
    sleep 2
    if docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${GREEN}✅ 容器启动成功!${NC}"
        echo ""
        echo -e "${BLUE}设备信息:${NC}"
        echo "  设备ID: $DEVICE_ID"
        echo "  HTTP地址: localhost:$PORT"
        echo "  健康检查: curl http://localhost:$PORT/health"
        echo ""
        echo -e "${BLUE}接下来的步骤:${NC}"
        echo "1. 在AgriNex前端添加设备"
        echo "2. 设备ID: $DEVICE_ID"
        echo "3. 设备地址: localhost:$PORT"
        echo "4. 设备类型: $DEVICE_TYPE"
        echo ""
        echo -e "${BLUE}设备管理命令:${NC}"
        echo "  查看设备: $0 list"
        echo "  查看日志: $0 logs $DEVICE_ID"
        echo "  停止设备: $0 stop $DEVICE_ID"
        echo "  删除设备: $0 remove $DEVICE_ID"
    else
        echo -e "${RED}❌ 容器启动失败${NC}"
        echo "检查日志: docker logs $CONTAINER_NAME"
        exit 1
    fi
}

# 检查Docker是否可用
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${RED}错误: Docker未安装或不可用${NC}"
        exit 1
    fi
}

# 主程序
main() {
    # 检查Docker
    check_docker
    
    # 如果没有参数，显示帮助
    if [[ $# -eq 0 ]]; then
        show_help
        exit 1
    fi
    
    # 检查第一个参数是否为管理命令
    case "${1:-}" in
        list|ls)
            list_devices
            exit 0
            ;;
        stop)
            stop_device "$2"
            exit 0
            ;;
        start)
            start_existing_device "$2"
            exit 0
            ;;
        remove|rm)
            remove_device "$2"
            exit 0
            ;;
        logs)
            show_logs "$2"
            exit 0
            ;;
        health)
            check_health "$2"
            exit 0
            ;;
        stop-all)
            stop_all_devices
            exit 0
            ;;
        clean)
            clean_containers
            exit 0
            ;;
        status)
            show_status
            exit 0
            ;;
        -h|--help|help)
            show_help
            exit 0
            ;;
        -*)
            # 以 - 开头的参数，说明是创建新设备
            create_new_device "$@"
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知命令 '$1'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主程序
main "$@"
