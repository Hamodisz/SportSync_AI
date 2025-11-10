// ==========================================
// SportSync AI - Quiz Application
// ==========================================

// Questions Data (10 Questions)
const questions = [
    {
        id: 1,
        title: "كيف تفضل قضاء وقتك الحر؟",
        description: "هذا السؤال يساعدنا نفهم أسلوب حياتك ونوع النشاط الذي يناسب طاقتك الطبيعية. لا توجد إجابة خاطئة - فقط عبّر عن نفسك الحقيقية.",
        tip: "💡 نصيحة: اختر ما تفعله فعلاً، ليس ما 'تظن' أنه يجب عليك فعله",
        options: [
            "في الطبيعة - أستكشف أماكن جديدة وأتحرك",
            "في المنزل - أقرأ، أشاهد، أو أمارس هوايات هادئة",
            "مع الأصدقاء - نشاطات اجتماعية وتجمعات",
            "في التمرين - أذهب للصالة أو أمارس رياضة",
            "في العمل - أحب إنجاز مشاريع وتحديات"
        ],
        allowText: true,
        textPlaceholder: "أخبرنا بالتفصيل عن نشاطك المفضل... (اختياري)"
    },
    {
        id: 2,
        title: "ما الذي يحفزك أكثر؟",
        description: "دوافعك الداخلية تكشف الكثير عن نوع الرياضة التي ستستمر فيها. نحلل هنا طبقة عميقة من شخصيتك النفسية.",
        tip: "💡 فكّر: ما الذي يجعلك تستيقظ متحمساً في الصباح؟",
        options: [
            "المنافسة والفوز - أحب التحدي والتفوق",
            "التحسن الشخصي - أن أصبح نسخة أفضل من نفسي",
            "الاسترخاء والهدوء - التخلص من التوتر",
            "التواصل الاجتماعي - بناء علاقات وصداقات",
            "الإبداع والتعبير - إيجاد طرق جديدة للتعبير عن نفسي"
        ],
        allowText: true,
        textPlaceholder: "شاركنا قصة عن موقف حفزك بشدة..."
    },
    {
        id: 3,
        title: "كيف تتعامل مع الضغوط؟",
        description: "استجابتك للضغط تحدد نوع النشاط الرياضي الذي سيساعدك. بعض الرياضات تزيد الأدرينالين، وأخرى تهدّئ الأعصاب.",
        tip: "💡 تذكر: لا حكم هنا - كل طريقة لها رياضة تناسبها",
        options: [
            "بالحركة - أتحرك وأمارس نشاط بدني",
            "بالتأمل - أجلس وأفكر بهدوء",
            "بالعزلة - أحتاج وقت لوحدي",
            "بالتحدث - أشارك مشاعري مع الآخرين",
            "بالتخطيط - أحلل الموقف وأضع خطة"
        ],
        allowText: true,
        textPlaceholder: "صف لنا آخر موقف ضاغط وكيف تعاملت معه..."
    }    ,{
        id: 4,
        title: "ما هو مستوى طاقتك اليومي؟",
        description: "مستوى طاقتك الطبيعي يحدد كثافة ونوع الرياضة المثالية. لا تقارن نفسك بالآخرين - فقط صف حالتك الطبيعية.",
        tip: "💡 فكّر في يوم عادي، ليس يوم استثنائي",
        options: [
            "طاقة عالية جداً - دائماً متحمس ونشيط",
            "طاقة متوسطة - نشيط في أوقات محددة",
            "طاقة هادئة - أفضل النشاطات المعتدلة",
            "طاقة متقلبة - تختلف من يوم لآخر",
            "طاقة منخفضة - أفضل الراحة غالباً"
        ],
        allowText: true,
        textPlaceholder: "متى تشعر بأعلى طاقة في اليوم؟"
    },
    {
        id: 5,
        title: "ما هي علاقتك بجسدك؟",
        description: "فهمك لجسدك يساعدنا نختار رياضة تحترم حدودك وتطور نقاط قوتك. كل جسد فريد وله احتياجاته الخاصة.",
        tip: "💡 الصدق هنا مهم جداً لاختيار رياضة آمنة ومناسبة",
        options: [
            "رياضي - أتمرن بانتظام وأعرف حدودي",
            "مرن - لم أتمرن كثيراً لكن مستعد للبدء",
            "حذر - عندي قيود جسدية أو إصابات سابقة",
            "مبتدئ - لم أمارس الرياضة من فترة طويلة",
            "مستكشف - أريد تجربة شيء جديد تماماً"
        ],
        allowText: true,
        textPlaceholder: "هل هناك نشاطات جسدية تستمتع بها حالياً؟"
    },
    {
        id: 6,
        title: "كيف تفضل التعلم؟",
        description: "أسلوب تعلمك يحدد كيف ستتقدم في الرياضة. بعض الناس يحبون البنية الواضحة، وآخرون يفضلون الاكتشاف الحر.",
        tip: "💡 تذكر: لا يوجد أسلوب أفضل من الآخر",
        options: [
            "التعليمات المباشرة - أعطني خطوات واضحة",
            "التجربة والخطأ - أحب أكتشف بنفسي",
            "المشاهدة والتقليد - أتعلم بالملاحظة",
            "التحليل العميق - أحب أفهم المبادئ أولاً",
            "التعلم الاجتماعي - أتعلم أفضل مع مجموعة"
        ],
        allowText: true,
        textPlaceholder: "اذكر شيئاً تعلمته بسهولة وكيف..."
    },
    {
        id: 7,
        title: "ما نوع البيئة التي تفضلها؟",
        description: "المكان الذي تمارس فيه الرياضة لا يقل أهمية عن الرياضة نفسها. بعضنا يحتاج الطبيعة، وآخرون يفضلون البيئة المنظمة.",
        tip: "💡 تخيل نفسك تمارس نشاط - أين تكون؟",
        options: [
            "الطبيعة المفتوحة - جبال، شواطئ، غابات",
            "الصالة الرياضية - معدات ومرافق متخصصة",
            "المنزل - خصوصية وراحة",
            "الأماكن الحضرية - حدائق، شوارع، ملاعب",
            "لا يهم - المهم النشاط نفسه"
        ],
        allowText: true,
        textPlaceholder: "صف لنا مكانك المفضل..."
    }    ,{
        id: 8,
        title: "ما هو هدفك الأساسي من الرياضة؟",
        description: "هدفك يشكل نوع الرياضة والطريقة التي ستمارسها بها. الصدق هنا يساعدنا نخترع لك تجربة تحقق ما تريد فعلاً.",
        tip: "💡 فكّر: لماذا أريد البدء بنشاط رياضي الآن؟",
        options: [
            "الصحة الجسدية - لياقة، قوة، مرونة",
            "الصحة النفسية - تقليل التوتر، السعادة",
            "التواصل الاجتماعي - صداقات ومجتمع",
            "تحدي نفسي - تحقيق إنجاز أو هدف",
            "المتعة والاستمتاع - نشاط ممتع فقط"
        ],
        allowText: true,
        textPlaceholder: "ما الذي تأمل أن تشعر به بعد 3 أشهر؟"
    },
    {
        id: 9,
        title: "كم من الوقت يمكنك تخصيصه أسبوعياً؟",
        description: "الواقعية مهمة. نريد اختراع رياضة تناسب حياتك، ليس حياة تتمحور حول الرياضة (إلا إذا أردت ذلك!).",
        tip: "💡 كن واقعياً - الاستمرارية أهم من الكم",
        options: [
            "15-30 دقيقة يومياً - روتين قصير ومنتظم",
            "1-2 ساعة، 3 مرات أسبوعياً - التزام معتدل",
            "3-5 ساعات أسبوعياً - جدي في الموضوع",
            "أكثر من 5 ساعات - رياضة جزء كبير من حياتي",
            "وقت مرن - أفضل نشاط يتأقلم مع جدولي"
        ],
        allowText: true,
        textPlaceholder: "ما هي التزاماتك الحالية؟"
    },
    {
        id: 10,
        title: "ماذا تريد أن تشعر أثناء الرياضة؟",
        description: "هذا السؤال الأهم! الشعور المطلوب يحدد DNA رياضتك. نحن لا نبحث فقط عن نشاط - نبحث عن تجربة.",
        tip: "💡 أغمض عينيك وتخيل - ما الشعور الذي تبحث عنه؟",
        options: [
            "الحرية والانطلاق - أطير وأنا أتحرك",
            "القوة والتحكم - أشعر بجسدي يعمل",
            "الهدوء والسكينة - سلام داخلي",
            "الإثارة والأدرينالين - نبض قلبي يرتفع",
            "الانسجام والتدفق - ذوبان في اللحظة"
        ],
        allowText: true,
        textPlaceholder: "صف لنا أجمل شعور جسدي مررت به..."
    }
];

