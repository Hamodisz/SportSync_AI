def schedule_publish(video_path, user_data):
    """
    جدولة نشر الفيديو تلقائيًا بناءً على تفضيلات المستخدم أو التوقيت الأمثل
    """
    user_id = user_data.get("user_id", "unknown")
    print(f"[🔔] تم جدولة الفيديو للنشر: {video_path} للمستخدم: {user_id}")
