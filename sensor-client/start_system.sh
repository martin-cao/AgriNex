#!/bin/bash
# AgriNex 传感器客户端系统启动脚本

echo "🚀 启动AgriNex传感器客户端系统..."

# 切换到项目目录
cd "$(dirname "$0")"

# 检查MQTT服务器状态
echo "📡 检查MQTT服务器状态..."
if ! lsof -i :1883 > /dev/null 2>&1; then
    echo "❌ MQTT服务器未运行，请先启动mosquitto服务"
    echo "   启动命令: /opt/homebrew/sbin/mosquitto -c mosquitto.conf -v"
    exit 1
fi

echo "✅ MQTT服务器正在运行"

# 创建日志目录
mkdir -p logs

# 启动传感器客户端
echo "🔌 启动传感器客户端..."
python sensor_launcher.py --client-id "agrinex_sensor_$(date +%H%M%S)" > logs/sensor_client.log 2>&1 &
SENSOR_PID=$!

# 等待客户端启动
sleep 3

# 启动监控器
echo "📊 启动监控器..."
python monitor.py > logs/monitor.log 2>&1 &
MONITOR_PID=$!

echo "✅ 系统启动完成"
echo "   传感器客户端 PID: $SENSOR_PID"
echo "   监控器 PID: $MONITOR_PID"
echo ""
echo "📋 管理命令:"
echo "   查看传感器日志: tail -f logs/sensor_client.log"
echo "   查看监控器日志: tail -f logs/monitor.log"
echo "   停止系统: kill $SENSOR_PID $MONITOR_PID"
echo ""
echo "按 Ctrl+C 停止系统..."

# 等待中断信号
trap 'echo "🛑 停止系统..."; kill $SENSOR_PID $MONITOR_PID; exit 0' INT TERM

# 保持脚本运行
while true; do
    sleep 1
done
