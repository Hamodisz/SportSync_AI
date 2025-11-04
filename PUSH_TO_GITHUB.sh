#!/bin/bash
# 🚀 سكريبت رفع المشروع النظيف إلى GitHub

echo "======================================"
echo "🧹 SportSync AI - Clean Project Push"
echo "======================================"
echo ""

# الانتقال لمجلد المشروع
cd "$(dirname "$0")"

echo "📍 المسار الحالي: $(pwd)"
echo ""

# ====================================
# 1️⃣ إضافة جميع التغييرات
# ====================================
echo "1️⃣  إضافة جميع التغييرات..."
git add .
echo "✅ تمت إضافة الملفات"
echo ""

# ====================================
# 2️⃣ عرض الملفات التي سيتم رفعها
# ====================================
echo "2️⃣  الملفات المعدلة/المحذوفة:"
echo "--------------------------------"
git status --short
echo ""

# ====================================
# 3️⃣ إنشاء Commit
# ====================================
echo "3️⃣  إنشاء commit..."
COMMIT_MSG="🧹 chore: Clean project structure

- Remove duplicate files and folders (claude-code-into/, backend_gpt.py.backup)
- Delete temporary files (temp videos, old logs)
- Remove unused external archives (orchive/)
- Update .gitignore with better rules
- Keep only essential files for production

This commit creates a clean, organized project structure ready for deployment.
"

git commit -m "$COMMIT_MSG"
echo "✅ تم إنشاء الـ commit"
echo ""

# ====================================
# 4️⃣ رفع على GitHub
# ====================================
echo "4️⃣  الرفع على GitHub..."
echo ""
echo "⚠️  تأكد من إعداد Remote Repository أولاً!"
echo ""
echo "📝 إذا لم يكن لديك repository على GitHub بعد، استخدم:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/SportSync_AI.git"
echo ""

read -p "هل تريد المتابعة مع الرفع؟ (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # التحقق من وجود remote
    if git remote | grep -q "origin"; then
        echo "🔄 جاري الرفع..."
        
        # الحصول على اسم الفرع الحالي
        CURRENT_BRANCH=$(git branch --show-current)
        
        # رفع التغييرات
        git push -u origin "$CURRENT_BRANCH"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "================================"
            echo "✅ نجح الرفع إلى GitHub!"
            echo "================================"
            echo ""
            echo "🌐 Repository URL:"
            git remote get-url origin
            echo ""
            echo "🎉 المشروع الآن على GitHub بنية نظيفة!"
        else
            echo ""
            echo "❌ فشل الرفع! تحقق من:"
            echo "   1. صلاحيات GitHub (SSH/HTTPS)"
            echo "   2. اتصال الإنترنت"
            echo "   3. اسم الـ remote صحيح"
        fi
    else
        echo ""
        echo "❌ لم يتم العثور على remote 'origin'"
        echo ""
        echo "📝 لإضافة remote جديد:"
        echo "   git remote add origin https://github.com/YOUR_USERNAME/SportSync_AI.git"
        echo ""
        echo "ثم شغّل السكريبت مرة أخرى"
    fi
else
    echo ""
    echo "⏸️  تم الإلغاء. يمكنك الرفع يدوياً لاحقاً باستخدام:"
    echo "   git push -u origin main"
fi

echo ""
echo "======================================"
echo "🏁 انتهى السكريبت"
echo "======================================"
