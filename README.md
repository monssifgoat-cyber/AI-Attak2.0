# فريق اختبار الاختراق الآلي (Pentest Agent Team)

أداة تؤتمت دورة اختبار اختراق مواقع الويب لتقليل العمل اليدوي المتكرر
لفريقكم: **استطلاع ← فحص ← تحقق من قابلية الاستغلال ← تقرير CVSS**.

## ⚠️ قبل أي استخدام

- استخدمها فقط ضمن نطاق موقّع ومتفق عليه صراحةً مع العميل (`scope.targets`
  في `config.yaml`).
- لا يوجد في هذه الأداة أي خيار لتعطيل التحقق من النطاق (Scope Guard)
  بالكامل، لا من الإعدادات ولا من سطر الأوامر — هذا مقصود. لإضافة هدف
  جديد تملكون تفويضًا موثّقًا له، استخدموا `--add-target`.
- الاستغلال الفعلي (فتح shell) لا يحدث تلقائيًا أبدًا، حتى لو كان
  `exploit.mode: full` في الإعدادات — يتطلب أيضًا `--confirm-exploit`
  صراحةً في كل تشغيلة، أي قرارًا بشريًا واعيًا، وليس قرارًا يتخذه النموذج.

## البنية

```
pentest-agent-team/
├── config.yaml              # النطاق، الأدوات، مزوّد الـ LLM، وضع الاستغلال
├── main.py                  # المنسّق الرئيسي
├── core/
│   ├── scope_guard.py       # يمنع تشغيل أي مرحلة خارج النطاق
│   ├── llm.py                # غلاف موحّد لـ Ollama/Gemini
│   ├── zap_client.py         # تكامل REST مع OWASP ZAP
│   ├── msf_client.py         # تكامل RPC مع Metasploit (check أولًا)
│   ├── tool_runner.py        # تشغيل nmap/httpx/katana/nuclei/sqlmap
│   └── agents/
│       ├── recon.py          # ReconAgent
│       ├── scanner.py        # ScannerAgent
│       ├── exploiter.py      # ExploiterAgent
│       └── reporter.py       # ReporterAgent
├── docker-compose.yml        # zap + ollama + team
└── Dockerfile
```

## ما الذي تغيّر مقارنةً بالنسخة التي أرسلتها (وما الذي لم يتغيّر)

**لم يتغيّر**: فكرة الأداة ومراحلها الأربع، أسماء الفئات
(`ReconAgent`/`ScannerAgent`/`ExploiterAgent`/`ReporterAgent`)، استخدام
Ollama محليًا و Gemini كبديل، `destructive: false`، وبنية `config.yaml`
العامة.

**تمت إضافته/تنفيذه فعليًا** (كان هيكلًا فارغًا في الملفات المرسلة):
دمج فعلي مع nmap/httpx/katana (استطلاع)، ZAP/nuclei/sqlmap (فحص)،
و Metasploit عبر RPC (تحقق من الاستغلال)، تماشيًا مع ما سبق أن استقر
عليه التصميم معي.

**التغيير الوحيد المتعمّد في السلوك**: `ExploiterAgent` يكتفي افتراضيًا
بـ `check()` الآمن (يسأل module هل الهدف عرضة للثغرة دون إرسال أي
payload). تنفيذ استغلال فعلي ممكن تقنيًا عبر `msf_client.exploit()`،
لكنه مربوط ببوابة `--confirm-exploit` كما هو موضّح أعلاه. لم أكتب أي
كود استغلال (exploit) من الصفر بنفسي — الأداة تُشغّل وتُنسّق أدوات
pentest معروفة وموثّقة (ZAP، nuclei، sqlmap، Metasploit)، وهذا هو
الحد الذي أستطيع المساعدة ضمنه.

## الإعداد

1. **المتطلبات على المضيف** (Kali Linux أو غيره):
   ```bash
   # شغّل msfrpcd قبل مرحلة exploit
   msfrpcd -P <كلمة-مرور-قوية> -S -a 127.0.0.1 -p 55553
   ```
2. انسخ `.env.example` إلى `.env` واملأ `MSF_RPC_PASSWORD` (ونفس القيمة
   في `msfrpcd` أعلاه) و `ZAP_API_KEY` و `GEMINI_API_KEY` إن استخدمت Gemini.
3. عدّل `scope.targets` في `config.yaml` ليطابق النطاق الموقّع مع العميل.
4. ```bash
   docker compose up --build
   ```

## الاستخدام

```bash
# تشغيل كامل
docker compose exec team python main.py

# إضافة هدف جديد لهذه الجلسة فقط (بعد تفويض موثّق من العميل)
docker compose exec team python main.py --add-target "https://new.example.com"

# مرحلة واحدة فقط
docker compose exec team python main.py --only-stage scan

# السماح باستغلال فعلي (بعد مراجعة نتائج check() يدويًا)
docker compose exec team python main.py --confirm-exploit
```

## ملاحظة حول النموذج المحلي والرام

`qwen2.5:14b` المحدّد افتراضيًا في `config.yaml` يحتاج تقريبًا 9-10 جيجا
رام فعليًا (بصيغة Q4). على جهاز محلي بـ3 جيجا رام لن يعمل. الخيارات:
- التشغيل على Oracle Cloud Free Tier (حتى 24 جيجا رام على ARM) كما كان
  مخطَّطًا للنشر — يعمل qwen2.5:14b هناك دون مشاكل.
- أو تبديل `llm.model` محليًا إلى نموذج أصغر مثل `qwen2.5:3b`.
- أو `llm.provider: gemini` لمراحل التحليل الثقيلة (التقرير والتحقق من
  الاستغلال) مع إبقاء Ollama لما هو أخف إن رغبت.

## التقرير

يُحفظ في `reports/report.json` (كامل البيانات) و `reports/report.md`
(بتنسيق CVSS قابل للقراءة مباشرة).
