#!/bin/bash

echo "🚀 بدء تثبيت المتطلبات..."

# تحديث pip
python3 -m pip install --upgrade pip

# تثبيت المتطلبات من requirements.txt
pip install --prefer-binary -r requirements.txt

# التأكد من تثبيت ffmpeg (فقط في بيئات Linux)
if command -v apt-get &> /dev/null
then
    echo "🔧 تثبيت ffmpeg..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
else
    echo "⚠ لم يتم تثبيت ffmpeg تلقائيًا، تأكد من وجوده يدويًا في بيئتك"
fi

echo "✅ تم الانتهاء من إعداد البيئة بنجاح!"
