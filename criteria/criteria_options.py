CRITERIA_OPTIONS = {
    'relationRequired': [
        {
            "value": "OR",
            "label": "ข้อใดข้อหนึ่ง"
        },
        {
            "value": "AND",
            "label": "ทุกข้อ"
        },
        {
            "value": "SUM",
            "label": "ใช้คะแนนรวม"
        },
        {
            "value": "MAX",
            "label": "ใช้คะแนนมากที่สุด"
        },
    ],
    'relationScoring': [
        {
            "value": "MAX",
            "label": "ใช้คะแนนมากที่สุด"
        },
        {
            "value": "SUM",
            "label": "ใช้คะแนนรวมตามสัดส่วน"
        },
    ],
    'general_required_tags': [
        {
            "score_type": "GPAX_5_SEMESTER",
            "description": "ผลการเรียนเฉลี่ยสะสม (GPAX) 5 ภาคเรียน", "unit": ""
        },
        {
            "score_type": "GPAX",
            "description": "ผลการเรียนเฉลี่ยสะสม (GPAX)", "unit": ""
        },
        #{
        #  "score_type": "STUDY_AT_12",
        #  "description": "เป็นผู้ที่กำลังศึกษาอยู่ชั้นมัธยมศึกษาปีที่ 6 หรือเทียบเท่า", "unit": ""
        #},
        #{
        #  "score_type": "GRAD_OR_STUDY_AT_12",
        #  "description": "กำลังศึกษาหรือสำเร็จศึกษาชั้นมัธยมศึกษาปีที่ 6 หรือเทียบเท่า", "unit": ""
        #},
        {
            "score_type": "UNIT_MATH",
            "description": "หน่วยกิตกลุ่มสาระการเรียนรู้คณิตศาสตร์", "unit": ""
        },
        {
            "score_type": "UNIT_FOREIGN",
            "description": "หน่วยกิตกลุ่มสาระการเรียนรู้ภาษาต่างประเทศ", "unit": ""
        },
        {
            "score_type": "UNIT_SCI",
            "description": "หน่วยกิตกลุ่มสาระการเรียนรู้วิทยาศาสตร์", "unit": ""
        },
        {
            "score_type": "GPAX_MATH",
            "description": "คะแนนเฉลี่ยรายวิชากลุ่มสาระการเรียนรู้คณิตศาสตร์", "unit": ""
        },
        {
            "score_type": "GPAX_FOREIGN",
            "description": "คะแนนเฉลี่ยรายวิชากลุ่มสาระการเรียนรู้ภาษาต่างประเทศ", "unit": ""
        },
        {
            "score_type": "GPAX_SCI",
            "description": "คะแนนเฉลี่ยรายวิชากลุ่มสาระการเรียนรู้วิทยาศาสตร์", "unit": ""
        },
    ],
    'general_scoring_tags': [
        {
            "score_type": "GPAX_5_SEMESTER",
            "description": "ผลการเรียนเฉลี่ยสะสม (GPAX) 5 ภาคเรียน", "unit": ""
        },
        {
            "score_type": "GPAX",
            "description": "ผลการเรียนเฉลี่ยสะสม (GPAX)", "unit": ""
        },
        {
            "score_type": "INTERVIEW",
            "description": "การสอบสัมภาษณ์", "unit": ""
        },
        {
            "score_type": "INTERVIEW_ENGLISH",
            "description": "การสอบสัมภาษณ์เป็นภาษาอังกฤษ", "unit": ""
        },
    ],
    'test_tags': [
        { "score_type": "TGAT", "description": "TGAT ความถนัดทั่วไป", "unit": "คะแนน" },
        { "score_type": "TGAT1", "description": "TGAT1 การสื่อสารภาษาอังกฤษ", "unit": "คะแนน" },
        { "score_type": "TGAT2", "description": "TGAT2 การคิดอย่างมีเหตุผล", "unit": "คะแนน" },
        { "score_type": "TGAT3", "description": "TGAT3 สมรรถนะการทำงาน", "unit": "คะแนน" },
        { "score_type": "TPAT1", "description": "TPAT1 วิชาเฉพาะ กสพท", "unit": "คะแนน" },
        { "score_type": "TPAT2", "description": "TPAT2 ความถนัดศิลปกรรมศาสตร์", "unit": "คะแนน" },
        { "score_type": "TPAT21", "description": "TPAT21 ทัศนศิลป์", "unit": "คะแนน" },
        { "score_type": "TPAT22", "description": "TPAT22 ดนตรี", "unit": "คะแนน" },
        { "score_type": "TPAT23", "description": "TPAT23 นาฏศิลป์", "unit": "คะแนน" },
        { "score_type": "TPAT3", "description": "TPAT3 ความถนัดวิทยาศาสตร์ เทคโนโลยี วิศวกรรมศาสตร์", "unit": "คะแนน" },
        { "score_type": "TPAT4", "description": "TPAT4 ความถนัดสถาปัตยกรรมศาสตร์", "unit": "คะแนน" },
        { "score_type": "TPAT5", "description": "TPAT5 ความถนัดครุศาสตร์-ศึกษาศาสตร์", "unit": "คะแนน" },
        { "score_type": "A61Math1", "description": "A-Level Math1 คณิตศาสตร์ประยุกต์ 1", "unit": "คะแนน" },
        { "score_type": "A62Math2", "description": "A-Level Math2 คณิตศาสตร์ประยุกต์ 2", "unit": "คะแนน" },
        { "score_type": "A63Sci", "description": "A-Level Sci วิทยาศาสตร์ประยุกต์", "unit": "คะแนน" },
        { "score_type": "A64Phy", "description": "A-Level Phy ฟิสิกส์", "unit": "คะแนน" },
        { "score_type": "A65Chem", "description": "A-Level Chem เคมี", "unit": "คะแนน" },
        { "score_type": "A66Bio", "description": "A-Level Bio ชีววิทยา", "unit": "คะแนน" },
        { "score_type": "A70Soc", "description": "A-Level Soc สังคมศาสตร์", "unit": "คะแนน" },
        { "score_type": "A81Thai", "description": "A-Level Thai ภาษาไทย", "unit": "คะแนน" },
        { "score_type": "A82Eng", "description": "A-Level Eng ภาษาอังกฤษ", "unit": "คะแนน" },
        { "score_type": "A83Fre", "description": "A-Level Fre ภาษาฝรั่งเศส", "unit": "คะแนน" },
        { "score_type": "A84Ger", "description": "A-Level Ger ภาษาเยอรมัน", "unit": "คะแนน" },
        { "score_type": "A85Jap", "description": "A-Level Jap ภาษาญี่ปุ่น", "unit": "คะแนน" },
        { "score_type": "A86Kor", "description": "A-Level Kor ภาษาเกาหลี", "unit": "คะแนน" },
        { "score_type": "A87Chi", "description": "A-Level Chi ภาษาจีน", "unit": "คะแนน" },
        { "score_type": "A88Bal", "description": "A-Level Bal ภาษาบาลี", "unit": "คะแนน" },
        { "score_type": "A89Spn", "description": "A-Level Spn ภาษาสเปน", "unit": "คะแนน" },
        { "score_type": "VNET", "description": "V-NET (รวมทุกทักษะ)", "unit": "คะแนน" },
        { "score_type": "TOEFL_PBT_ITP", "description": "TOEFL PBT/ITP", "unit": "คะแนน" },
        { "score_type": "TOEFL_CBT", "description": "TOEFL CBT", "unit": "คะแนน" },
        { "score_type": "TOEFL_IBT", "description": "TOEFL IBT", "unit": "คะแนน" },
        { "score_type": "IELTS", "description": "IELTS", "unit": "คะแนน" },
        { "score_type": "TOEIC", "description": "TOEIC", "unit": "คะแนน" },
        { "score_type": "OOPT", "description": "OOPT", "unit": "คะแนน" },
        { "score_type": "KU_EPT", "description": "KU-EPT", "unit": "คะแนน" },
        { "score_type": "CU_TEP", "description": "CU-TEP", "unit": "คะแนน" },
        { "score_type": "TU_GET", "description": "TU-GET", "unit": "คะแนน" },
        { "score_type": "KKU_KEPT", "description": "KKU-KEPT", "unit": "คะแนน" },
        { "score_type": "PSU_TEP", "description": "PSU-TEP", "unit": "คะแนน" },
        { "score_type": "CMU_ETEGS", "description": "CMU-eTEGS", "unit": "คะแนน" },
        { "score_type": "SWU_SET", "description": "SWU-SET", "unit": "คะแนน" },
        { "score_type": "DET", "description": "Duolingo English Test", "unit": "คะแนน" },
        { "score_type": "MU_ELT", "description": "MU-ELT", "unit": "คะแนน" },
    ]
}

REQUIRED_SCORE_TYPE_TAGS = CRITERIA_OPTIONS['general_required_tags'] + CRITERIA_OPTIONS['test_tags']
SCORING_SCORE_TYPE_TAGS = CRITERIA_OPTIONS['general_scoring_tags'] + CRITERIA_OPTIONS['test_tags']
