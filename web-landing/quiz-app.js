// ==========================================
// SportSync AI - Quiz Application
// ==========================================

// Questions Data (10 Questions)
const questions = [
    {
        id: 1,
        title: "متى آخر مرة شعرت بـ 'الانسجام التام'؟",
        description: "تلك اللحظة اللي تنسى فيها الوقت والمكان، وتذوب في النشاط اللي تسويه. علماء النفس يسمونها 'Flow State' - ونحن نبحث عن رياضة توصلك لهذا الشعور دائماً.",
        tip: "💡 فكّر: هل كنت مع ناس أو لوحدك؟ في الطبيعة أو مكان مغلق؟ تتحرك أو تركز ذهنياً؟",
        options: [
            "في نقاش عميق - أتبادل أفكار مع أشخاص مثيرين للاهتمام",
            "أحل مشكلة معقدة - تحدي ذهني يستهلك انتباهي بالكامل",
            "أتحرك بحرية - جري، رقص، أي شي يحرك جسمي",
            "في الطبيعة - أمشي، أتأمل، أستكشف مكان جديد",
            "أخلق شيئاً - رسم، كتابة، بناء، أي عمل إبداعي"
        ],
        allowText: true,
        textPlaceholder: "صف لنا آخر مرة نسيت فيها نفسك في نشاط معين..."
    },
    {
        id: 2,
        title: "لو كان عندك يوم كامل بدون أي التزامات، وش تسوي؟",
        description: "ليس 'ماذا يجب أن تفعل' - بل ماذا تفعل فعلاً عندما لا يراقبك أحد ولا توجد توقعات. هذا يكشف دوافعك الحقيقية.",
        tip: "💡 أول شي يطرى في بالك - لا تفكر 'وش المفروض'",
        options: [
            "أستكشف - أروح مكان جديد أو أجرب تجربة غريبة",
            "أتعلم - أقرأ، أشاهد محتوى مفيد، أطور مهارة",
            "أرتاح فقط - نوم، مسلسلات، أي شي ما يحتاج مجهود",
            "أتواصل - أقضي وقت مع أشخاص أحبهم",
            "أبني شيئاً - مشروع، هواية، أي شي ملموس"
        ],
        allowText: true,
        textPlaceholder: "آخر يوم إجازة حقيقية، وش سويت؟"
    },
    {
        id: 3,
        title: "عندما تغضب أو تتوتر، جسمك يطلب منك إيش؟",
        description: "جسمك أذكى منك. عندما تضغط عليك الحياة، جسمك يعرف وش يحتاج عشان يعيد التوازن. استمع له - هذا مؤشر مهم لنوع النشاط اللي يناسبك.",
        tip: "💡 لا تقول 'ما أدري' - حتى لو ما تسوي الشي، جسمك يعطيك إشارات",
        options: [
            "يطلب حركة - حاس بطاقة زايدة، أبي أكسر شي أو أجري",
            "يطلب هدوء - أبي أنعزل، أتنفس، ما أبي أحد يكلمني",
            "يطلب تنفيس - أبي أتكلم، أصارخ، أطلع اللي جواي",
            "يطلب تحدي - أبي ألعب لعبة صعبة أو أحل مشكلة تشغل عقلي",
            "يطلب لمسة طبيعة - أبي أطلع برا، أشم هوا، أشوف سما"
        ],
        allowText: true,
        textPlaceholder: "آخر مرة زعلت جداً، وش سويت (أو تمنيت تسوي)؟"
    }    ,{
        id: 4,
        title: "في أي لحظة من اليوم تحس جسمك 'صاحي' فعلاً؟",
        description: "مو سؤال عن الساعة - بل عن الحالة. متى تحس إن جسمك مستعد يتحرك؟ هذا يحدد متى وكيف تمارس الرياضة المثالية لك.",
        tip: "💡 انتبه: 'وقت الطاقة' مختلف عن 'وقت الاستيقاظ'",
        options: [
            "بعد ما أصحى مباشرة - جسمي جاهز قبل ما يبدأ اليوم",
            "بعد القهوة الأولى - محتاج kickstart بسيط",
            "العصر / المغرب - ذروة طاقتي بعد الظهر",
            "الليل - أنشط بعد ما يهدى العالم",
            "متقلب - يعتمد على النوم والأكل واليوم"
        ],
        allowText: true,
        textPlaceholder: "متى آخر مرة حسيت بطاقة قوية وحركت جسمك؟"
    },
    {
        id: 5,
        title: "لو جسمك يقدر يتكلم، وش بيقولك الحين؟",
        description: "جسمك عنده رأي واضح. بعض الأجسام تقول 'اتركني أرتاح'، وأخرى تصارخ 'حركني الآن!'. استمع له - هذا أهم سؤال.",
        tip: "💡 كن صادق 100% - ما نبي نجبرك على شي جسمك يرفضه",
        options: [
            "'أنا مستعد لأي شي' - محتاج تحدي جسدي قوي",
            "'تعامل معي بلطف' - أبي نشاط خفيف وآمن",
            "'حركني بس ببطء' - أبي أبدأ من الصفر بدون ضغط",
            "'أنا محتاج استشفاء' - عندي ألم أو تعب مزمن",
            "'جربني بشي جديد' - مستعد لتجربة غير تقليدية"
        ],
        allowText: true,
        textPlaceholder: "لو عندك ألم أو إصابة سابقة، اكتبها هنا..."
    },
    {
        id: 6,
        title: "وش أكثر شي يخليك تستمر في نشاط معين؟",
        description: "الناس يتركون الرياضة مو لأنها صعبة - بل لأنها ما تعطيهم الشي اللي يبحثون عنه. نحن نبي نعرف وش 'الوقود' اللي يخليك تستمر.",
        tip: "💡 فكّر في شي استمريت فيه لفترة طويلة - ليش؟",
        options: [
            "النتائج المرئية - أشوف جسمي يتغير، أرقامي تتحسن",
            "الشعور الفوري - أحس أحسن بعد كل جلسة مباشرة",
            "التطور التدريجي - كل أسبوع ألاحظ شي جديد أقدر أسويه",
            "الانتماء - أحس إني جزء من مجموعة أو مجتمع",
            "المتعة البحتة - ما يهمني أي شي، بس استمتع"
        ],
        allowText: true,
        textPlaceholder: "حدثنا عن نشاط استمريت فيه (رياضي أو غيره)..."
    },
    {
        id: 7,
        title: "لو تخيلت نفسك في أفضل لحظة رياضية، وين تكون؟",
        description: "أغمض عينيك. تخيل نفسك تتحرك، مستمتع، في قمة الانسجام. وين المكان؟ هذا ليس سؤال منطقي - بل حدسي. أول إجابة تطرى في بالك.",
        tip: "💡 لا تفكر في 'الواقعية' - فقط تخيل المكان المثالي",
        options: [
            "في قلب الطبيعة البرية - جبال، بحر، صحراء",
            "في مدينة نابضة - شوارع، حدائق حضرية، أماكن عامة",
            "في مكان خاص بي - غرفتي، حديقة بيتي، مساحتي الخاصة",
            "في منشأة متخصصة - صالة رياضية، استوديو، مكان مجهز",
            "ما يهم المكان - المهم النشاط والشعور"
        ],
        allowText: true,
        textPlaceholder: "صف لنا هذا المكان بالتفصيل..."
    }    ,{
        id: 8,
        title: "إذا نجحت في هذه الرياضة، وش أول شي تبي تحسه؟",
        description: "النجاح له أشكال مختلفة. بعض الناس يبون يحسون بالقوة، وآخرون يبون السلام الداخلي. ما فيه صح أو غلط - بس وش أنت تبي؟",
        tip: "💡 لا تفكر في 'المفروض' - وش أنت فعلاً تتمنى تحسه؟",
        options: [
            "'أنا قوي' - أحس بجسمي قادر على أي شي",
            "'أنا هادئ' - عقلي صافي ومتوازن داخلياً",
            "'أنا حي' - أحس بكل خلية في جسمي تنبض",
            "'أنا فخور' - حققت شي كنت أظن مستحيل",
            "'أنا منتمي' - جزء من مجموعة تفهمني"
        ],
        allowText: true,
        textPlaceholder: "صف أجمل شعور داخلي مرّ عليك..."
    },
    {
        id: 9,
        title: "لو تقدر تهدي نفسك 'قوة خارقة' جسدية وحدة، وش بتختار؟",
        description: "هذا السؤال يكشف رغبتك العميقة. مو عن الواقع - بل عن الحلم. جوابك يحدد نوع الشعور اللي نبي نوصلك له في الرياضة.",
        tip: "💡 أول شي يطرى في بالك - لا تفكر 'هل هذا منطقي؟'",
        options: [
            "قدرة تحمل لا نهائية - ما أتعب أبداً",
            "سرعة خارقة - أطير على الأرض",
            "مرونة مذهلة - جسمي يتحرك بسلاسة تامة",
            "قوة هائلة - أرفع أي شي وأكسر أي حاجز",
            "توازن مثالي - ما أقع ولا أتعثر أبداً"
        ],
        allowText: true,
        textPlaceholder: "ليش اخترت هذي القوة بالذات؟"
    },
    {
        id: 10,
        title: "آخر سؤال: لو هذي الرياضة 'تغيرك'، وش تبي تصير؟",
        description: "الرياضة مو بس حركة - إنها تحول. مين تبي تكون بعد 6 أشهر من الالتزام؟ هذا أهم سؤال - لأن الجواب يحدد رياضتك المثالية.",
        tip: "💡 كن طموح - نحن نخترع رياضة تحولك للشخص اللي تحلم تكونه",
        options: [
            "أقوى نسخة من نفسي - جسدياً وذهنياً",
            "أكثر هدوءاً وسلاماً - متصالح مع نفسي",
            "أكثر مغامرة وجرأة - أواجه مخاوفي",
            "أكثر انضباطاً والتزاماً - روتين وعادات صحية",
            "أكثر حرية وانطلاقاً - متحرر من القيود"
        ],
        allowText: true,
        textPlaceholder: "اكتب رسالة لنفسك بعد 6 أشهر - وش تقولها؟"
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