// ==========================================
// Application State
// ==========================================

let currentQuestion = 0;
let answers = {};

// Load saved progress
function loadProgress() {
    const saved = localStorage.getItem('sportsync_quiz_progress');
    if (saved) {
        const data = JSON.parse(saved);
        currentQuestion = data.currentQuestion || 0;
        answers = data.answers || {};
    }
}

// Save progress
function saveProgress() {
    localStorage.setItem('sportsync_quiz_progress', JSON.stringify({
        currentQuestion,
        answers,
        timestamp: new Date().toISOString()
    }));
}
// ==========================================
// Render Question
// ==========================================

function renderQuestion() {
    const question = questions[currentQuestion];
    const card = document.getElementById('questionCard');
    
    // Build options HTML
    let optionsHTML = '<div class="options-container">';
    question.options.forEach((option, index) => {
        const isSelected = answers[question.id]?.option === index;
        optionsHTML += `
            <button class="option-btn ${isSelected ? 'selected' : ''}" 
                    onclick="selectOption(${index})">
                ${option}
            </button>
        `;
    });
    optionsHTML += '</div>';
    
    // Build text input if allowed
    let textInputHTML = '';
    if (question.allowText) {
        const savedText = answers[question.id]?.text || '';
        textInputHTML = `
            <div class="text-input-container">
                <label class="text-label">📝 أضف ملاحظاتك الخاصة (اختياري ولكن يُفضّل):</label>
                <textarea class="text-input" 
                          id="textInput"
                          placeholder="${question.textPlaceholder}"
                          oninput="saveTextInput()">${savedText}</textarea>
            </div>
        `;
    }
    
    // Render complete question
    card.innerHTML = `
        <div class="question-number">السؤال ${question.id}</div>
        <h2 class="question-title">${question.title}</h2>
        <div class="question-description">${question.description}</div>
        <div class="question-tip">${question.tip}</div>
        ${optionsHTML}
        ${textInputHTML}
    `;
    
    // Update progress
    updateProgress();
    updateNavButtons();
}
// ==========================================
// User Interactions
// ==========================================

