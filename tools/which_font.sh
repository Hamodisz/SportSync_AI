#!/usr/bin/env bash
set -e
# 1) DejaVu من النظام (دوكر)
if [ -f "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" ]; then
  echo "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
  exit 0
fi
# 2) نسخة مضمّنة بالريبو (اختياري تحطها لاحقاً)
for f in "vendor/fonts/DejaVuSans.ttf" "assets/fonts/DejaVuSans.ttf"; do
  [ -f "$f" ] && { echo "$f"; exit 0; }
done
# 3) بدون خط: خليه يكمل بدون drawtext
echo "FONT_NOT_FOUND"
exit 0
