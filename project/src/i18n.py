# -*- coding: utf-8 -*-
"""
Pre-written, reviewable translations (no machine translation at run time).

IMPORTANT: Hindi and Marathi wording was drafted for this prototype and MUST be
checked by a native speaker (ideally with medical-communication experience)
before any real-world use. Wording is kept deliberately simple.
"""

LANGUAGES = {"en": "English", "hi": "हिन्दी", "mr": "मराठी"}

T = {
    "en": {
        "title": "Pancreatic Cancer Risk Screening (Research Prototype)",
        "subtitle": "Enter the patient's values to see an estimated risk and what drove it.",
        "disclaimer": "Educational/research prototype only. This is NOT a medical diagnosis. "
                      "Please consult a doctor for any health concern.",
        "language": "Language", "inputs": "Patient values",
        "age": "Age (years)", "sex": "Sex", "sex_F": "Female", "sex_M": "Male",
        "creatinine": "Creatinine (mg/ml)", "LYVE1": "LYVE1 (ng/ml)",
        "REG1B": "REG1B (ng/ml)", "TFF1": "TFF1 (ng/ml)",
        "plasma_CA19_9": "Plasma CA19-9 (U/ml)", "REG1A": "REG1A (ng/ml)",
        "measured_ca": "CA19-9 was measured", "measured_reg": "REG1A was measured",
        "predict": "Estimate risk", "risk_estimate": "Estimated risk score",
        "band_high": "Higher risk signal", "band_inconclusive": "Inconclusive",
        "band_low": "Lower risk signal",
        "guide_high": "The estimated risk is high. Please see a doctor for further tests.",
        "guide_inconclusive": "The result is not clear. Please consult a doctor, and repeat testing if advised.",
        "guide_low": "The estimated risk is low, but this is not a diagnosis. See a doctor if you have symptoms.",
        "expect_high": "What to expect: your doctor may repeat the tests and may suggest imaging (such as CT or MRI) or other checks. A higher-risk signal is a reason for follow-up, not a diagnosis.",
        "expect_inconclusive": "What to expect: the result is borderline, so your doctor may repeat the tests after some time and review them together with your symptoms and history.",
        "expect_low": "What to expect: this estimate alone does not suggest urgent follow-up. Keep up regular check-ups and see a doctor promptly if you develop persistent abdominal or back pain, unexplained weight loss, or yellowing of the skin or eyes.",
        "factors": "What influenced this result",
        "raised": "{f} is increasing the estimated risk.",
        "lowered": "{f} is decreasing the estimated risk.",
        "warn_range": "{f} is outside the range seen in the training data; treat the result with extra caution.",
        "report": "Download report", "report_title": "Risk Screening Report",
        "about": "About this model",
        "about_text": "Random Forest trained on 590 samples (urinary biomarkers, Debernardi et al. 2020), "
                      "probabilities calibrated, threshold tuned for high sensitivity. Not externally validated.",
        "age_name": "Age", "sex_name": "Sex", "creatinine_name": "Creatinine",
    },
    "hi": {
        "title": "अग्नाशय कैंसर जोखिम स्क्रीनिंग (शोध प्रोटोटाइप)",
        "subtitle": "अनुमानित जोखिम और उसके कारण देखने के लिए मरीज़ के मान भरें।",
        "disclaimer": "यह केवल शैक्षणिक/शोध प्रोटोटाइप है। यह चिकित्सकीय निदान नहीं है। "
                      "किसी भी स्वास्थ्य संबंधी चिंता के लिए कृपया डॉक्टर से परामर्श करें।",
        "language": "भाषा", "inputs": "मरीज़ के मान",
        "age": "आयु (वर्ष)", "sex": "लिंग", "sex_F": "महिला", "sex_M": "पुरुष",
        "creatinine": "क्रिएटिनिन (mg/ml)", "LYVE1": "LYVE1 (ng/ml)",
        "REG1B": "REG1B (ng/ml)", "TFF1": "TFF1 (ng/ml)",
        "plasma_CA19_9": "प्लाज़्मा CA19-9 (U/ml)", "REG1A": "REG1A (ng/ml)",
        "measured_ca": "CA19-9 की जाँच हुई है", "measured_reg": "REG1A की जाँच हुई है",
        "predict": "जोखिम का अनुमान लगाएँ", "risk_estimate": "अनुमानित जोखिम स्कोर",
        "band_high": "अधिक जोखिम का संकेत", "band_inconclusive": "अनिर्णायक",
        "band_low": "कम जोखिम का संकेत",
        "guide_high": "अनुमानित जोखिम अधिक है। कृपया आगे की जाँच के लिए डॉक्टर से मिलें।",
        "guide_inconclusive": "परिणाम स्पष्ट नहीं है। कृपया डॉक्टर से सलाह लें और सलाह मिलने पर जाँच दोबारा करवाएँ।",
        "guide_low": "अनुमानित जोखिम कम है, लेकिन यह निदान नहीं है। लक्षण हों तो डॉक्टर से मिलें।",
        "expect_high": "आगे क्या होगा: डॉक्टर जाँच दोबारा करवा सकते हैं और इमेजिंग (जैसे CT या MRI) या अन्य जाँच सुझा सकते हैं। अधिक जोखिम का संकेत आगे की जाँच का कारण है, निदान नहीं।",
        "expect_inconclusive": "आगे क्या होगा: परिणाम सीमा-रेखा पर है, इसलिए डॉक्टर कुछ समय बाद जाँच दोबारा करवा सकते हैं और आपके लक्षणों व इतिहास के साथ देखेंगे।",
        "expect_low": "आगे क्या होगा: केवल इस अनुमान के आधार पर तत्काल फ़ॉलो-अप का सुझाव नहीं है। नियमित जाँच करवाते रहें और लगातार पेट या पीठ में दर्द, बिना कारण वज़न घटने, या त्वचा/आँखों के पीले पड़ने जैसे लक्षण हों तो तुरंत डॉक्टर से मिलें।",
        "factors": "इस परिणाम को किसने प्रभावित किया",
        "raised": "{f} का मान अनुमानित जोखिम को बढ़ा रहा है।",
        "lowered": "{f} का मान अनुमानित जोखिम को घटा रहा है।",
        "warn_range": "{f} प्रशिक्षण डेटा की सीमा से बाहर है; परिणाम को अतिरिक्त सावधानी से देखें।",
        "report": "रिपोर्ट डाउनलोड करें", "report_title": "जोखिम स्क्रीनिंग रिपोर्ट",
        "about": "इस मॉडल के बारे में",
        "about_text": "Random Forest मॉडल, 590 नमूनों (मूत्र बायोमार्कर, Debernardi et al. 2020) पर प्रशिक्षित; "
                      "संभावनाएँ कैलिब्रेटेड हैं और सीमा उच्च संवेदनशीलता के लिए चुनी गई है। बाहरी सत्यापन नहीं हुआ है।",
        "age_name": "आयु", "sex_name": "लिंग", "creatinine_name": "क्रिएटिनिन",
    },
    "mr": {
        "title": "स्वादुपिंड कर्करोग जोखीम तपासणी (संशोधन प्रोटोटाइप)",
        "subtitle": "अंदाजित जोखीम आणि त्याची कारणे पाहण्यासाठी रुग्णाची मूल्ये भरा.",
        "disclaimer": "हा फक्त शैक्षणिक/संशोधन प्रोटोटाइप आहे. हे वैद्यकीय निदान नाही. "
                      "आरोग्याबाबत कोणतीही चिंता असल्यास कृपया डॉक्टरांचा सल्ला घ्या.",
        "language": "भाषा", "inputs": "रुग्णाची मूल्ये",
        "age": "वय (वर्षे)", "sex": "लिंग", "sex_F": "स्त्री", "sex_M": "पुरुष",
        "creatinine": "क्रिएटिनिन (mg/ml)", "LYVE1": "LYVE1 (ng/ml)",
        "REG1B": "REG1B (ng/ml)", "TFF1": "TFF1 (ng/ml)",
        "plasma_CA19_9": "प्लाझ्मा CA19-9 (U/ml)", "REG1A": "REG1A (ng/ml)",
        "measured_ca": "CA19-9 ची तपासणी झाली आहे", "measured_reg": "REG1A ची तपासणी झाली आहे",
        "predict": "जोखमीचा अंदाज काढा", "risk_estimate": "अंदाजित जोखीम गुण",
        "band_high": "जास्त जोखमीचा संकेत", "band_inconclusive": "अनिर्णायक",
        "band_low": "कमी जोखमीचा संकेत",
        "guide_high": "अंदाजित जोखीम जास्त आहे. कृपया पुढील तपासणीसाठी डॉक्टरांना भेटा.",
        "guide_inconclusive": "निकाल स्पष्ट नाही. कृपया डॉक्टरांचा सल्ला घ्या आणि सांगितल्यास तपासणी पुन्हा करा.",
        "guide_low": "अंदाजित जोखीम कमी आहे, पण हे निदान नाही. लक्षणे असल्यास डॉक्टरांना भेटा.",
        "expect_high": "पुढे काय होईल: डॉक्टर तपासण्या पुन्हा करायला सांगू शकतात आणि इमेजिंग (उदा. CT किंवा MRI) किंवा इतर तपासण्या सुचवू शकतात. जास्त जोखमीचा संकेत हा पुढील तपासणीचे कारण आहे, निदान नाही.",
        "expect_inconclusive": "पुढे काय होईल: निकाल सीमारेषेवर आहे, त्यामुळे डॉक्टर काही काळानंतर तपासण्या पुन्हा करायला सांगू शकतात आणि तुमची लक्षणे व इतिहास यांच्यासह पाहतील.",
        "expect_low": "पुढे काय होईल: फक्त या अंदाजावरून तातडीच्या पाठपुराव्याची गरज सुचवलेली नाही. नियमित तपासणी करत रहा आणि सतत पोटदुखी किंवा पाठदुखी, कारणाशिवाय वजन घटणे, किंवा त्वचा/डोळे पिवळे पडणे अशी लक्षणे दिसल्यास लगेच डॉक्टरांना भेटा.",
        "factors": "या निकालावर कशाचा प्रभाव पडला",
        "raised": "{f}: या मूल्यामुळे अंदाजित जोखीम वाढत आहे.",
        "lowered": "{f}: या मूल्यामुळे अंदाजित जोखीम कमी होत आहे.",
        "warn_range": "{f} प्रशिक्षण डेटाच्या मर्यादेबाहेर आहे; निकालाकडे अतिरिक्त सावधगिरीने पहा.",
        "report": "अहवाल डाउनलोड करा", "report_title": "जोखीम तपासणी अहवाल",
        "about": "या मॉडेलबद्दल",
        "about_text": "Random Forest मॉडेल, 590 नमुन्यांवर (मूत्र बायोमार्कर, Debernardi et al. 2020) प्रशिक्षित; "
                      "संभाव्यता कॅलिब्रेट केल्या आहेत आणि मर्यादा उच्च संवेदनशीलतेसाठी निवडली आहे. बाह्य पडताळणी झालेली नाही.",
        "age_name": "वय", "sex_name": "लिंग", "creatinine_name": "क्रिएटिनिन",
    },
}


def tr(lang, key, **kw):
    s = T.get(lang, T["en"]).get(key) or T["en"][key]
    return s.format(**kw) if kw else s


def factor_label(lang, feat):
    """Display name for a model feature (biomarker acronyms stay in Latin script)."""
    special = {"age": "age_name", "sex": "sex_name", "creatinine": "creatinine_name"}
    if feat in special:
        return tr(lang, special[feat])
    return {"plasma_CA19_9": "CA19-9"}.get(feat, feat)