function selectOption(optionIndex) {
    const question = questions[currentQuestion];
    
    // Save answer
    if (!answers[question.id]) {
        answers[question.id] = {};
    }
    answers[question.id].option = optionIndex;
    answers[question.id].optionText = question.options[optionIndex];
    
    // Update UI
    document.querySelectorAll('.option-btn').forEach((btn, index) => {
        if (index === optionIndex) {
            btn.classList.add('selected');
        } else {
            btn.classList.remove('selected');
        }
    });
    
    saveProgress();
    updateNavButtons();
}

function saveTextInput() {
    const question = questions[currentQuestion];
    const textValue = document.getElementById('textInput')?.value || '';
    
    if (!answers[question.id]) {
        answers[question.id] = {};
    }
    answers[question.id].text = textValue;
    
    saveProgress();
}

// ==========================================
// Navigation
// ==========================================

function nextQuestion() {
    if (currentQuestion < questions.length - 1) {
        currentQuestion++;
        renderQuestion();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        submitQuiz();
    }
    saveProgress();
}

function previousQuestion() {
    if (currentQuestion > 0) {
        currentQuestion--;
        renderQuestion();
        window.scrollTo({ top: 0, behavior: 'smooth' });
        saveProgress();
    }
}

function updateNavButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const question = questions[currentQuestion];
    
    // Previous button
    prevBtn.disabled = currentQuestion === 0;
    
    // Next button text
    if (currentQuestion === questions.length - 1) {
        nextBtn.textContent = '✨ اكتشف رياضتك';
    } else {
        nextBtn.textContent = 'التالي →';
    }
    
    // Next button enabled only if option selected
    const hasAnswer = answers[question.id]?.option !== undefined;
    nextBtn.disabled = !hasAnswer;
}

function updateProgress() {
    const progress = ((currentQuestion + 1) / questions.length) * 100;
    document.getElementById('progressFill').style.width = progress + '%';
    document.getElementById('progressText').textContent = 
        `سؤال ${currentQuestion + 1} من ${questions.length}`;
}
// ==========================================
// Submit Quiz
// ==========================================

function submitQuiz() {
    // Show loading screen
    document.getElementById('loadingScreen').classList.add('active');
    
    // Prepare data for backend
    const quizData = {
        answers: answers,
        timestamp: new Date().toISOString(),
        userId: localStorage.getItem('sportsync_user_id') || 'anonymous'
    };
    
    // Save final answers
    localStorage.setItem('sportsync_quiz_complete', JSON.stringify(quizData));
    
    // Simulate processing (3 seconds) then redirect
    setTimeout(() => {
        // TODO: Send to backend API
        console.log('Quiz Data:', quizData);
        
        // Redirect to results (backend URL)
        window.location.href = 'https://sportsync-ai-quiz.onrender.com?quiz_complete=true';
    }, 3000);
}

// ==========================================
// Initialization
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    loadProgress();
    renderQuestion();
    
    console.log('🎯 SportSync Quiz Ready!');
    console.log(`Loaded ${questions.length} questions`);
});

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' && currentQuestion > 0) {
        previousQuestion();
    } else if (e.key === 'ArrowLeft' && !document.getElementById('nextBtn').disabled) {
        nextQuestion();
    }
});

console.log('✨ SportSync AI Quiz Loaded Successfully!');