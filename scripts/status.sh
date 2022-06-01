while sleep 5; do
    TS=$(date "+%Y-%m-%d-%H-%M")
    TEMP=$(sfx-status | grep "Temperature")
    WARNING=$(sfx-status | grep "Warning")
    MEM=$(free -h)
    echo "${TS}:"
    echo "${TEMP}"
    echo "${MEM}"
    echo "${WARNING}"
done