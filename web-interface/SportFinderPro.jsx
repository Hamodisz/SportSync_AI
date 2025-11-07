import React, { useState, useEffect, useRef } from 'react';
import { Send, Brain, Zap, Target, CheckCircle, AlertCircle, Loader2, MessageCircle } from 'lucide-react';

const SportFinderProFIXED = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiLogs, setAiLogs] = useState([]);
  const [typingText, setTypingText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // ═══════════════════════════════════════════════════════
  // CRITICAL: API KEY & MODELS CONFIGURATION
  // ═══════════════════════════════════════════════════════
  // SECURITY: API Key should be loaded from environment variables
  // In production, use process.env.REACT_APP_OPENAI_API_KEY
  // For development, replace with your key (NEVER commit to GitHub!)
  const API_KEY = process.env.REACT_APP_OPENAI_API_KEY || 'YOUR_API_KEY_HERE';

  const AI_MODELS = {
    fast: process.env.REACT_APP_AI_FAST_MODEL || 'gpt-3.5-turbo',      // ⚡ Quick understanding
    reasoning: process.env.REACT_APP_AI_REASONING_MODEL || 'o1-mini',  // 🧠 Deep reasoning (O1!)
    intelligence: process.env.REACT_APP_AI_INTELLIGENCE_MODEL || 'gpt-4' // 🎯 Final recommendation
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, aiLogs, typingText]);

  useEffect(() => {
    setMessages([{
      role: 'assistant',
      content: 'مرحباً! 👋\n\nأنا هنا عشان أساعدك تلاقي الرياضة المثالية لك.\n\nخلنا نبدأ بسؤال بسيط:\n**كيف حاسس اليوم؟** وش اللي يضايقك أو يهمك بخصوص نشاطك البدني؟'
    }]);
  }, []);

  // ═══════════════════════════════════════════════════════
  // AI LOGGING SYSTEM (NO FALLBACK)
  // ═══════════════════════════════════════════════════════
  const addLog = (layer, status, message, duration = null) => {
    setAiLogs(prev => [...prev, {
      layer,
      status,
      message,
      duration,
      timestamp: new Date().toLocaleTimeString('ar-SA', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        fractionalSecondDigits: 1
      })
    }]);
  };

  // ═══════════════════════════════════════════════════════
  // CORE AI CALL FUNCTION (NO FALLBACK ALLOWED)
  // ═══════════════════════════════════════════════════════
  const callAI = async (model, messages, temperature = 0.7, maxTokens = 1500) => {
    const startTime = Date.now();
    
    const payload = {
      model,
      messages,
      temperature,
      max_tokens: maxTokens
    };

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMsg = errorData.error?.message || response.statusText;
      throw new Error(`❌ ${model} FAILED - NO FALLBACK: ${errorMsg}`);
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    return { data: await response.json(), duration };
  };

  // ═══════════════════════════════════════════════════════
  // TYPING EFFECT FOR USER-FRIENDLY EXPERIENCE
  // ═══════════════════════════════════════════════════════
  const simulateTyping = async (text, speed = 30) => {
    setIsTyping(true);
    setTypingText('');
    
    for (let i = 0; i < text.length; i++) {
      setTypingText(text.slice(0, i + 1));
      await new Promise(resolve => setTimeout(resolve, speed));
    }
    
    setIsTyping(false);
    return text;
  };

  // ═══════════════════════════════════════════════════════
  // TRIPLE AI ANALYSIS ENGINE (3 LAYERS)
  // ═══════════════════════════════════════════════════════
  const analyzeWithTripleAI = async (userMessage) => {
    setLoading(true);
    setAiLogs([]);
    setTypingText('');

    try {
      // ═════════════════════════════════════════
      // LAYER 1: ⚡ Fast Intelligence
      // ═════════════════════════════════════════
      addLog('fast', 'running', 'بدأ التحليل السريع للمشاعر والقيود...');
      
      const { data: fastData, duration: fastDuration } = await callAI(AI_MODELS.fast, [
        {
          role: 'system',
          content: `أنت محلل سريع محترف. استخرج من رسالة المستخدم:
1. emotion: الحالة العاطفية (frustrated/motivated/tired/confused/anxious/excited)
2. constraints: القيود العملية (وقت، مكان، ميزانية، إصابات، معدات)
3. goals: الأهداف الحقيقية (weight_loss/stress_relief/social/performance/health)
4. readiness_level: مستوى الجاهزية (low/medium/high)

أجب فقط بـ JSON بهذا الشكل - لا تضف أي نص إضافي:
{
  "emotion": "...",
  "constraints": ["...", "..."],
  "goals": ["...", "..."],
  "readiness_level": "..."
}`
        },
        {
          role: 'user',
          content: userMessage
        }
      ], 0.3, 400);

      const responseText = fastData.choices[0].message.content;
      const cleanedJSON = responseText.replace(/```json\n?|```\n?/g, '').trim();
      const quickInsights = JSON.parse(cleanedJSON);
      
      addLog('fast', 'success', 
        `✓ تم: ${quickInsights.emotion} | ${quickInsights.constraints.length} قيود | جاهزية ${quickInsights.readiness_level}`,
        fastDuration
      );

      // ═════════════════════════════════════════
      // LAYER 2: 🧠 Deep Reasoning (O1-MINI)
      // ═════════════════════════════════════════
      addLog('reasoning', 'running', 'بدأ التفكير العميق (Z-layer: الدوافع الخفية)...');

      const { data: reasoningData, duration: reasoningDuration } = await callAI(AI_MODELS.reasoning, [
        {
          role: 'user',
          content: `المستخدم قال: "${userMessage}"

**التحليل السريع:**
- المشاعر: ${quickInsights.emotion}
- القيود: ${quickInsights.constraints.join(', ')}
- الأهداف: ${quickInsights.goals.join(', ')}
- الجاهزية: ${quickInsights.readiness_level}

**مهمتك الآن (تحليل Z-layer العميق):**

1. **الدوافع الخفية**: ما الأسباب الحقيقية غير المعلنة وراء كلامه؟ (خوف، رغبة، حنين، ضغط اجتماعي؟)

2. **الحواجز النفسية/العملية**: ما الذي قد يمنعه من الالتزام؟ (خجل، ملل، قلة ثقة، جدول مزدحم؟)

3. **مستوى الاستعداد الحقيقي**: هل هو مستعد فعلاً للالتزام أم مجرد فضول؟ دلل بأمثلة من كلامه.

4. **الرياضة المثالية**: بناءً على كل ما سبق، ما الرياضة التي تناسبه 100%؟ اذكر السبب المنطقي لكل عنصر من تحليلك.

اكتب تحليل عميق بالعربية بدون مقدمات - ابدأ مباشرة بالتحليل.`
        }
      ], 1, 2000); // O1 needs temp=1

      const deepAnalysis = reasoningData.choices[0].message.content;
      addLog('reasoning', 'success', 
        `✓ تحليل Z-layer مكتمل (${deepAnalysis.length} حرف)`,
        reasoningDuration
      );

      // ═════════════════════════════════════════
      // LAYER 3: 🎯 Intelligence (GPT-4)
      // ═════════════════════════════════════════
      addLog('intelligence', 'running', 'بدأ صياغة التوصية النهائية...');

      const { data: finalData, duration: intelligenceDuration } = await callAI(AI_MODELS.intelligence, [
        {
          role: 'system',
          content: `أنت مستشار رياضي محترف وودود. لديك تحليل كامل للمستخدم:

**📊 التحليل السريع:**
${JSON.stringify(quickInsights, null, 2)}

**🧠 التحليل العميق (Z-layer):**
${deepAnalysis}

**مهمتك الآن:**
اكتب توصية شخصية user-friendly للمستخدم باللغة العربية. اتبع هذه القواعد:

✅ **قواعد الكتابة:**
1. استخدم "أنت" بدل "المستخدم" - كلمه مباشرة
2. اكتب كأنك صديق يساعد صديقه (دافئ وشخصي)
3. **ممنوع bullet points أو نقاط مرقمة** - اكتب فقرات طبيعية
4. استخدم رموز تعبيرية بسيطة (emoji) لكن بتوازن
5. لا تكتب عناوين أو headers - فقط كلام طبيعي

✅ **محتوى التوصية:**
1. اعترف بمشاعره/قيوده (أظهر أنك فاهمه)
2. اشرح **بالضبط** ليش هذي الرياضة مناسبة له (بناءً على التحليل العميق)
3. أعطي خطوة أولى عملية وواضحة جداً للبداية
4. حفزه بطريقة حقيقية (مو كليشيهات أو مبالغة)
5. أنهي بجملة دافئة تشجعه

**مهم جداً:** لا تكتب مثل روبوت. اكتب كأنك إنسان يفهم ويتعاطف.`
        },
        {
          role: 'user',
          content: 'اكتب التوصية النهائية الآن'
        }
      ], 0.8, 1500);

      const finalRecommendation = finalData.choices[0].message.content;
      
      const totalTime = (parseFloat(fastDuration) + parseFloat(reasoningDuration) + parseFloat(intelligenceDuration)).toFixed(1);
      addLog('intelligence', 'success', 
        `✓ التوصية جاهزة - إجمالي الوقت: ${totalTime}s`,
        intelligenceDuration
      );

      // ═════════════════════════════════════════
      // TYPING EFFECT FOR USER-FRIENDLY UX
      // ═════════════════════════════════════════
      await simulateTyping(finalRecommendation, 20);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: finalRecommendation,
        metadata: {
          totalTime,
          layers: {
            fast: fastDuration,
            reasoning: reasoningDuration,
            intelligence: intelligenceDuration
          }
        }
      }]);

      setLoading(false);

    } catch (error) {
      // NO FALLBACK - SHOW EXACT ERROR
      addLog('system', 'error', `❌ فشل النظام: ${error.message}`);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ **فشل النظام الذكي - لا يوجد Fallback!**\n\n**الخطأ:** ${error.message}\n\n**التشخيص:**\nالنظام مصمم بـ 3 طبقات ذكاء:\n- ⚡ Fast (GPT-3.5) \n- 🧠 Reasoning (o1-mini)\n- 🎯 Intelligence (GPT-4)\n\n**تحقق من:**\n1. صلاحية API Key\n2. الاتصال بالإنترنت\n3. حد الاستخدام من OpenAI\n\n**حاول مرة أخرى بعد قليل.**`
      }]);
      
      setLoading(false);
      setIsTyping(false);
    }
  };

  // ═══════════════════════════════════════════════════════
  // HANDLE USER MESSAGE SUBMISSION
  // ═══════════════════════════════════════════════════════
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');

    await analyzeWithTripleAI(userMessage);
  };

  // ═══════════════════════════════════════════════════════
  // RENDER UI
  // ═══════════════════════════════════════════════════════
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col">
      {/* HEADER */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 shadow-2xl">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
          <Brain className="w-8 h-8" />
          🧠 نظام الذكاء الثلاثي
        </h1>
        <p className="text-sm opacity-90">⚡ Fast → 🧠 Reasoning → 🎯 Intelligence | ❌ لا يوجد Fallback</p>
      </div>

      {/* AI LOGS PANEL */}
      {aiLogs.length > 0 && (
        <div className="bg-gray-900 border-b border-gray-700 p-4 max-h-48 overflow-y-auto">
          <div className="space-y-2">
            {aiLogs.map((log, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="text-gray-500 text-xs font-mono">{log.timestamp}</span>
                {log.status === 'running' && <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />}
                {log.status === 'success' && <CheckCircle className="w-4 h-4 text-green-400" />}
                {log.status === 'error' && <AlertCircle className="w-4 h-4 text-red-400" />}
                <span className={`
                  ${log.layer === 'fast' ? 'text-blue-400' : ''}
                  ${log.layer === 'reasoning' ? 'text-purple-400' : ''}
                  ${log.layer === 'intelligence' ? 'text-green-400' : ''}
                  ${log.layer === 'system' ? 'text-red-400' : ''}
                  font-semibold text-xs uppercase
                `}>
                  {log.layer === 'fast' && '⚡ FAST'}
                  {log.layer === 'reasoning' && '🧠 REASONING'}
                  {log.layer === 'intelligence' && '🎯 INTELLIGENCE'}
                  {log.layer === 'system' && '⚠️ SYSTEM'}
                </span>
                <span className="text-gray-300">{log.message}</span>
                {log.duration && (
                  <span className="text-gray-500 text-xs ml-auto">{log.duration}s</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MESSAGES AREA */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl p-4 rounded-2xl ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-800 text-gray-100'
            }`}>
              <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
              {msg.metadata && (
                <div className="mt-3 pt-3 border-t border-gray-700 text-xs text-gray-400">
                  <div className="flex gap-4">
                    <span>⚡ {msg.metadata.layers.fast}s</span>
                    <span>🧠 {msg.metadata.layers.reasoning}s</span>
                    <span>🎯 {msg.metadata.layers.intelligence}s</span>
                    <span className="ml-auto font-semibold">⏱️ {msg.metadata.totalTime}s</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {/* TYPING INDICATOR */}
        {isTyping && typingText && (
          <div className="flex justify-start">
            <div className="max-w-2xl p-4 rounded-2xl bg-gray-800 text-gray-100">
              <div className="flex items-center gap-2 mb-2">
                <MessageCircle className="w-4 h-4 animate-pulse text-green-400" />
                <span className="text-xs text-gray-400">يكتب الآن...</span>
              </div>
              <div className="whitespace-pre-wrap leading-relaxed">{typingText}</div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* INPUT AREA */}
      <form onSubmit={handleSubmit} className="p-6 bg-gray-900 border-t border-gray-700">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="اكتب رسالتك هنا..."
            disabled={loading}
            className="flex-1 p-4 bg-gray-800 text-white rounded-xl border border-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>يحلل...</span>
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                <span>إرسال</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SportFinderProFIXED;