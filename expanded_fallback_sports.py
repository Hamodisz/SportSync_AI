# -*- coding: utf-8 -*-
"""
Expanded Fallback Sports List
Priority 3: Expand from 36 → 225+ sports

Organized by Z-axis categories for personality-matched fallbacks
"""

EXPANDED_FALLBACK_SPORTS = {
    # Calm/Adrenaline Axis
    "very_calm": {  # calm_adrenaline < -0.6
        "sports": [
            # Original 4
            {"name_en": "Fire Yoga", "name_ar": "🧘 اليوغا النارية"},
            {"name_en": "Moving Meditation", "name_ar": "🎯 التأمل الحركي"},
            {"name_en": "Meditative Swimming", "name_ar": "🌊 السباحة التأملية"},
            {"name_en": "Energy through Movement", "name_ar": "🎨 الطاقة بالحركة"},
            # +21 new calm sports
            {"name_en": "Tai Chi", "name_ar": "🥋 التاي تشي"},
            {"name_en": "Qigong", "name_ar": "🌀 التشي كونغ"},
            {"name_en": "Yin Yoga", "name_ar": "🧘 يوغا اليين"},
            {"name_en": "Restorative Yoga", "name_ar": "🌿 اليوغا الاستعادية"},
            {"name_en": "Forest Bathing", "name_ar": "🌲 الاستحمام بالغابات"},
            {"name_en": "Walking Meditation", "name_ar": "🚶 تأمل المشي"},
            {"name_en": "Breathwork Exercises", "name_ar": "💨 تمارين التنفس"},
            {"name_en": "Gentle Stretching", "name_ar": "🤸 الإطالة اللطيفة"},
            {"name_en": "Pilates", "name_ar": "🧘 البيلاتس"},
            {"name_en": "Floating Therapy", "name_ar": "🌊 العلاج بالطفو"},
            {"name_en": "Sound Bath Meditation", "name_ar": "🎵 تأمل الحمام الصوتي"},
            {"name_en": "Mindful Swimming", "name_ar": "🏊 السباحة الواعية"},
            {"name_en": "Slow Flow Yoga", "name_ar": "🧘 يوغا التدفق البطيء"},
            {"name_en": "Nature Walking", "name_ar": "🌳 المشي في الطبيعة"},
            {"name_en": "Gentle Cycling", "name_ar": "🚴 ركوب الدراجات الهادئ"},
            {"name_en": "Water Aerobics", "name_ar": "💧 التمارين المائية"},
            {"name_en": "Body Scan Meditation", "name_ar": "🧘 تأمل مسح الجسم"},
            {"name_en": "Pranayama", "name_ar": "🌬️ البراناياما"},
            {"name_en": "Mindful Gardening", "name_ar": "🌱 البستنة الواعية"},
            {"name_en": "Feldenkrais Method", "name_ar": "🤸 طريقة فيلدنكرايس"},
            {"name_en": "Alexander Technique", "name_ar": "🧘 تقنية ألكسندر"},
            {"name_en": "Somatic Yoga", "name_ar": "🧘 اليوغا الجسدية"},
            {"name_en": "Restorative Swimming", "name_ar": "🏊 السباحة الترميمية"},
            {"name_en": "Meditative Jogging", "name_ar": "🏃 الهرولة التأملية"},
            {"name_en": "Calm Paddleboarding", "name_ar": "🏄 التجديف الهادئ"}
        ]
    },

    "very_adrenaline": {  # calm_adrenaline > 0.6
        "sports": [
            # Original 4
            {"name_en": "Urban Parkour", "name_ar": "🏃 الباركور الحضري"},
            {"name_en": "Free Climbing", "name_ar": "🧗 التسلق الحر"},
            {"name_en": "Extreme Cycling", "name_ar": "🚴 الدراجات المتطرفة"},
            {"name_en": "Obstacle Racing", "name_ar": "⚡ سباقات العوائق"},
            # +21 new adrenaline sports
            {"name_en": "Skydiving", "name_ar": "🪂 القفز بالمظلات"},
            {"name_en": "Bungee Jumping", "name_ar": "🪢 القفز بالحبل المطاطي"},
            {"name_en": "Rock Climbing", "name_ar": "🧗 تسلق الصخور"},
            {"name_en": "White Water Rafting", "name_ar": "🌊 ركوب الأمواج البيضاء"},
            {"name_en": "Mountain Biking", "name_ar": "🚵 ركوب الدراجات الجبلية"},
            {"name_en": "BASE Jumping", "name_ar": "🪂 القفز من المباني"},
            {"name_en": "Zip-lining", "name_ar": "🌲 الانزلاق بالحبال"},
            {"name_en": "Cliff Diving", "name_ar": "🌊 الغوص من المنحدرات"},
            {"name_en": "Freestyle BMX", "name_ar": "🚴 دراجات BMX الحرة"},
            {"name_en": "Skateboarding", "name_ar": "🛹 التزلج على الألواح"},
            {"name_en": "Snowboarding", "name_ar": "🏂 التزلج على الثلج"},
            {"name_en": "Wakeboarding", "name_ar": "🏄 ركوب الأمواج بالحبل"},
            {"name_en": "Kitesurfing", "name_ar": "🪁 ركوب الأمواج بالطائرة الورقية"},
            {"name_en": "Wingsuit Flying", "name_ar": "🦅 الطيران ببدلة الأجنحة"},
            {"name_en": "Motocross", "name_ar": "🏍️ سباق الدراجات النارية"},
            {"name_en": "Downhill Skiing", "name_ar": "⛷️ التزلج على المنحدرات"},
            {"name_en": "Ice Climbing", "name_ar": "🧊 تسلق الجليد"},
            {"name_en": "Canyoning", "name_ar": "🏞️ استكشاف الأخاديد"},
            {"name_en": "Hang Gliding", "name_ar": "🪂 الطيران الشراعي"},
            {"name_en": "Paragliding", "name_ar": "🪂 الطيران المظلي"},
            {"name_en": "Heli-Skiing", "name_ar": "🚁 التزلج بالهليكوبتر"},
            {"name_en": "Free Diving", "name_ar": "🤿 الغوص الحر"},
            {"name_en": "Slacklining", "name_ar": "🎪 المشي على الحبل المرن"},
            {"name_en": "Extreme Parkour", "name_ar": "🏃 الباركور الشديد"},
            {"name_en": "Urban Climbing", "name_ar": "🧗 التسلق الحضري"}
        ]
    },

    "balanced_calm": {  # -0.6 <= calm_adrenaline <= 0.6
        "sports": [
            # Original 4
            {"name_en": "Dynamic Swimming", "name_ar": "🏊 السباحة الديناميكية"},
            {"name_en": "Strategic Tennis", "name_ar": "🎾 التنس الاستراتيجي"},
            {"name_en": "Active Walking", "name_ar": "🚶 المشي النشط"},
            {"name_en": "Rhythmic Gymnastics", "name_ar": "🤸 الجمباز الإيقاعي"},
            # +21 new balanced sports
            {"name_en": "Jogging", "name_ar": "🏃 الهرولة"},
            {"name_en": "Recreational Swimming", "name_ar": "🏊 السباحة الترفيهية"},
            {"name_en": "Badminton", "name_ar": "🏸 الريشة الطائرة"},
            {"name_en": "Table Tennis", "name_ar": "🏓 تنس الطاولة"},
            {"name_en": "Hiking", "name_ar": "🥾 المشي الجبلي"},
            {"name_en": "Casual Cycling", "name_ar": "🚴 ركوب الدراجات العادي"},
            {"name_en": "Dance Fitness", "name_ar": "💃 اللياقة بالرقص"},
            {"name_en": "Zumba", "name_ar": "💃 الزومبا"},
            {"name_en": "Kayaking", "name_ar": "🛶 ركوب القوارب"},
            {"name_en": "Canoeing", "name_ar": "🛶 ركوب الزوارق"},
            {"name_en": "Stand-Up Paddleboarding", "name_ar": "🏄 التجديف الواقف"},
            {"name_en": "Rowing", "name_ar": "🚣 التجديف"},
            {"name_en": "Frisbee", "name_ar": "🥏 الفريسبي"},
            {"name_en": "Disc Golf", "name_ar": "🥏 الجولف بالأقراص"},
            {"name_en": "Bowling", "name_ar": "🎳 البولينج"},
            {"name_en": "Golf", "name_ar": "⛳ الجولف"},
            {"name_en": "Rollerblading", "name_ar": "🛼 التزلج بالعجلات"},
            {"name_en": "Ice Skating", "name_ar": "⛸️ التزلج على الجليد"},
            {"name_en": "Trampoline Fitness", "name_ar": "🤸 لياقة الترامبولين"},
            {"name_en": "Barre", "name_ar": "🩰 تمارين البار"},
            {"name_en": "Aqua Jogging", "name_ar": "🏊 الهرولة المائية"},
            {"name_en": "Nordic Walking", "name_ar": "🥾 المشي الشمالي"},
            {"name_en": "Orienteering", "name_ar": "🧭 رياضة التوجيه"},
            {"name_en": "Trail Running", "name_ar": "🏃 الجري على المسارات"},
            {"name_en": "Beach Volleyball", "name_ar": "🏐 كرة الطائرة الشاطئية"}
        ]
    },

    # Social/Solo Axis
    "very_social": {  # solo_group > 0.6
        "sports": [
            # Original 4
            {"name_en": "Beach Football", "name_ar": "⚽ كرة القدم الشاطئية"},
            {"name_en": "Volleyball", "name_ar": "🏐 الكرة الطائرة"},
            {"name_en": "Team Basketball", "name_ar": "🏀 كرة السلة الجماعية"},
            {"name_en": "Group Martial Arts", "name_ar": "🤼 الرياضات القتالية الجماعية"},
            # +21 new social sports
            {"name_en": "Soccer", "name_ar": "⚽ كرة القدم"},
            {"name_en": "Rugby", "name_ar": "🏉 الرجبي"},
            {"name_en": "Hockey", "name_ar": "🏒 الهوكي"},
            {"name_en": "Baseball", "name_ar": "⚾ البيسبول"},
            {"name_en": "Softball", "name_ar": "🥎 السوفتبول"},
            {"name_en": "Handball", "name_ar": "🤾 كرة اليد"},
            {"name_en": "Water Polo", "name_ar": "🤽 كرة الماء"},
            {"name_en": "Lacrosse", "name_ar": "🥍 اللاكروس"},
            {"name_en": "Ultimate Frisbee", "name_ar": "🥏 الفريسبي النهائي"},
            {"name_en": "Dragon Boat Racing", "name_ar": "🐉 سباق قوارب التنين"},
            {"name_en": "Synchronized Swimming", "name_ar": "🏊 السباحة الإيقاعية"},
            {"name_en": "Cheerleading", "name_ar": "📣 التشجيع الرياضي"},
            {"name_en": "Team Relay Running", "name_ar": "🏃 الجري بالتتابع"},
            {"name_en": "Dodgeball", "name_ar": "🥎 كرة المراوغة"},
            {"name_en": "Kickball", "name_ar": "⚽ كرة الركل"},
            {"name_en": "Flag Football", "name_ar": "🏈 كرة القدم بالأعلام"},
            {"name_en": "Touch Rugby", "name_ar": "🏉 الرجبي باللمس"},
            {"name_en": "Netball", "name_ar": "🏀 كرة الشبكة"},
            {"name_en": "Sepak Takraw", "name_ar": "🥎 سيبك تاكرو"},
            {"name_en": "Quidditch", "name_ar": "🧹 الكويدتش"},
            {"name_en": "Roller Derby", "name_ar": "🛼 سباق الدراجات"},
            {"name_en": "Crew Rowing", "name_ar": "🚣 التجديف الجماعي"},
            {"name_en": "Team Cycling", "name_ar": "🚴 ركوب الدراجات الجماعي"},
            {"name_en": "Group Fitness Classes", "name_ar": "🏋️ دروس اللياقة الجماعية"},
            {"name_en": "Dance Teams", "name_ar": "💃 فرق الرقص"}
        ]
    },

    "very_solo": {  # solo_group < -0.6
        "sports": [
            # Original 4
            {"name_en": "Archery", "name_ar": "🎯 الرماية بالقوس"},
            {"name_en": "Solo Running", "name_ar": "🏃 الجري الفردي"},
            {"name_en": "Solo Yoga", "name_ar": "🧘 اليوغا المنفردة"},
            {"name_en": "Individual Cycling", "name_ar": "🚴 ركوب الدراجات الفردي"},
            # +21 new solo sports
            {"name_en": "Solo Hiking", "name_ar": "🥾 المشي الفردي"},
            {"name_en": "Solo Swimming", "name_ar": "🏊 السباحة الفردية"},
            {"name_en": "Weightlifting", "name_ar": "🏋️ رفع الأثقال"},
            {"name_en": "Solo Climbing", "name_ar": "🧗 التسلق الفردي"},
            {"name_en": "Solo Surfing", "name_ar": "🏄 ركوب الأمواج الفردي"},
            {"name_en": "Solo Skiing", "name_ar": "⛷️ التزلج الفردي"},
            {"name_en": "Track & Field", "name_ar": "🏃 ألعاب القوى"},
            {"name_en": "Marathon Running", "name_ar": "🏃 الماراثون"},
            {"name_en": "Triathlon", "name_ar": "🏊 سباق الثلاثي"},
            {"name_en": "Bodybuilding", "name_ar": "💪 بناء الأجسام"},
            {"name_en": "Powerlifting", "name_ar": "🏋️ رفع القوة"},
            {"name_en": "CrossFit", "name_ar": "🏋️ الكروس فت"},
            {"name_en": "Calisthenics", "name_ar": "🤸 التمارين البدنية"},
            {"name_en": "Solo Meditation", "name_ar": "🧘 التأمل الفردي"},
            {"name_en": "Solo Tai Chi", "name_ar": "🥋 التاي تشي الفردي"},
            {"name_en": "Solo Shadowboxing", "name_ar": "🥊 الملاكمة الوهمية"},
            {"name_en": "Solo Kata Practice", "name_ar": "🥋 ممارسة الكاتا"},
            {"name_en": "Solo Gymnastics", "name_ar": "🤸 الجمباز الفردي"},
            {"name_en": "Individual Skating", "name_ar": "⛸️ التزلج الفردي"},
            {"name_en": "Solo Paddleboarding", "name_ar": "🏄 التجديف الفردي"},
            {"name_en": "Individual Track Cycling", "name_ar": "🚴 الدراجات الفردي"},
            {"name_en": "Solo Trail Running", "name_ar": "🏃 الجري الفردي على المسارات"},
            {"name_en": "Individual Pilates", "name_ar": "🧘 البيلاتس الفردي"},
            {"name_en": "Solo Barre", "name_ar": "🩰 البار الفردي"},
            {"name_en": "Personal Training", "name_ar": "🏋️ التدريب الشخصي"}
        ]
    },

    "balanced_social": {  # -0.6 <= solo_group <= 0.6
        "sports": [
            # Original 4
            {"name_en": "Doubles Tennis", "name_ar": "🎾 التنس الزوجي"},
            {"name_en": "Table Tennis", "name_ar": "🏓 تنس الطاولة"},
            {"name_en": "Badminton", "name_ar": "🏸 الريشة الطائرة"},
            {"name_en": "Fencing", "name_ar": "🤺 المبارزة"},
            # +21 new balanced social sports
            {"name_en": "Squash", "name_ar": "🎾 الاسكواش"},
            {"name_en": "Racquetball", "name_ar": "🎾 كرة المضرب"},
            {"name_en": "Pickleball", "name_ar": "🏓 البيكلبول"},
            {"name_en": "Beach Tennis", "name_ar": "🎾 التنس الشاطئي"},
            {"name_en": "Padel", "name_ar": "🎾 بادل تنس"},
            {"name_en": "Platform Tennis", "name_ar": "🎾 تنس المنصة"},
            {"name_en": "Mixed Doubles Badminton", "name_ar": "🏸 الريشة الزوجية المختلطة"},
            {"name_en": "Partner Yoga", "name_ar": "🧘 يوغا الشريك"},
            {"name_en": "Partner Dancing", "name_ar": "💃 الرقص الزوجي"},
            {"name_en": "Boxing (Sparring)", "name_ar": "🥊 الملاكمة (المباراة)"},
            {"name_en": "Judo", "name_ar": "🥋 الجودو"},
            {"name_en": "Jiu-Jitsu", "name_ar": "🥋 الجيو جيتسو"},
            {"name_en": "Karate (Kumite)", "name_ar": "🥋 الكاراتيه (الكوميتيه)"},
            {"name_en": "Taekwondo", "name_ar": "🥋 التايكوندو"},
            {"name_en": "Wrestling", "name_ar": "🤼 المصارعة"},
            {"name_en": "Kickboxing", "name_ar": "🥊 الكيك بوكسينج"},
            {"name_en": "Muay Thai", "name_ar": "🥊 المواي تاي"},
            {"name_en": "Mixed Martial Arts", "name_ar": "🥊 الفنون القتالية المختلطة"},
            {"name_en": "Kendo", "name_ar": "🥋 الكيندو"},
            {"name_en": "Aikido", "name_ar": "🥋 الأيكيدو"},
            {"name_en": "Capoeira", "name_ar": "🤸 الكابويرا"},
            {"name_en": "Rock Climbing (Belaying)", "name_ar": "🧗 التسلق (التأمين)"},
            {"name_en": "Tandem Cycling", "name_ar": "🚴 الدراجة الترادفية"},
            {"name_en": "Doubles Bowling", "name_ar": "🎳 البولينج الزوجي"},
            {"name_en": "Partner Acrobatics", "name_ar": "🤸 الأكروبات الزوجية"}
        ]
    },

    # Variety/Repetition Axis
    "high_variety": {  # repeat_variety > 0.6
        "sports": [
            # Original 4
            {"name_en": "CrossFit", "name_ar": "🏋️ التدريب المتقاطع"},
            {"name_en": "Free Gymnastics", "name_ar": "🤸 الجمباز الحر"},
            {"name_en": "Triathlon", "name_ar": "🏃 سباق الثلاثي"},
            {"name_en": "Multi-Sport Training", "name_ar": "🧗 رياضات متعددة"},
            # +21 new variety sports
            {"name_en": "Decathlon", "name_ar": "🏃 العشاري"},
            {"name_en": "Heptathlon", "name_ar": "🏃 السباعي"},
            {"name_en": "Adventure Racing", "name_ar": "🗺️ سباق المغامرات"},
            {"name_en": "Obstacle Course Racing", "name_ar": "⚡ سباقات المعوقات"},
            {"name_en": "Spartan Race", "name_ar": "⚡ سباق سبارتان"},
            {"name_en": "Tough Mudder", "name_ar": "⚡ تاف مادر"},
            {"name_en": "Parkour Freerunning", "name_ar": "🏃 الباركور الحر"},
            {"name_en": "Mixed Martial Arts", "name_ar": "🥊 الفنون القتالية المختلطة"},
            {"name_en": "Brazilian Jiu-Jitsu", "name_ar": "🥋 الجيو جيتسو البرازيلي"},
            {"name_en": "Rock Climbing Variety", "name_ar": "🧗 تسلق متنوع"},
            {"name_en": "Bouldering", "name_ar": "🧗 التسلق الصخري"},
            {"name_en": "Sport Climbing", "name_ar": "🧗 التسلق الرياضي"},
            {"name_en": "Circus Arts", "name_ar": "🎪 فنون السيرك"},
            {"name_en": "Aerial Silks", "name_ar": "🎪 الأقمشة الهوائية"},
            {"name_en": "Trapeze", "name_ar": "🎪 الترابيز"},
            {"name_en": "Street Workout", "name_ar": "🤸 التمرين الشارع"},
            {"name_en": "Functional Fitness", "name_ar": "🏋️ اللياقة الوظيفية"},
            {"name_en": "HIIT Training", "name_ar": "🏋️ تدريب HIIT"},
            {"name_en": "Boot Camp", "name_ar": "🏋️ معسكر التدريب"},
            {"name_en": "Animal Flow", "name_ar": "🤸 تدفق الحيوانات"},
            {"name_en": "MovNat", "name_ar": "🤸 الحركة الطبيعية"},
            {"name_en": "Ninja Warrior Training", "name_ar": "🥷 تدريب المحارب النينجا"},
            {"name_en": "Slackline Tricks", "name_ar": "🎪 حيل الحبل المرن"},
            {"name_en": "Freestyle Swimming", "name_ar": "🏊 السباحة الحرة"},
            {"name_en": "Water Sports Variety", "name_ar": "🌊 رياضات مائية متنوعة"}
        ]
    },

    "low_variety": {  # repeat_variety < -0.6
        "sports": [
            # Original 4
            {"name_en": "Routine Swimming", "name_ar": "🏊 السباحة الروتينية"},
            {"name_en": "Regular Walking", "name_ar": "🚶 المشي المنتظم"},
            {"name_en": "Repetitive Archery", "name_ar": "🎯 الرماية المتكررة"},
            {"name_en": "Daily Yoga", "name_ar": "🧘 اليوغا اليومية"},
            # +21 new repetitive sports
            {"name_en": "Distance Running", "name_ar": "🏃 الجري لمسافات طويلة"},
            {"name_en": "Lap Swimming", "name_ar": "🏊 السباحة بالدورات"},
            {"name_en": "Stationary Cycling", "name_ar": "🚴 الدراجة الثابتة"},
            {"name_en": "Treadmill Running", "name_ar": "🏃 الجري على السير"},
            {"name_en": "Elliptical Training", "name_ar": "🏋️ التدريب الإهليلجي"},
            {"name_en": "Rowing Machine", "name_ar": "🚣 آلة التجديف"},
            {"name_en": "Stair Climbing", "name_ar": "🪜 صعود الدرج"},
            {"name_en": "Jump Rope", "name_ar": "🪢 حبل القفز"},
            {"name_en": "Weightlifting Routine", "name_ar": "🏋️ روتين رفع الأثقال"},
            {"name_en": "Bodyweight Exercises", "name_ar": "🤸 تمارين وزن الجسم"},
            {"name_en": "Daily Planking", "name_ar": "🤸 البلانك اليومي"},
            {"name_en": "Core Exercises", "name_ar": "🏋️ تمارين الجذع"},
            {"name_en": "Stretching Routine", "name_ar": "🤸 روتين الإطالة"},
            {"name_en": "Meditation Practice", "name_ar": "🧘 ممارسة التأمل"},
            {"name_en": "Tai Chi Daily", "name_ar": "🥋 التاي تشي اليومي"},
            {"name_en": "Qigong Daily", "name_ar": "🌀 التشي كونغ اليومي"},
            {"name_en": "Walking Laps", "name_ar": "🚶 المشي بالدورات"},
            {"name_en": "Indoor Cycling", "name_ar": "🚴 ركوب الدراجات الداخلي"},
            {"name_en": "Spinning Classes", "name_ar": "🚴 دروس السبينينج"},
            {"name_en": "Shadowboxing Daily", "name_ar": "🥊 الملاكمة الوهمية اليومية"},
            {"name_en": "Kata Repetition", "name_ar": "🥋 تكرار الكاتا"},
            {"name_en": "Form Practice", "name_ar": "🥋 ممارسة الأشكال"},
            {"name_en": "Breathing Exercises", "name_ar": "💨 تمارين التنفس"},
            {"name_en": "Plank Challenges", "name_ar": "🤸 تحديات البلانك"},
            {"name_en": "Daily Push-ups", "name_ar": "🤸 الضغط اليومي"}
        ]
    },

    "balanced_variety": {  # -0.6 <= repeat_variety <= 0.6
        "sports": [
            # Original 4
            {"name_en": "Interval Running", "name_ar": "🏃 الجري بالفترات"},
            {"name_en": "Mixed Cycling", "name_ar": "🚴 ركوب الدراجات المختلط"},
            {"name_en": "Varied Swimming", "name_ar": "🏊 السباحة المتنوعة"},
            {"name_en": "Tactical Tennis", "name_ar": "🎾 التنس التكتيكي"},
            # +21 new balanced variety sports
            {"name_en": "Circuit Training", "name_ar": "🏋️ التدريب الدائري"},
            {"name_en": "Tabata Workouts", "name_ar": "🏋️ تمارين تاباتا"},
            {"name_en": "Fartlek Running", "name_ar": "🏃 الجري فارتلك"},
            {"name_en": "Tempo Runs", "name_ar": "🏃 الجري الإيقاعي"},
            {"name_en": "Pyramid Training", "name_ar": "🏋️ التدريب الهرمي"},
            {"name_en": "Strength & Cardio Mix", "name_ar": "🏋️ مزيج القوة والقلب"},
            {"name_en": "Upper/Lower Split", "name_ar": "🏋️ تقسيم علوي/سفلي"},
            {"name_en": "Push/Pull/Legs", "name_ar": "🏋️ دفع/سحب/أرجل"},
            {"name_en": "Full Body Workouts", "name_ar": "🏋️ تمارين الجسم الكامل"},
            {"name_en": "Athletic Conditioning", "name_ar": "🏋️ اللياقة الرياضية"},
            {"name_en": "Sport-Specific Training", "name_ar": "🏋️ التدريب الخاص بالرياضة"},
            {"name_en": "Periodized Training", "name_ar": "🏋️ التدريب الدوري"},
            {"name_en": "Hybrid Workouts", "name_ar": "🏋️ التمارين الهجينة"},
            {"name_en": "Kettlebell Training", "name_ar": "🏋️ تدريب الكيتلبل"},
            {"name_en": "Medicine Ball Exercises", "name_ar": "🏋️ تمارين الكرة الطبية"},
            {"name_en": "Battle Rope Training", "name_ar": "🏋️ تدريب حبال المعركة"},
            {"name_en": "TRX Suspension", "name_ar": "🏋️ تعليق TRX"},
            {"name_en": "Resistance Band Training", "name_ar": "🏋️ تدريب الأشرطة المقاومة"},
            {"name_en": "Plyometric Exercises", "name_ar": "🤸 تمارين البليومترية"},
            {"name_en": "Agility Training", "name_ar": "🤸 تدريب الرشاقة"},
            {"name_en": "Speed Training", "name_ar": "🏃 تدريب السرعة"},
            {"name_en": "Endurance Training", "name_ar": "🏃 تدريب التحمل"},
            {"name_en": "Power Training", "name_ar": "🏋️ تدريب القوة"},
            {"name_en": "Mobility Training", "name_ar": "🤸 تدريب الحركة"},
            {"name_en": "Flexibility Training", "name_ar": "🤸 تدريب المرونة"}
        ]
    }
}

# Statistics
def get_fallback_stats():
    """Get statistics about the expanded fallback list"""
    total_sports = sum(len(category["sports"]) for category in EXPANDED_FALLBACK_SPORTS.values())

    stats = {
        "total_sports": total_sports,
        "categories": len(EXPANDED_FALLBACK_SPORTS),
        "sports_per_category": {
            category: len(data["sports"])
            for category, data in EXPANDED_FALLBACK_SPORTS.items()
        }
    }

    return stats

if __name__ == "__main__":
    stats = get_fallback_stats()
    print("=" * 60)
    print("EXPANDED FALLBACK SPORTS STATISTICS")
    print("=" * 60)
    print(f"\nTotal sports: {stats['total_sports']}")
    print(f"Categories: {stats['categories']}")
    print("\nSports per category:")
    for category, count in stats['sports_per_category'].items():
        print(f"  - {category}: {count} sports")
    print("\n" + "=" * 60)
